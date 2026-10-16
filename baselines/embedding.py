"""Baseline: sentence-embedding cosine of the whole JD vs whole resume (same local model as the pipeline).

`score` is the evaluated baseline. MiniLM reads at most 256 tokens, so it only sees the start of each document (often
company boilerplate in a JD, contact details in a resume). `score_chunked` is a separate, post-test variant: it
embeds overlapping word windows and averages them, so the whole document counts.
"""
import numpy as np

from src.embed import embed

from .common import resume_body

WINDOW, STRIDE = 150, 100  # words; 150 words stays under 256 tokens for ordinary English


def score(jd_text: str, resume_text: str) -> float:
    v = embed([jd_text[:4000], resume_body(resume_text)])
    return float(v[0] @ v[1])


def chunks(text: str) -> list[str]:
    w = text.split()
    if len(w) <= WINDOW:
        return [" ".join(w)] if w else [""]
    return [" ".join(w[i:i + WINDOW]) for i in range(0, max(1, len(w) - WINDOW + STRIDE), STRIDE)]


def doc_vector(text: str) -> np.ndarray:
    v = embed(chunks(text)).mean(axis=0)
    return v / (np.linalg.norm(v) or 1.0)


def score_chunked(jd_text: str, resume_text: str) -> float:
    return float(doc_vector(jd_text) @ doc_vector(resume_body(resume_text)))
