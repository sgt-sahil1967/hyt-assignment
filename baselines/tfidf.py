"""Baseline: TF-IDF cosine (vectoriser fit on all JDs + resumes in the corpus)."""
from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .common import resume_body, tokens


class TfidfScorer:
    def __init__(self, corpus: list[str]):
        self.v = TfidfVectorizer(tokenizer=tokens, lowercase=False, token_pattern=None, sublinear_tf=True)
        self.v.fit(corpus)

    def score(self, jd_text: str, resume_text: str) -> float:
        m = self.v.transform([jd_text, resume_body(resume_text)])
        return float(cosine_similarity(m[0], m[1])[0, 0])
