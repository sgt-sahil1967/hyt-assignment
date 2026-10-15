from datetime import date

import pytest

from src.experience import compute_yoe, parse_date
from src.normalize import canon, satisfies

REF = date(2024, 1, 15)


# ---------------- normalisation
@pytest.mark.parametrize("raw,want", [
    ("K8s", "kubernetes"), ("ReactJS", "react"), ("Postgres", "postgresql"), ("REST APIs", "rest api"),
    ("Spring Framework", "spring"), ("Node.js", "node.js"), ("NodeJS", "node.js"), ("C/C++", "c++"),
    ("Containerisation and orchestration", "containerisation"), ("Machine Learning", "machine learning"),
])
def test_alias(raw, want):
    assert canon(raw, allow_embedding=False) == want


def test_versioned_skills_stay_separate():
    assert canon("AngularJS", allow_embedding=False) == "angularjs"
    assert canon("Angular", allow_embedding=False) == "angular"
    assert satisfies("angularjs", "angular") is None and satisfies("angular", "angularjs") is None


def test_child_satisfies_parent_not_reverse():
    assert satisfies("postgresql", "sql") == "taxonomy"
    assert satisfies("sql", "postgresql") is None
    assert satisfies("django", "python") == "taxonomy"
    assert satisfies("spring boot", "java") == "taxonomy"
    assert satisfies("java", "spring boot") is None
    assert satisfies("ec2", "aws") == "taxonomy"
    assert satisfies("docker", "containerisation") == "taxonomy"
    assert satisfies("python", "programming language") == "taxonomy"


def test_javascript_does_not_satisfy_java():
    assert satisfies("javascript", "java") is None


# ---------------- dates
@pytest.mark.parametrize("s,want,exact", [
    ("Present", REF, True), ("current", REF, True), ("2019", date(2019, 7, 1), False),
    ("Mar 2019", date(2019, 3, 1), True), ("March 2019", date(2019, 3, 1), True), ("03/2019", date(2019, 3, 1), True),
    ("2019-03", date(2019, 3, 1), True), ("Summer 2020", date(2020, 7, 1), False), ("Jan '21", date(2021, 1, 1), True),
    ("Q3 2019", date(2019, 8, 1), False),
])
def test_parse_date(s, want, exact):
    assert parse_date(s, REF) == (want, exact)


def test_unparseable_date():
    assert parse_date("sometime", REF) == (None, False)


def test_overlapping_roles_merged():
    r = compute_yoe([{"start": "2018", "end": "2021"}, {"start": "2020", "end": "Present"}], REF)
    assert r["yoe"] == pytest.approx((REF - date(2018, 7, 1)).days / 365.25, abs=0.01)
    assert r["confidence"] == "high"


def test_internship_half_weight_and_not_double_counted():
    r = compute_yoe([{"start": "Jan 2020", "end": "Jan 2021", "is_internship": True}], REF)
    assert r["yoe"] == pytest.approx(0.5, abs=0.01)
    r2 = compute_yoe([{"start": "Jan 2020", "end": "Jan 2021", "is_internship": True},
                      {"start": "Jan 2020", "end": "Jan 2021"}], REF)
    assert r2["yoe"] == pytest.approx(1.0, abs=0.01)


def test_future_and_unparseable_dates_low_confidence():
    r = compute_yoe([{"start": "2023", "end": "2030"}], REF)
    assert r["confidence"] == "low" and r["yoe"] == pytest.approx(0.54, abs=0.02)
    r = compute_yoe([{"start": "2027", "end": "Present"}], REF)
    assert r["confidence"] == "low" and r["yoe"] == 0
    r = compute_yoe([{"start": "the past", "end": "Present"}], REF)
    assert r["confidence"] == "low" and r["yoe"] == 0


def test_reversed_dates_swapped_low_confidence():
    r = compute_yoe([{"start": "2021", "end": "2019"}], REF)
    assert r["confidence"] == "low" and r["yoe"] == pytest.approx(2.0, abs=0.01)


def test_template_corpus_values():
    for y, want in [(2018, 5.5), (2023, 0.5)]:
        assert compute_yoe([{"start": str(y), "end": "Present"}], REF)["yoe"] == pytest.approx(want, abs=0.05)


# ---------------- scorer evidence helpers
def test_mentions_handles_plurals_and_symbols():
    from src.score import _mentions
    assert _mentions("- Built REST APIs", "REST API", "rest api")
    assert _mentions("wrote C++ services", "C++", "c++")
    assert not _mentions("JavaScript apps", "Java", "java")
    assert not _mentions("used Golang", "Go", "go")


def test_career_break_not_counted_as_experience():
    r = compute_yoe([{"start": "2016", "end": "2017", "title": "Career break – full-time family caregiving"},
                     {"start": "2018", "end": "Present", "title": "Backend Developer"}], REF)
    assert r["yoe"] == pytest.approx(5.54, abs=0.02) and r["confidence"] == "high"


def test_framework_categories():
    req = canon("web development frameworks", allow_embedding=False)
    assert req == "web framework"
    for fw in ["Express.js", "FastAPI", "Django", "Flask", "Spring Boot", "NestJS"]:
        assert satisfies(canon(fw, allow_embedding=False), req) == "taxonomy", fw
    assert satisfies("python", req) is None and satisfies("node.js", req) is None  # language != framework
    assert satisfies(canon("React.js", allow_embedding=False), canon("frontend frameworks", allow_embedding=False))
    assert satisfies(canon("Tailwind CSS", allow_embedding=False), "css")


def test_is_known():
    from src.normalize import is_known
    assert is_known("web frameworks") and is_known("K8s")
    assert not is_known("quantum basket weaving")
