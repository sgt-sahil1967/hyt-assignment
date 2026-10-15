"""Decision policy (plan §5.6): auto-advance or escalate with reason codes. Never rejects."""
from __future__ import annotations

from .config import cfg
from .schemas import Decision, ScoreResult

SENIORITY_MAX_YEARS = {"intern": 1, "junior": 2, "mid": 6, "senior": 12, "lead": 20, "unspecified": 99}
BLOCKING_FLAGS = {"SUSPECTED_MANIPULATION", "EXTRACTION_FAILED", "LOW_CONFIDENCE_DATES", "SPARSE_RESUME", "NON_ENGLISH"}
INFO_ONLY = {"LOCATION_MISMATCH"}  # reported to the recruiter, never blocks advance on its own


def info_codes(params: dict | None = None) -> set[str]:
    """Reason codes shown to the recruiter that never block an auto-advance on their own.

    CAREER_SWITCH is informational since v1.1 (DECISIONS #15b): the corpus has no genuine career switchers to validate
    a blocking flag against. `career_switch_blocking: true` restores the frozen v1.0 policy.
    """
    d = {**cfg()["decide"], **(params or {})}
    return INFO_ONLY | (set() if d.get("career_switch_blocking", False) else {"CAREER_SWITCH"})


def doc_flags(meta: dict, res: dict | None, jd: dict, jd_meta: dict | None = None) -> list[str]:
    """Flags from ingestion + extraction, independent of the score."""
    d = cfg()
    flags = []
    f = meta.get("flags", {})
    if f.get("injection_suspected") or f.get("hidden_text_removed") or meta.get("stuffing"):
        flags.append("SUSPECTED_MANIPULATION")
    if res is None:
        flags.append("EXTRACTION_FAILED")
        return flags
    if meta.get("words", 999) < d["sanitize"]["min_words"] or not (res.get("roles") or res.get("projects")):
        flags.append("SPARSE_RESUME")
    lang = (res.get("language") or meta.get("language") or "en").lower()
    if not lang.startswith("en") or meta.get("language", "en") not in ("en", "unknown"):
        flags.append("NON_ENGLISH")
    jt = (jd_meta or {}).get("job_type", "")
    if jt.lower() == "onsite" and res.get("location"):
        city = res["location"].split(",")[0].strip().lower()
        if city and city not in (jd_meta or {}).get("location", "").lower():
            flags.append("LOCATION_MISMATCH")
    return flags


def keyword_stuffing(skills: list[dict]) -> bool:
    n = len(skills)
    used = sum(1 for s in skills if s.get("proficiency") == "used")
    return n >= cfg()["decide"]["stuffing_min_skills"] and used / max(n, 1) < 0.1


def decide(sr: ScoreResult, jd: dict, flags: list[str], params: dict | None = None) -> Decision:
    d = {**cfg()["decide"], **(params or {})}
    reasons = list(dict.fromkeys(flags))
    if sr.yoe_confidence == "low":
        reasons.append("LOW_CONFIDENCE_DATES")
    must = [e for e in sr.evidence if e.level == "must"]
    if any(e.strength == 0 for e in must) or (jd.get("min_years") and sr.yoe < float(jd["min_years"])):
        reasons.append("MISSING_MUST_HAVE")
    if any(0 < e.strength < 0.5 for e in must):
        reasons.append("AMBIGUOUS_EVIDENCE")
    band = SENIORITY_MAX_YEARS.get(jd.get("seniority", "unspecified"), 99)
    if sr.yoe > band + d["overqualified_years_over"]:
        reasons.append("OVERQUALIFIED")
    rel = sr.components.get("role_relevance")
    if rel is not None and rel < d["career_switch_relevance"] and (sr.components.get("must_have") or 0) >= 0.5:
        reasons.append("CAREER_SWITCH")

    s = sr.score
    if s < d["t_low"]:
        reasons.append("LOW_FIT")
    elif s < d["t_high"] - d["delta"]:
        reasons.append("BELOW_THRESHOLD")
    elif s < d["t_high"]:
        reasons.append("BORDERLINE_SCORE")

    reasons = list(dict.fromkeys(reasons))
    blocking = [r for r in reasons if r not in info_codes(params)]
    if not blocking:
        return Decision(decision="advance", reasons=reasons, queue="advance")
    queue = "low_priority" if "LOW_FIT" in reasons and not (set(reasons) & {"SUSPECTED_MANIPULATION", "EXTRACTION_FAILED"}) else "review"
    return Decision(decision="escalate", reasons=reasons, queue=queue)
