import pytest
from pydantic import BaseModel

from src import llm


class _R:
    text = "ok"


class _Client:
    def __init__(self, behaviour):
        self.b = behaviour
        self.models = self

    def generate_content(self, **kw):
        if self.b == "daily":
            raise RuntimeError("429 RESOURCE_EXHAUSTED GenerateRequestsPerDayPerProjectPerModel-FreeTier")
        return _R()


class ResumeExtraction(BaseModel):  # same name as the real schema -> "parse" purpose
    x: str = ""


class JDExtraction(BaseModel):
    x: str = ""


@pytest.fixture(autouse=True)
def reset(monkeypatch):
    llm._exhausted.clear()
    llm._clients.clear()
    monkeypatch.delenv("GEMINI_PARSE_API_KEY", raising=False)
    yield
    llm._exhausted.clear()
    llm._clients.clear()


def _pool(monkeypatch, keys):
    for i, k in enumerate(keys):
        monkeypatch.setenv("GEMINI_API_KEY" if i == 0 else f"GEMINI_API_KEY_{i + 1}", k)


def test_failover_to_next_key(monkeypatch):
    monkeypatch.setattr(llm, "_keys", lambda purpose=None: ["k1", "k2", "k3"])
    monkeypatch.setattr(llm, "_client_for", lambda k: _Client("daily" if k in ("k1", "k2") else "ok"))
    assert llm._call("p", "m", None, 0.0) == "ok"
    assert {("k1", "m"), ("k2", "m")} <= llm._exhausted


def test_all_keys_exhausted(monkeypatch):
    monkeypatch.setattr(llm, "_keys", lambda purpose=None: ["k1", "k2"])
    monkeypatch.setattr(llm, "_client_for", lambda k: _Client("daily"))
    with pytest.raises(llm.LLMError, match="all 2 key"):
        llm._call("p", "m", None, 0.0)


def test_exhaustion_is_per_model():
    llm._exhausted.add(("k1", "judge"))
    assert llm._pick_key("generator", ["k1"]) == "k1"
    with pytest.raises(llm.LLMError):
        llm._pick_key("judge", ["k1"])


def test_parse_key_first_for_resumes_only(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "general-key")  # self-contained: never depends on the developer's .env
    monkeypatch.setenv("GEMINI_PARSE_API_KEY", "parse-key")
    general = llm._keys()
    assert "parse-key" not in general
    assert llm._keys("parse")[0] == "parse-key" and llm._keys("parse")[1:] == general
    used = []
    monkeypatch.setattr(llm, "_client_for", lambda k: (used.append(k), _Client("ok"))[1])
    llm._call("p", "m", ResumeExtraction, 0.0)
    llm._call("p", "m", JDExtraction, 0.0)
    assert used[0] == "parse-key" and used[1] != "parse-key"


def test_parse_key_falls_back_to_pool_when_spent(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "general-key")
    monkeypatch.setenv("GEMINI_PARSE_API_KEY", "parse-key")
    monkeypatch.setattr(llm, "_client_for", lambda k: _Client("daily" if k == "parse-key" else "ok"))
    assert llm._call("p", "m", ResumeExtraction, 0.0) == "ok"
    assert ("parse-key", "m") in llm._exhausted


def test_uploaded_resumes_cache_privately(monkeypatch, tmp_path):
    import agent
    from src.config import cfg

    monkeypatch.setattr(llm, "path", lambda key: tmp_path)
    monkeypatch.setitem(cfg()["llm"], "offline", False)
    ext = '{"skills":[{"name":"Python","proficiency":"listed","evidence":"Python"}],"roles":[],"projects":[],' \
          '"education":[],"location":null,"language":"en"}'
    monkeypatch.setattr(llm, "_call", lambda *a, **k: ext)
    crit = {"title": "t", "must_have": [{"name": "python"}]}
    agent.screen("Python developer, upload", crit, received="2026-10-15")      # real upload -> private
    agent.screen("Python developer, benchmark", crit)                          # benchmark -> public
    assert len(list((tmp_path / "private").glob("*.json"))) == 1
    assert len(list((tmp_path / "llm").glob("*.json"))) == 1
