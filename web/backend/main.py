"""FastAPI backend for the HYT screening workspace.

    .venv/bin/uvicorn web.backend.main:app --port 8000 --reload

Every score/decision comes from agent.screen(); this layer adds jobs, editable requirements, stages and an audit log.
"""
from __future__ import annotations

import math
import os
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HYT_OFFLINE", "1")

from fastapi import FastAPI, File, HTTPException, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel  # noqa: E402

import agent  # noqa: E402

from .engine import STAGES, Engine  # noqa: E402

app = FastAPI(title="HYT Screening API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5180", "http://127.0.0.1:5180"],
                   allow_methods=["*"], allow_headers=["*"])
E = Engine()
threading.Thread(target=E.warm, daemon=True).start()


def _job(jid: str):
    if jid not in E.job_ids():
        raise HTTPException(404, f"unknown job {jid}")


class Requirement(BaseModel):
    id: str | None = None
    name: str
    type: str | None = "skill"
    alternatives: list[str] = []
    level: str


class RequirementsIn(BaseModel):
    requirements: list[Requirement] | None = None
    min_years: float | None = None
    set_min_years: bool = False


class ThresholdIn(BaseModel):
    threshold: float


class MoveIn(BaseModel):
    stage: str
    note: str | None = None


class JobIn(BaseModel):
    title: str = ""
    text: str
    location: str = ""
    job_type: str = ""


class SettingsIn(BaseModel):
    live: bool


@app.get("/api/settings")
def settings():
    return {**agent.settings(), "stages": STAGES, "reason_help": agent.REASON_HELP}


@app.put("/api/settings")
def put_settings(s: SettingsIn):
    agent.set_offline(not s.live)
    return agent.settings()


@app.get("/api/jobs")
def jobs():
    return [E.job_summary(j) for j in E.job_ids()]


@app.post("/api/jobs")
def create_job(j: JobIn):
    try:
        return E.create_job(j.title, j.text, j.location, j.job_type)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"Could not parse the JD ({e}). Enable live Gemini calls in settings.")


@app.get("/api/jobs/{jid}")
def job(jid: str):
    _job(jid)
    return E.job_detail(jid)


@app.put("/api/jobs/{jid}/requirements")
def put_requirements(jid: str, body: RequirementsIn):
    _job(jid)
    reqs = [r.model_dump() for r in body.requirements] if body.requirements is not None else None
    return E.set_requirements(jid, reqs, body.min_years if body.set_min_years else "keep")


@app.put("/api/jobs/{jid}/threshold")
def put_threshold(jid: str, body: ThresholdIn):
    _job(jid)
    if not 0 <= body.threshold <= 1:
        raise HTTPException(422, "threshold must be in [0, 1]")
    return E.set_threshold(jid, body.threshold)


@app.post("/api/jobs/{jid}/reset")
def reset(jid: str):
    _job(jid)
    return E.reset(jid)


@app.get("/api/jobs/{jid}/candidates")
def candidates(jid: str):
    _job(jid)
    return E.candidates(jid)


@app.get("/api/jobs/{jid}/candidates/{cid}")
def candidate(jid: str, cid: str):
    _job(jid)
    try:
        return E.candidate(jid, cid)
    except StopIteration:
        raise HTTPException(404, f"unknown candidate {cid}")


@app.post("/api/jobs/{jid}/candidates/{cid}/stage")
def move(jid: str, cid: str, body: MoveIn):
    _job(jid)
    try:
        return E.move(jid, cid, body.stage, body.note)
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/api/jobs/{jid}/candidates/{cid}/unlock")
def unlock(jid: str, cid: str):
    _job(jid)
    return E.unlock(jid, cid)


@app.post("/api/jobs/{jid}/candidates/{cid}/retry")
def retry(jid: str, cid: str):
    _job(jid)
    return E.retry(jid, cid)


@app.post("/api/jobs/{jid}/candidates/{cid}/explain")
def explain(jid: str, cid: str):
    _job(jid)
    try:
        return {"explanation": E.explain(jid, cid)}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(503, f"Explanation needs a live Gemini call ({type(e).__name__}).")


@app.post("/api/jobs/{jid}/upload")
async def upload(jid: str, files: list[UploadFile] = File(...)):
    _job(jid)
    out = []
    for f in files:
        try:
            out.append(E.upload(jid, f.filename or "resume.txt", await f.read()))
        except Exception as e:  # noqa: BLE001
            out.append({"filename": f.filename, "error": str(e)[:200]})
    return out


@app.get("/api/jobs/{jid}/activity")
def activity(jid: str):
    _job(jid)
    return E.activity(jid)


@app.get("/api/insights")
def insights():
    names = ["metrics.json", "baselines.json", "ablations.json", "extraction_metrics.json", "robustness.json",
             "adversarial.json", "fairness.json", "judge_summary.json", "judge_agreement.json", "label_agreement.json",
             "v1_1.json", "posthoc.json", "real_set.json"]
    return _finite({n.removesuffix(".json"): agent.results(n) for n in names})


def _finite(o):
    """NaN/inf (e.g. MRR on a job with no good candidate) are not valid JSON: send null instead."""
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return {k: _finite(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_finite(v) for v in o]
    return o
