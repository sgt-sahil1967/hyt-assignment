"""Groundedness: every quoted span in an explanation must exist in the visible, sanitised resume text."""
from __future__ import annotations

import re

from rapidfuzz import fuzz

QUOTE = re.compile(r"[\"“]([^\"”]{2,200})[\"”]")
THRESHOLD = 90


def is_grounded(span: str, resume_text: str) -> bool:
    s = span.strip().strip(".,;:!?").strip().lower()
    t = resume_text.lower()
    if not s:
        return True
    if s in t:
        return True
    return fuzz.partial_ratio(s, t) >= THRESHOLD


def check(explanation: str, resume_text: str) -> dict:
    """Return cleaned explanation + counts. Ungrounded quotes are removed (and counted as hallucinations)."""
    quotes = QUOTE.findall(explanation)
    bad = [q for q in quotes if not is_grounded(q, resume_text)]
    cleaned = explanation
    for q in bad:
        cleaned = re.sub(r"[\"“]" + re.escape(q) + r"[\"”]", "[unverified quote removed]", cleaned)
    return {"explanation": cleaned, "n_quotes": len(quotes), "n_ungrounded": len(bad), "ungrounded": bad}


def check_evidence(evidence_quotes: list[str], resume_text: str) -> dict:
    bad = [q for q in evidence_quotes if q and not is_grounded(q, resume_text)]
    return {"n": len([q for q in evidence_quotes if q]), "n_ungrounded": len(bad), "ungrounded": bad}
