"""Baseline: token Jaccard between JD and resume."""
from .common import resume_body, tokens


def score(jd_text: str, resume_text: str) -> float:
    a, b = set(tokens(jd_text)), set(tokens(resume_body(resume_text)))
    return len(a & b) / len(a | b) if a | b else 0.0
