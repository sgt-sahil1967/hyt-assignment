"""Ablation: one-prompt LLM fit score (what you get without extraction / evidence / code scoring)."""
from __future__ import annotations

from pydantic import BaseModel, Field

from src.extract import GUARD
from src.llm import generate_model


class ZeroShot(BaseModel):
    score: int = Field(ge=0, le=100)
    decision: str = Field(description="'advance' or 'escalate'")


PROMPT = """You are screening a candidate for a software engineering job. {guard}
Rate how well the resume fits the job from 0 (no fit) to 100 (perfect fit), and say whether the candidate should be
advanced to a recruiter interview ("advance") or reviewed by a human ("escalate").

<<<DOCUMENT>>>
JOB DESCRIPTION:
{jd}

RESUME:
{resume}
<<<END>>>
"""


def score(jd_text: str, resume_text: str, salt: str = "") -> tuple[float | None, str | None]:
    x, meta = generate_model(PROMPT.format(guard=GUARD, jd=jd_text[:6000], resume=resume_text), ZeroShot, salt=salt)
    if x is None:
        return None, None
    return x.score / 100, x.decision.strip().lower()
