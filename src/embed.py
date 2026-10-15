"""Local sentence embeddings (no API key) with a JSON disk cache keyed by text hash."""
from __future__ import annotations

import json
import threading

import numpy as np

from .config import cfg, path, sha

_model = None
_cache: dict | None = None
_lock = threading.Lock()
_dirty = False


def _file():
    return path("cache") / "embeddings.json"


def _load():
    global _cache
    if _cache is None:
        f = _file()
        _cache = json.loads(f.read_text()) if f.exists() else {}
    return _cache


def save():
    global _dirty
    if _dirty and _cache is not None:
        _file().write_text(json.dumps(_cache))
        _dirty = False


def embed(texts: list[str]) -> np.ndarray:
    global _model, _dirty
    cache = _load()
    name = cfg()["embedding"]["model"]
    keys = [sha(name, t) for t in texts]
    missing = [t for t, k in zip(texts, keys) if k not in cache]
    if missing:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer(name, device="cpu")
            vecs = _model.encode(list(dict.fromkeys(missing)), normalize_embeddings=True, batch_size=64)
            for t, v in zip(dict.fromkeys(missing), vecs):
                cache[sha(name, t)] = [round(float(x), 6) for x in v]
            _dirty = True
    return np.array([cache[k] for k in keys], dtype=np.float32)


def cosine(a: str, b: str) -> float:
    v = embed([a, b])
    return float(v[0] @ v[1])
