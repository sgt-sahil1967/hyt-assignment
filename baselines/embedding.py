"""Baseline: sentence-embedding cosine of the whole JD vs whole resume (same local model as the pipeline)."""
from src.embed import embed

from .common import resume_body


def score(jd_text: str, resume_text: str) -> float:
    v = embed([jd_text[:4000], resume_body(resume_text)])
    return float(v[0] @ v[1])
