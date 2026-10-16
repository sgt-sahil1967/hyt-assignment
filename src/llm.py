"""Provider-agnostic LLM client with a content-addressed disk cache.

Cache key = sha256(model, prompt_version, schema name, prompt, salt). Cached files hold the raw response text
(only ever produced from masked inputs), so `make reproduce` runs without an API key.
"""
from __future__ import annotations

import json
import threading
import time
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel, ValidationError

from .config import cfg, path, sha


class CacheMiss(RuntimeError):
    pass


class LLMError(RuntimeError):
    pass


# Calls made while screening a real uploaded resume are cached in cache/private/ (gitignored), never in the
# committed cache/llm/. Set via the `private_cache()` context manager (agent.screen does this for uploads).
_PRIVATE: ContextVar[bool] = ContextVar("hyt_private_cache", default=False)
# Read the cache but never call the API, for this call only (the global `offline` flag is shared across requests).
_CACHE_ONLY: ContextVar[bool] = ContextVar("hyt_cache_only", default=False)


@contextmanager
def private_cache(on: bool = True):
    token = _PRIVATE.set(on)
    try:
        yield
    finally:
        _PRIVATE.reset(token)


@contextmanager
def cache_only(on: bool = True):
    token = _CACHE_ONLY.set(on)
    try:
        yield
    finally:
        _CACHE_ONLY.reset(token)


def _cache_dir(private: bool | None = None) -> Path:
    private = _PRIVATE.get() if private is None else private
    p = path("cache") / ("private" if private else "llm")
    p.mkdir(parents=True, exist_ok=True)
    return p


STATS = {"calls": 0, "cache_hits": 0, "errors": 0, "error_samples": [], "key_failovers": 0}

_pool_lock = threading.Lock()
_clients: dict[str, object] = {}
_exhausted: set[tuple[str, str]] = set()  # (key, model) whose daily quota is spent / unusable

PARSE_SCHEMAS = {"ResumeExtraction"}  # calls that may use the dedicated GEMINI_PARSE_API_KEY


def _keys(purpose: str | None = None) -> list[str]:
    """Key pool in priority order (values are never logged or printed).

    General pool: GEMINI_API_KEY, GEMINI_API_KEY_2, ... For purpose="parse" (resume extraction) the dedicated
    GEMINI_PARSE_API_KEY goes first, then the general pool as fallback. Nothing else ever uses the parse key.
    """
    import os
    import re

    from .config import _load_env

    cfg()
    _load_env()  # re-read .env so a key added while the app runs is picked up without a restart
    named = sorted((k for k in os.environ if re.fullmatch(r"GEMINI_API_KEY(_\d+)?", k)),
                   key=lambda k: int(k.rsplit("_", 1)[1]) if k[-1].isdigit() else 1)
    pool = [os.environ[k].strip() for k in named if os.environ[k].strip()]
    if purpose == "parse" and os.environ.get("GEMINI_PARSE_API_KEY", "").strip():
        pk = os.environ["GEMINI_PARSE_API_KEY"].strip()
        pool = [pk] + [k for k in pool if k != pk]
    return pool


def _client_for(key: str):
    with _pool_lock:  # one shared client per key: racing threads used to create (and GC-close) extra clients
        if key not in _clients:
            from google import genai

            _clients[key] = genai.Client(api_key=key)
        return _clients[key]


def _pick_key(model: str, keys: list[str]) -> str:
    if not keys:
        raise LLMError("no GEMINI_API_KEY set (or run offline from cache with HYT_OFFLINE=1)")
    with _pool_lock:
        for k in keys:
            if (k, model) not in _exhausted:
                return k
    raise LLMError(f"daily quota exhausted on all {len(keys)} key(s) for {model}")


def _call(prompt: str, model: str, schema: Optional[Type[BaseModel]], temperature: float) -> str:
    from google.genai import types

    conf = {"temperature": temperature}
    if schema is not None:
        conf.update(response_mime_type="application/json", response_schema=schema)
    keys = _keys("parse" if schema is not None and schema.__name__ in PARSE_SCHEMAS else None)
    last = None
    for attempt in range(cfg()["llm"]["max_retries_api"] + len(keys)):
        k = _pick_key(model, keys)
        try:
            r = _client_for(k).models.generate_content(model=model, contents=prompt, config=types.GenerateContentConfig(**conf))
            if r.text is None:
                raise LLMError(f"empty response (finish={r.candidates[0].finish_reason if r.candidates else '?'})")
            return r.text
        except Exception as e:  # rate limits / 5xx / empty
            last = e
            STATS["errors"] += 1
            if len(STATS["error_samples"]) < 20:
                STATS["error_samples"].append(type(e).__name__ + ": " + str(e)[:120].replace(k, "***"))
            unusable = "PERMISSION_DENIED" in str(e) or "NOT_FOUND" in str(e)  # key's project can't use this model
            if "PerDay" in str(e) or unusable:  # this key is spent/unusable for this model: fail over
                with _pool_lock:
                    _exhausted.add((k, model))
                STATS["key_failovers"] += 1
                continue
            rate = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e)
            time.sleep(min(60, (8 if rate else 2) * 2 ** min(attempt, 4)))
    raise LLMError(f"API failed after retries: {type(last).__name__}")


def generate(prompt: str, *, schema: Optional[Type[BaseModel]] = None, model: Optional[str] = None,
             salt: str = "", temperature: Optional[float] = None) -> str:
    c = cfg()["llm"]
    model = model or c["model"]
    temperature = c["temperature"] if temperature is None else temperature
    key = sha(model, c["prompt_version"], schema.__name__ if schema else "text", prompt, salt, str(temperature))
    f = _cache_dir() / f"{key}.json"
    public = _cache_dir(private=False) / f"{key}.json"
    for hit in (f, public):  # a private run may reuse a public entry; a public run never reads private ones
        if hit.exists():
            STATS["cache_hits"] += 1
            return json.loads(hit.read_text())["text"]
    if c["offline"] or _CACHE_ONLY.get():
        raise CacheMiss(f"offline and no cache entry for {key[:12]}")
    STATS["calls"] += 1
    text = _call(prompt, model, schema, temperature)
    f.write_text(json.dumps({"model": model, "prompt_version": c["prompt_version"], "salt": salt, "text": text}))
    return text


def generate_model(prompt: str, schema: Type[BaseModel], **kw) -> tuple[Optional[BaseModel], dict]:
    """Structured call: validate; on failure retry once with the validation error appended."""
    meta = {"attempts": 0, "error": None}
    p = prompt
    for attempt in range(2):
        meta["attempts"] += 1
        try:
            text = generate(p, schema=schema, **kw)
            return schema.model_validate_json(text), meta
        except (ValidationError, json.JSONDecodeError) as e:
            meta["error"] = f"schema: {str(e)[:300]}"
            p = prompt + f"\n\nYour previous output failed validation:\n{str(e)[:800]}\nReturn valid JSON for the schema only."
        except (LLMError, CacheMiss) as e:
            meta["error"] = f"{type(e).__name__}: {str(e)[:300]}"
            if isinstance(e, CacheMiss):
                break
    return None, meta
