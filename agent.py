"""HYT screening agent: the public API.

    from agent import screen
    result = screen(candidate_text, criteria)        # -> dict

`criteria` is any of:
  * a JD as plain text                      -> requirements extracted by the LLM (cached)
  * {"job_id": "JD06"}                      -> one of the 10 benchmark jobs
  * a parsed-requirements dict              -> {"title", "must_have", "nice_to_have", "min_years", "seniority", ...}
    (e.g. after a recruiter edited the requirements: re-scoring then needs no LLM call)

Everything else in this file is a thin helper for UIs (Streamlit, FastAPI): sample data, benchmark data, results.
UIs never import from src/ directly.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "samples"

REASON_HELP = {
    "MISSING_MUST_HAVE": "A must-have has no evidence, or an explicit minimum-years requirement is not met.",
    "AMBIGUOUS_EVIDENCE": "A must-have is only backed by 'learning / exposure' wording.",
    "BORDERLINE_SCORE": "Score sits just below the auto-advance threshold (noise buffer).",
    "BELOW_THRESHOLD": "Score is below the auto-advance threshold.",
    "LOW_FIT": "Score is well below the threshold, so the candidate goes to the low-priority queue.",
    "SPARSE_RESUME": "Resume is too short, or lists no roles or projects.",
    "OVERQUALIFIED": "Years of experience are far above the role's seniority band.",
    "CAREER_SWITCH": "Skills match, but past role titles look unrelated to this one (information only, never blocks).",
    "LOCATION_MISMATCH": "Onsite role in a different city (information only, never blocks).",
    "EXTRACTION_FAILED": "The resume could not be parsed reliably.",
    "LOW_CONFIDENCE_DATES": "Experience was computed from unclear or future dates.",
    "SUSPECTED_MANIPULATION": "Hidden text, prompt injection or keyword stuffing detected.",
    "NON_ENGLISH": "Resume is not in English.",
}
EDU_RANK = {"none": 0, "diploma": 1, "other": 1, "bachelor": 2, "master": 3, "phd": 4}


# ------------------------------------------------------------------ criteria
def _benchmark_jobs() -> dict:
    from src.pipeline import load

    return load()[0]


@lru_cache(maxsize=64)
def _parse_jd_text(text: str) -> str:
    from src.extract import extract_jd

    x, meta = extract_jd(text)
    if x is None:
        raise RuntimeError(f"could not parse the job description: {meta.get('error')}")
    return json.dumps(x.model_dump())


def parse_criteria(criteria: Any) -> dict:
    """Normalise any accepted `criteria` form into a requirements dict (JD extraction schema + job metadata)."""
    if isinstance(criteria, str):
        jd = json.loads(_parse_jd_text(criteria.strip()))
        jd.setdefault("job_type", "")
        return jd
    if isinstance(criteria, dict) and "job_id" in criteria and "must_have" not in criteria:
        meta = _benchmark_jobs()[criteria["job_id"]]
        jd = json.loads(_parse_jd_text(meta["text"].strip()))
        jd.update(job_id=criteria["job_id"], job_type=meta["job_type"], location_meta=meta["location"])
        return jd
    if isinstance(criteria, dict):
        jd = {"title": "", "seniority": "unspecified", "summary": "", "min_years": None,
              "equivalent_experience_allowed": False, "nice_to_have": [], "job_type": "", **criteria}
        for r in jd["must_have"] + jd["nice_to_have"]:
            r.setdefault("type", "skill")
            r["alternatives"] = list(r.get("alternatives") or [])
        return jd
    raise TypeError("criteria must be JD text, {'job_id': ...} or a requirements dict")


# ------------------------------------------------------------------ the agent
def screen(candidate_text: str, criteria: Any, **kw) -> dict:
    """See _screen for parameters. Runs inside the private cache when the resume is a real upload."""
    from src.llm import private_cache

    private = kw.pop("private", None)
    if private is None:
        private = kw.get("received") is not None
    with private_cache(private):
        return _screen(candidate_text, criteria, **kw)


def _screen(candidate_text: str, criteria: Any, *, candidate_id: str = "candidate", html: bool = False,
           explain: bool = False, threshold: float | None = None, extraction: dict | None = None,
           hidden_chars_removed: int = 0, received: str | None = None) -> dict:
    """Screen one candidate against one set of criteria.

    `private`: cache LLM calls in cache/private/ (gitignored). Defaults to True for new resumes (`received` set), so
    real applicants' data never lands in the committed cache.

    `received`: ISO date the application arrived; "Present" in the resume resolves to it. Default = the pinned
    benchmark date (config as_of_date), so evaluation results stay reproducible. Pass today's date for new resumes.

    Returns a JSON-serialisable dict: score, decision ('advance' | 'escalate'), queue, reason codes (+ plain-English
    help), score components, years of experience, per-requirement evidence, gaps, a short profile, sanitiser flags and
    the masked text that the LLM saw. The agent never rejects.
    """
    from src.decide import decide, doc_flags, keyword_stuffing
    from src.pipeline import ingest_text, resume_extraction
    from src.score import score_pair

    jd = parse_criteria(criteria)
    rec = ingest_text(candidate_id, candidate_text, html=html)
    if hidden_chars_removed:  # hidden runs already stripped from a .docx by read_document()
        rec["flags"] = {**rec["flags"], "hidden_text_removed": True,
                        "chars_removed": rec["flags"]["chars_removed"] + hidden_chars_removed}
    if extraction is None and not rec["text"].strip():
        # nothing readable (e.g. a scanned PDF): don't ask the LLM to invent a resume; escalate as SPARSE_RESUME
        x, xmeta = {"skills": [], "roles": [], "projects": [], "education": [], "location": None, "language": "en"}, \
            {"attempts": 0, "error": None}
    elif extraction is None:
        x, xmeta = resume_extraction(rec)
    else:
        x, xmeta = extraction, {"attempts": 0, "error": None}
    meta = dict(rec)
    if x is not None:
        meta["stuffing"] = keyword_stuffing(x["skills"])
    jd_meta = {"job_type": jd.get("job_type", ""), "location": jd.get("location_meta") or jd.get("location") or ""}
    flags = doc_flags(meta, x, jd, jd_meta)
    xs = x or {"skills": [], "roles": [], "projects": [], "education": []}
    from datetime import date as _date

    as_of = _date.fromisoformat(received[:10]) if received else None
    sr = score_pair(jd.get("job_id", "custom"), candidate_id, jd, xs, as_of=as_of)
    params = {"t_high": threshold} if threshold is not None else None
    d = decide(sr, jd, flags, params)

    edu = max(xs.get("education") or [{"degree_level": "none"}], key=lambda e: EDU_RANK.get(e.get("degree_level", "none"), 0))
    out = {
        "candidate_id": candidate_id,
        "score": sr.score,
        "decision": d.decision,
        "queue": d.queue,
        "reasons": d.reasons,
        "reason_help": {r: REASON_HELP.get(r, "") for r in d.reasons},
        "components": sr.components,
        "capped_for_missing_must_have": sr.capped,
        "years_experience": round(sr.yoe, 1),
        "evidence": [e.model_dump() for e in sr.evidence],
        "gaps": sr.gaps,
        "profile": {
            "title": (xs.get("roles") or [{}])[0].get("title", ""),
            "skills": [s["name"] for s in xs.get("skills", [])],
            "education_level": edu.get("degree_level", "none"),
            "education_field": edu.get("field", ""),
            "location": xs.get("location"),
            "n_roles": len(xs.get("roles", [])),
            "n_projects": len(xs.get("projects", [])),
        },
        "sanitizer_flags": rec["flags"],
        "injection_matches": rec.get("injection_matches", []),
        "masked_text": rec["text"],
        "extraction_error": xmeta.get("error") if x is None else None,
        "extraction": x,
        "criteria_title": jd.get("title", ""),
    }
    if explain:
        from src.explain import explain as _explain

        e = _explain(sr, d, jd.get("title", ""), rec["text"])
        out["explanation"] = None if e.get("error") else e["explanation"]
        out["explanation_error"] = e.get("error")
        out["explanation_ungrounded_removed"] = e["n_ungrounded"]
    return out


def read_document(filename: str, data: bytes) -> dict:
    """Uploaded file -> {'text', 'html', 'hidden_chars_removed', 'warning'} ready for screen().

    Supports .pdf, .docx, .html and .txt. Hidden text (white, tiny, off-page, `vanish`) is dropped and counted so
    screen() can flag it.
    """
    name = filename.lower()
    if name.endswith(".pdf"):
        import io

        from src.sanitize import pdf_visible_text

        try:
            text, hidden, pages = pdf_visible_text(io.BytesIO(data))
        except Exception as e:  # encrypted / corrupt
            raise ValueError(f"could not read PDF ({type(e).__name__}); is it password-protected?") from e
        warning = None
        if not text.strip():
            warning = (f"No text layer found in {pages} page(s): this looks like a scanned PDF. "
                       "It will be escalated as SPARSE_RESUME; OCR is not supported.")
        return {"text": text, "html": False, "hidden_chars_removed": hidden, "warning": warning}
    if name.endswith(".docx"):
        import tempfile

        from src.sanitize import docx_visible_text

        with tempfile.NamedTemporaryFile(suffix=".docx") as tmp:
            tmp.write(data)
            tmp.flush()
            text, hidden = docx_visible_text(tmp.name)
        return {"text": text, "html": False, "hidden_chars_removed": hidden, "warning": None}
    if not name.endswith((".txt", ".html", ".htm", ".md")):
        raise ValueError(f"unsupported file type: {filename} (use .pdf, .docx, .html or .txt)")
    text = data.decode("utf-8", "ignore")
    return {"text": text, "html": name.endswith((".html", ".htm")), "hidden_chars_removed": 0, "warning": None}


# ------------------------------------------------------------------ helpers for UIs
def settings() -> dict:
    from src.config import cfg
    from src.decide import info_codes

    c = cfg()
    return {"model": c["llm"]["model"], "judge_model": c["llm"]["judge_model"], "t_high": c["decide"]["t_high"],
            "t_low": c["decide"]["t_low"], "delta": c["decide"]["delta"], "offline": bool(c["llm"]["offline"]),
            "as_of_date": c["as_of_date"], "info_codes": sorted(info_codes())}


def set_offline(offline: bool) -> None:
    from src.config import cfg

    cfg()["llm"]["offline"] = offline


def sample_data() -> dict:
    """One JD + a handful of resumes (masked, synthetic) shipped in samples/, so a reviewer gets results in one click."""
    jd = (SAMPLES / "jd.txt").read_text()
    cands = [{"id": f.stem, "text": f.read_text()} for f in sorted((SAMPLES / "resumes").glob("*.txt"))]
    return {"criteria": jd, "candidates": cands, "about": (SAMPLES / "README.md").read_text()}


def benchmark_jobs() -> list[dict]:
    return [{k: v[k] for k in ("id", "title", "location", "job_type", "level", "split", "text")}
            for v in _benchmark_jobs().values()]


def benchmark_resumes() -> dict[str, str]:
    from src.pipeline import load

    return {rid: r["text"] for rid, r in load()[1].items()}


def golden_labels() -> list[dict]:
    import pandas as pd

    return pd.read_csv(ROOT / "golden" / "labels.csv").to_dict("records")


def cached_explanation(job_id: str, resume_id: str) -> str | None:
    f = ROOT / "results" / "golden_predictions.json"
    if not f.exists():
        return None
    for r in _golden_predictions():
        if r["job_id"] == job_id and r["resume_id"] == resume_id and isinstance(r.get("explanation"), dict):
            return r["explanation"]["explanation"]
    return None


@lru_cache(maxsize=1)
def _golden_predictions() -> list:
    return json.loads((ROOT / "results" / "golden_predictions.json").read_text())


def results(name: str) -> Any:
    """Evaluation artefacts from results/ (None if that run has not happened yet)."""
    f = ROOT / "results" / name
    if not f.exists():
        return None
    if f.suffix == ".json":
        return json.loads(f.read_text())
    if f.suffix == ".csv":
        import pandas as pd

        return pd.read_csv(f)
    return f.read_text()
