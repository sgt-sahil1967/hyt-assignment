"""Scorer + decision policy unit tests (no LLM, no embeddings: role relevance is disabled by giving no role text)."""
from src.decide import decide, doc_flags, keyword_stuffing
from src.schemas import Evidence, ScoreResult
from src.score import candidate_skills, rank, score_pair

JD = {"title": "Python Engineer", "seniority": "mid", "summary": "", "min_years": None,
      "equivalent_experience_allowed": False,
      "must_have": [{"name": "python", "type": "skill", "alternatives": []},
                    {"name": "containerisation", "type": "skill", "alternatives": ["docker", "kubernetes"]}],
      "nice_to_have": [{"name": "aws", "type": "skill", "alternatives": []}]}


def resume(skills, start="2018", bullets="", projects=None, title=""):
    return {"skills": [{"name": n, "proficiency": p, "evidence": n} for n, p in skills],
            "roles": [{"title": title, "company_masked": "X", "start": start, "end": "Present", "is_internship": False,
                       "description_evidence": bullets}],
            "projects": projects or [], "education": [{"degree_level": "bachelor", "field": "Computer Science", "year": 2017}]}


def test_used_verified_by_code():
    s = candidate_skills(resume([("Python", "used"), ("Docker", "listed")], bullets="- Shipped Docker images"))
    assert s["python"]["basis"] == "listed"  # LLM claimed used, no bullet shows it -> downgraded
    assert s["docker"]["basis"] == "used"    # bullet shows it -> upgraded


def test_alternatives_and_taxonomy():
    sr = score_pair("J", "R", JD, resume([("Django", "listed"), ("Kubernetes", "listed")]))
    ev = {e.requirement: e for e in sr.evidence}
    assert ev["python"].strength == 0.5 and "taxonomy" in ev["python"].basis
    assert ev["containerisation"].strength == 0.5
    assert not sr.capped


def test_missing_must_have_multiplicative_cap_preserves_order():
    strong = score_pair("J", "A", JD, resume([("Python", "listed"), ("AWS", "listed")], start="2018"))
    weak = score_pair("J", "B", JD, resume([("Python", "listed")], start="2022"))
    assert strong.capped and weak.capped
    assert strong.score <= 0.6 and weak.score <= 0.6
    assert strong.score > weak.score  # a hard min(fit, 0.6) would not guarantee this


def test_no_nice_to_haves_renormalises():
    jd = {**JD, "nice_to_have": []}
    sr = score_pair("J", "R", jd, resume([("Python", "used"), ("Docker", "used")], bullets="- Python and Docker"))
    c = sr.components
    assert c["nice_to_have"] is None
    w = {"must_have": 0.50, "experience": 0.20, "role_relevance": 0.15}  # nice (0.15) dropped, rest renormalised
    want = sum(w[k] * c[k] for k in w) / sum(w.values())
    assert abs(sr.score - round(want, 4)) < 1e-4


def test_ties_broken_deterministically():
    a = ScoreResult(job_id="J", resume_id="R2", score=0.5, components={"must_have": 0.5}, evidence=[], gaps=[], yoe=1,
                    yoe_confidence="high", capped=False)
    b = a.model_copy(update={"resume_id": "R1"})
    c = a.model_copy(update={"resume_id": "R3", "components": {"must_have": 0.9}})
    assert [r.resume_id for r in rank([a, b, c])] == ["R3", "R1", "R2"]


def _sr(score, strengths, yoe=3.0, rel=None):
    ev = [Evidence(requirement=f"r{i}", level="must", matched_skill=None, strength=s, basis="x") for i, s in enumerate(strengths)]
    return ScoreResult(job_id="J", resume_id="R", score=score, components={"must_have": 0.5, "role_relevance": rel},
                       evidence=ev, gaps=[], yoe=yoe, yoe_confidence="high", capped=False)


P = {"t_high": 0.5, "t_low": 0.3, "delta": 0.05}


def test_policy_advance_and_reasons():
    assert decide(_sr(0.7, [0.5, 1.0]), JD, [], P).decision == "advance"
    assert "BORDERLINE_SCORE" in decide(_sr(0.47, [0.5]), JD, [], P).reasons
    assert "MISSING_MUST_HAVE" in decide(_sr(0.7, [0.0, 1.0]), JD, [], P).reasons
    assert "AMBIGUOUS_EVIDENCE" in decide(_sr(0.7, [0.25]), JD, [], P).reasons
    d = decide(_sr(0.1, [0.0]), JD, [], P)
    assert "LOW_FIT" in d.reasons and d.queue == "low_priority"


