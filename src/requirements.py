"""Deterministic post-processing of LLM-extracted JD requirements (v1.2).

The LLM sometimes turns an *example list* into separate must-haves: "Experience with MySQL, Redis, Nginx, Kubernetes,
Docker, OpenStack, Hadoop, Spark, Flink, etc." became 9 must-haves, so no real candidate could meet them all (REPORT
§5c). Code fixes that from the JD text itself: when ≥ 3 requirements of the same level are all named in one clause
that is marked as a list of examples ("etc.", "e.g.", "such as", "or similar", "including", "for example"), they are
merged into ONE requirement whose alternatives are those items, so any one of them satisfies it.
"""
from __future__ import annotations

import re
from copy import deepcopy

POSTFIX = re.compile(r",?\s*(?:\betc\b\.?|and more\b|or similar\b|and similar\b|among others\b)", re.IGNORECASE)
PREFIX = re.compile(r"(?:such as|e\.g\.?|for example|including)[:,]?\s*", re.IGNORECASE)
MAX_ITEM_WORDS = 3
MIN_GROUP = 3


def _named(clause: str, req: dict) -> bool:
    """Requirement named in the clause: exact word match, or a near-identical token for typos ("Ngnix" ~ nginx)."""
    from rapidfuzz import fuzz

    low = clause.lower()
    tokens = re.findall(r"[a-z0-9+#.]+", low)
    for n in [req["name"], *(req.get("alternatives") or [])]:
        n = n.strip().lower()
        if len(n) < 2:
            continue
        if re.search(r"(?<![\w.+#])" + re.escape(n) + r"(?![\w+#])", low):
            return True
        if len(n) >= 5 and " " not in n and any(fuzz.ratio(n, t) >= 80 for t in tokens if abs(len(t) - len(n)) <= 1):
            return True
    return False


def example_lists(text: str) -> list[str]:
    """The comma-separated item runs next to an example marker: "MySQL, Redis, Nginx, … etc." or "such as A, B, C".

    Only short items (≤ 3 words) count, so a run stops at the first long phrase. That keeps scraped postings whose
    bullets are concatenated without punctuation from turning a whole requirements section into one "list".
    """
    runs = []
    for m in POSTFIX.finditer(text or ""):
        segs = text[max(0, m.start() - 400):m.start()].split(",")
        items = []
        for seg in reversed(segs):
            words = seg.split()
            if not words:
                continue
            if len(words) > MAX_ITEM_WORDS:
                items.append(" ".join(words[-2:]))  # "…systemsExperience in MySQL" -> keep the tail ("in MySQL")
                break
            items.append(seg.strip())
        if len(items) >= 2:
            runs.append(", ".join(reversed(items)))
    for m in PREFIX.finditer(text or ""):
        segs = re.split(r",|\band\b|\bor\b", re.split(r"[.;:]\s", text[m.end():m.end() + 400])[0])
        items = []
        for seg in segs:
            words = seg.split()
            if not words:
                continue
            if len(words) > MAX_ITEM_WORDS:
                items.append(" ".join(words[:2]))
                break
            items.append(seg.strip())
        if len(items) >= 2:
            runs.append(", ".join(items))
    return runs


def consolidate_example_lists(jd: dict, text: str) -> dict:
    """Return a copy of the extracted JD with example-list requirements merged (deterministic, no LLM)."""
    jd = deepcopy(jd)
    lists = example_lists(text)
    merged_log = []
    for level in ("must_have", "nice_to_have"):
        reqs = jd.get(level, [])
        used: set[int] = set()
        out = []
        # the list naming the most requirements wins first
        named = {c: [i for i, r in enumerate(reqs) if r.get("type") == "skill" and _named(c, r)] for c in lists}
        for run in sorted(lists, key=lambda c: -len(named[c])):
            idx = [i for i in named[run] if i not in used]
            if len(idx) >= MIN_GROUP:
                names = []
                for i in idx:
                    names += [reqs[i]["name"], *(reqs[i].get("alternatives") or [])]
                names = list(dict.fromkeys(names))
                # "experience with A, B, C, … etc." means several of them, not any one: full credit needs about a
                # third of the listed items (at most 3); fewer matches earn proportional credit (see score._match)
                need = min(3, max(1, -(-len(idx) // 3)))
                out.append({"name": f"{need}+ of: {', '.join(names[:4])}{'…' if len(names) > 4 else ''}",
                            "type": "skill", "alternatives": names, "min_matches": need})
                used.update(idx)
                merged_log.append({"level": level, "merged": [reqs[i]["name"] for i in idx]})
        jd[level] = out + [r for i, r in enumerate(reqs) if i not in used]
    if merged_log:
        jd["consolidated_example_lists"] = merged_log
    return jd


def postprocess(jd: dict, text: str) -> dict:
    """All v1.2 deterministic JD fixes, each behind its config flag (off in the frozen v1.0 profile)."""
    from .config import cfg

    if cfg()["score"].get("consolidate_example_lists", False):
        jd = consolidate_example_lists(jd, text)
    return jd
