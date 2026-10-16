"""Runtime settings: validation, live effect on scoring, and reset to the start-up configuration."""
import pytest

from src import settings
from src.config import cfg
from src.score import score_pair
from tests.test_score_decide import JD, resume


@pytest.fixture(autouse=True)
def _restore():
    settings.defaults()
    yield
    settings.reset()


def test_spec_matches_config():
    cur = settings.current()
    assert set(cur) == {s["key"] for s in settings.SPEC}
    assert cur["decide.t_high"] == cfg()["decide"]["t_high"]


@pytest.mark.parametrize("patch", [
    {"decide.t_high": 1.5},                      # out of range
    {"decide.t_high": "high"},                   # wrong type
    {"llm.offline": 1},                          # bool must be a bool
    {"llm.model": "gpt-x"},                      # not an option
    {"no.such.key": 1},
    {"decide.t_low": 0.48},                      # above T_high - band
    {"score.evidence_strength.listed": 1.0, "score.evidence_strength.used": 0.5},
    {f"score.weights.{k}": 0 for k in ("must_have", "nice_to_have", "experience", "role_relevance")},
])
def test_rejects_invalid(patch):
    before = settings.current()
    with pytest.raises(ValueError):
        settings.apply(patch)
    assert settings.current() == before  # nothing half-applied


def test_change_takes_effect_and_resets():
    r = resume([("Python", "listed"), ("Docker", "listed")])
    base = score_pair("J", "R", JD, r).score
    assert settings.apply({"score.evidence_strength.listed": 0.25}) == {"score.evidence_strength.listed": 0.25}
    assert score_pair("J", "R", JD, r).score < base
    assert settings.overrides() == {"score.evidence_strength.listed": 0.25}
    settings.reset()
    assert score_pair("J", "R", JD, r).score == base and settings.overrides() == {}


def test_unchanged_value_is_not_reported():
    assert settings.apply({"decide.delta": settings.current()["decide.delta"]}) == {}


def test_cache_only_never_calls_the_api(monkeypatch):
    """The Compare tab reads LLM zero-shot from cache; cache_only() must stop a call even in live mode."""
    from src import llm

    monkeypatch.setitem(cfg()["llm"], "offline", False)
    monkeypatch.setattr(llm, "_call", lambda *a, **k: (_ for _ in ()).throw(AssertionError("API called")))
    with llm.cache_only(), pytest.raises(llm.CacheMiss):
        llm.generate("a prompt that is certainly not cached 7f3a", salt="test")
