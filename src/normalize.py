"""Skill normalisation: alias map -> parent/child taxonomy -> embedding fallback (plan §5.4)."""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

import yaml

from .config import cfg

FALLBACK_LOG: list[dict] = []  # every embedding-fallback match, for review


@lru_cache(maxsize=1)
def _data():
    from .config import ROOT

    d = yaml.safe_load((ROOT / cfg().get("normalize", {}).get("skills_file", "src/skills.yaml")).read_text())
    aliases = {str(k).lower(): str(v).lower() for k, v in d["aliases"].items()}
    parents = {str(k).lower(): [str(p).lower() for p in v] for k, v in d["parents"].items()}
    vocab = set(aliases.values()) | set(parents) | {p for ps in parents.values() for p in ps}
    return aliases, parents, sorted(vocab)


def _clean(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s*\((?:e\.g\.|eg|i\.e\.)[^)]*\)", "", s)  # drop "(e.g. ...)"
    s = re.sub(r"\b(experience|knowledge|proficiency|familiarity|expertise|skills?|frameworks?|development|platforms?|tools?|libraries|library)\b( (with|in|of))?", "", s)
    s = re.sub(r"\s+", " ", s).strip(" .,:;-")
    return s


def canon(name: str, allow_embedding: bool = True) -> str:
    """Map a surface skill name to a canonical vocabulary entry (or a cleaned lowercase form)."""
    aliases, parents, vocab = _data()
    raw = name.lower().strip()
    for cand in (raw, _clean(name)):
        if cand in aliases:
            return aliases[cand]
        if cand in parents or cand in vocab:
            return cand
    c = _clean(name)
    if not c:
        return raw
    if allow_embedding:
        hit = _embedding_fallback(c)
        if hit:
            return hit
    return c


@lru_cache(maxsize=4096)
def _embedding_fallback(term: str) -> str | None:
    from .embed import embed

    _, _, vocab = _data()
    vecs = embed([term] + vocab)
    sims = vecs[1:] @ vecs[0]
    i = int(sims.argmax())
    thr = cfg()["embedding"]["fallback_threshold"]
    if sims[i] >= thr:
        FALLBACK_LOG.append({"term": term, "mapped_to": vocab[i], "similarity": round(float(sims[i]), 3)})
        return vocab[i]
    return None


@lru_cache(maxsize=4096)
def ancestors(skill: str) -> frozenset[str]:
    _, parents, _ = _data()
    out, stack = set(), [skill]
    while stack:
        for p in parents.get(stack.pop(), []):
            if p not in out:
                out.add(p)
                stack.append(p)
    return frozenset(out)


def satisfies(candidate: str, requirement: str) -> str | None:
    """Return basis if the candidate's canonical skill satisfies the canonical requirement.

    'exact' | 'taxonomy' (child satisfies parent) | None. A parent never satisfies a child.
    """
    if candidate == requirement:
        return "exact"
    if requirement in ancestors(candidate):
        return "taxonomy"
    return None


def is_known(name: str) -> bool:
    """True if the term maps onto the curated skill vocabulary (so taxonomy matching applies)."""
    _, _, vocab = _data()
    if canon(name, allow_embedding=False) in vocab:
        return True
    return "/" in name and cfg()["score"].get("split_slash_requirements", False) and \
        any(canon(p, allow_embedding=False) in vocab for p in name.split("/") if p.strip())