def test_location_is_info_only_but_manipulation_blocks():
    assert decide(_sr(0.7, [1.0]), JD, ["LOCATION_MISMATCH"], P).decision == "advance"
    d = decide(_sr(0.95, [1.0]), JD, ["SUSPECTED_MANIPULATION"], P)
    assert d.decision == "escalate" and d.queue == "review"


def test_overqualified_for_junior():
    jd = {**JD, "seniority": "junior"}
    assert "OVERQUALIFIED" in decide(_sr(0.7, [1.0], yoe=5.5), jd, [], {**P, "overqualified_years_over": 3}).reasons
    assert "OVERQUALIFIED" not in decide(_sr(0.7, [1.0], yoe=3.5), jd, [], {**P, "overqualified_years_over": 3}).reasons


def test_explicit_min_years_is_a_must_have():
    jd = {**JD, "min_years": 7}
    assert "MISSING_MUST_HAVE" in decide(_sr(0.7, [1.0], yoe=5.5), jd, [], P).reasons


def test_doc_flags():
    meta = {"words": 75, "language": "en", "flags": {"injection_suspected": True}}
    assert "SUSPECTED_MANIPULATION" in doc_flags(meta, resume([("Python", "listed")]), JD)
    assert doc_flags({"words": 10, "language": "en", "flags": {}}, resume([]), JD) == ["SPARSE_RESUME"]
    assert "EXTRACTION_FAILED" in doc_flags({"flags": {}}, None, JD)
    assert "NON_ENGLISH" in doc_flags({"words": 80, "language": "de", "flags": {}}, {**resume([]), "language": "de"}, JD)


def test_keyword_stuffing_detector():
    assert keyword_stuffing([{"name": f"s{i}", "proficiency": "listed"} for i in range(30)])
    assert not keyword_stuffing([{"name": f"s{i}", "proficiency": "listed"} for i in range(8)])


def test_career_switch_is_informational_by_default_and_blocking_in_v1():
    sr = _sr(0.7, [1.0], rel=0.1)
    d = decide(sr, JD, [], P)
    assert "CAREER_SWITCH" in d.reasons and d.decision == "advance"
    d1 = decide(sr, JD, [], {**P, "career_switch_blocking": True})
    assert d1.decision == "escalate"


def test_failed_explanation_is_none_not_error_text(monkeypatch):
    import agent
    import src.explain as ex
    monkeypatch.setattr(ex, "generate", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("quota")))
    x = {"skills": [{"name": "Python", "proficiency": "listed", "evidence": "Python"}], "roles": [], "projects": [],
         "education": []}
    out = agent.screen("Python", {"title": "t", "must_have": [{"name": "python"}]}, extraction=x, explain=True)
    assert out["explanation"] is None and "quota" in out["explanation_error"]


def test_under_seniority_escalates_lead_role_without_stated_minimum():
    """v1.3: a 2.6-year candidate meeting every must-have was auto-shortlisted for a Lead role (implied 6y)."""
    on = {**P, "under_seniority_blocking": True, "under_seniority_fraction": 0.5}
    lead = {**JD, "seniority": "lead", "min_years": None}
    d = decide(_sr(0.8, [1.0], yoe=2.6), lead, [], on)
    assert "UNDER_SENIORITY" in d.reasons and d.decision == "escalate"
    assert "UNDER_SENIORITY" not in decide(_sr(0.8, [1.0], yoe=3.5), lead, [], on).reasons  # >= half of 6y
    assert "UNDER_SENIORITY" not in decide(_sr(0.8, [1.0], yoe=1.0), {**JD, "seniority": "mid"}, [], on).reasons
    assert "UNDER_SENIORITY" not in decide(_sr(0.8, [1.0], yoe=2.6), {**lead, "min_years": 2}, [], on).reasons  # stated
    assert decide(_sr(0.8, [1.0], yoe=2.6), lead, [], {**P, "under_seniority_blocking": False}).decision == "advance"
