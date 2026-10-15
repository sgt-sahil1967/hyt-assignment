"""Evidence-only explanation (plan §5.7). The LLM never sees raw resume text, only scorer output."""
from __future__ import annotations

import json

from .grounded import check
from .llm import generate
from .schemas import Decision, ScoreResult

PROMPT = """You write a short note for a recruiter explaining an automated screening result.
You are given ONLY the scorer's structured output below; do not invent facts that are not in it.

Write 3-5 plain sentences:
1) the overall fit and score; 2) the strongest evidence; 3) the key gaps; 4) why it was advanced or escalated
(translate reason codes into plain words).
Put double quotes ONLY around text copied exactly from an "evidence_quote" field. Mention requirement names without quotes.
Never claim the candidate has a skill whose strength is 0. Do not mention names, gender, age, university or location.

SCORER OUTPUT:
{payload}
"""


def payload(sr: ScoreResult, dec: Decision, job_title: str) -> dict:
    return {
        "job_title": job_title,
        "score": sr.score,
        "components": sr.components,
        "years_experience": sr.yoe,
        "decision": dec.decision,
        "reason_codes": dec.reasons,
        "evidence": [
            {"requirement": e.requirement, "level": e.level, "strength": e.strength, "basis": e.basis,
             "evidence_quote": e.quote} for e in sr.evidence],
        "gaps": sr.gaps,
        "score_capped_for_missing_must_have": sr.capped,
    }


def explain(sr: ScoreResult, dec: Decision, job_title: str, resume_text: str) -> dict:
    p = PROMPT.format(payload=json.dumps(payload(sr, dec, job_title), indent=1))
    try:
        text = generate(p).strip()
    except Exception as e:  # explanation is best-effort; the decision never depends on it
        return {"explanation": f"[explanation unavailable: {type(e).__name__}]", "n_quotes": 0, "n_ungrounded": 0,
                "ungrounded": [], "error": str(e)[:200]}
    return check(text, resume_text)
