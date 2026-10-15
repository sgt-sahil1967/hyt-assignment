"""Workflow layer around agent.screen(): jobs, editable requirements, pipeline stages, audit log.

Stages:  new → shortlisted → interview, or → rejected
  * the AGENT may only move a candidate into `shortlisted` (decision == advance at the job's threshold)
  * `interview` and `rejected` are human-only; rejecting requires a reason (the agent never rejects)
  * a human move locks the stage; re-scoring never overrides a human decision
"""
from __future__ import annotations

import json
import re
import threading
import time
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import agent
from src.decide import info_codes
from src.normalize import is_known

STATE_FILE = Path(__file__).resolve().parent / "state.json"
STAGES = ["new", "shortlisted", "interview", "rejected"]
THRESHOLD_CODES = {"BORDERLINE_SCORE", "BELOW_THRESHOLD", "LOW_FIT"}
EDU_RANK = agent.EDU_RANK


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "req"


class Engine:
    def __init__(self):
        self.lock = threading.RLock()
        self.state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"jobs": {}, "uploads": {}, "custom_jobs": {}}
        self.state.setdefault("custom_jobs", {})
        self._bench = {j["id"]: j for j in agent.benchmark_jobs()}
        self._texts = agent.benchmark_resumes()
        self._extractions: dict[str, dict | None] = {}
        self._parsed: dict[str, dict] = {}
        self._screened: dict[tuple, list[dict]] = {}
        self._labels = {(r["job_id"], r["resume_id"]): r for r in agent.golden_labels()}

    # ---------------------------------------------------------------- persistence
    def save(self):
        STATE_FILE.write_text(json.dumps(self.state, indent=1))

    def job_state(self, jid: str) -> dict:
        js = self.state["jobs"].setdefault(jid, {})
        js.setdefault("stages", {})
        js.setdefault("history", [])
        js.setdefault("requirements", None)
        js.setdefault("threshold", None)
        js.setdefault("min_years", "unset")
        return js

    # ---------------------------------------------------------------- jobs
    def job_meta(self, jid: str) -> dict:
        if jid in self._bench:
            return {**self._bench[jid], "kind": "benchmark"}
        cj = self.state["custom_jobs"].get(jid)
        if not cj:
            raise KeyError(jid)
        return {"id": jid, "title": cj["title"], "location": cj.get("location", ""), "job_type": cj.get("job_type", ""),
                "level": cj.get("level", ""), "split": "custom", "text": cj["text"], "kind": "custom"}

    def job_ids(self) -> list[str]:
        return list(self._bench) + list(self.state["custom_jobs"])

    def parsed(self, jid: str) -> dict:
        if jid not in self._parsed:
            meta = self.job_meta(jid)
            crit = {"job_id": jid} if meta["kind"] == "benchmark" else meta["text"]
            p = agent.parse_criteria(crit)
            p.setdefault("job_type", meta["job_type"])
            p.setdefault("location_meta", meta["location"])
            self._parsed[jid] = p
        return self._parsed[jid]

    def requirements(self, jid: str) -> list[dict]:
        """Effective requirement list: recruiter overrides if any, else the AI-parsed ones."""
        js = self.job_state(jid)
        if js["requirements"] is not None:
            return js["requirements"]
        p = self.parsed(jid)
        out = []
        for level, items in (("must", p["must_have"]), ("nice", p["nice_to_have"])):
            for r in items:
                scored = r["type"] in ("skill", "degree")
                out.append({"id": slug(f"{level}-{r['name']}"), "name": r["name"], "type": r["type"],
                            "alternatives": list(r.get("alternatives") or []),
                            "level": level if scored else "unscored", "ai_level": level if scored else "unscored",
                            "source": "ai"})
        return out

    def min_years(self, jid: str):
        js = self.job_state(jid)
        return self.parsed(jid).get("min_years") if js["min_years"] == "unset" else js["min_years"]

    def threshold(self, jid: str) -> float:
        js = self.job_state(jid)
        return js["threshold"] if js["threshold"] is not None else agent.settings()["t_high"]

    def criteria(self, jid: str) -> dict:
        p = deepcopy(self.parsed(jid))
        reqs = self.requirements(jid)
        pick = lambda lvl: [{"name": r["name"], "type": r["type"], "alternatives": r["alternatives"]}  # noqa: E731
                            for r in reqs if r["level"] == lvl]
        p["must_have"], p["nice_to_have"] = pick("must"), pick("nice")
        p["min_years"] = self.min_years(jid)
        return p

    def version(self, jid: str) -> str:
        js = self.job_state(jid)
        return json.dumps([self.requirements(jid), self.min_years(jid), self.threshold(jid),
                           sorted(self.pool(jid)), agent.settings()["offline"]], sort_keys=True)

    # ---------------------------------------------------------------- candidates
    def pool(self, jid: str) -> dict[str, str]:
        ups = {cid: u["text"] for cid, u in self.state["uploads"].items() if u["job_id"] == jid}
        return {**self._texts, **ups}

    def _screen_one(self, jid: str, cid: str, text: str, crit: dict, t: float) -> dict:
        up = self.state["uploads"].get(cid, {})
        ext = self._extractions.get(cid)
        o = agent.screen(text, crit, candidate_id=cid, threshold=t, extraction=ext, html=up.get("html", False),
                         hidden_chars_removed=up.get("hidden_chars_removed", 0), received=up.get("at"))
        if ext is None and o["extraction"] is not None:
            self._extractions[cid] = o["extraction"]
        return o

    def screened(self, jid: str) -> list[dict]:
        with self.lock:
            key = (jid, self.version(jid))
            if key not in self._screened:
                crit, t = self.criteria(jid), self.threshold(jid)
                rows = [self._screen_one(jid, cid, txt, crit, t) for cid, txt in self.pool(jid).items()]
                rows.sort(key=lambda o: (-o["score"], -(o["components"].get("must_have") or 0), o["candidate_id"]))
                self._screened = {k: v for k, v in self._screened.items() if k[0] != jid}
                self._screened[key] = rows
            return self._screened[key]

    def _summary(self, jid: str, o: dict, rank: int) -> dict:
        js = self.job_state(jid)
        st_ = js["stages"].get(o["candidate_id"])
        blocking = [r for r in o["reasons"] if r not in THRESHOLD_CODES | info_codes()]
        auto_stage = "shortlisted" if o["decision"] == "advance" else "new"
        stage = st_["stage"] if st_ else auto_stage
        lab = self._labels.get((jid, o["candidate_id"]))
        ev = {}
        for e in o["evidence"]:
            ev[slug(f"{e['level']}-{e['requirement']}")] = {"strength": e["strength"], "basis": e["basis"]}
        return {
            "id": o["candidate_id"], "rank": rank, "score": o["score"], "decision": o["decision"], "queue": o["queue"],
            "reasons": o["reasons"], "blocking": blocking, "gates_passed": not blocking,
            "components": o["components"], "years": o["years_experience"], "title": o["profile"]["title"],
            "skills": o["profile"]["skills"], "education": o["profile"]["education_level"],
            "location": o["profile"]["location"], "stage": stage, "stage_by": st_["by"] if st_ else ("agent" if auto_stage == "shortlisted" else None),
            "locked": bool(st_), "evidence": ev, "uploaded": o["candidate_id"] in self.state["uploads"],
            "manipulation": "SUSPECTED_MANIPULATION" in o["reasons"], "extraction_error": o["extraction_error"],
            "label": lab["relevance"] if lab else None, "ideal": lab["ideal_decision"] if lab else None,
        }

    def candidates(self, jid: str) -> list[dict]:
        return [self._summary(jid, o, i) for i, o in enumerate(self.screened(jid), 1)]

    def candidate(self, jid: str, cid: str) -> dict:
        rows = self.screened(jid)
        i, o = next((i, o) for i, o in enumerate(rows, 1) if o["candidate_id"] == cid)
        s = self._summary(jid, o, i)
        return {**s, "full_evidence": o["evidence"], "gaps": o["gaps"], "reason_help": o["reason_help"],
                "masked_text": o["masked_text"], "sanitizer_flags": o["sanitizer_flags"],
                "injection_matches": o["injection_matches"], "extraction": o["extraction"],
                **self._explanation(jid, cid),
                "history": [h for h in self.job_state(jid)["history"] if h["candidate"] == cid]}

    # ---------------------------------------------------------------- job summary
    def job_summary(self, jid: str) -> dict:
        meta = self.job_meta(jid)
        cands = self.candidates(jid)
        cnt = {s: sum(c["stage"] == s for c in cands) for s in STAGES}
        return {"id": jid, "title": meta["title"], "location": meta["location"], "job_type": meta["job_type"],
                "level": meta["level"], "kind": meta["kind"], "split": meta["split"], "applicants": len(cands),
                "stages": cnt, "needs_review": sum(c["queue"] == "review" and c["stage"] == "new" for c in cands),
                "edited": self.job_state(jid)["requirements"] is not None}

    def job_detail(self, jid: str) -> dict:
        meta = self.job_meta(jid)
        p = self.parsed(jid)
        cands = self.candidates(jid)
        reqs = self.requirements(jid)
        for r in reqs:
            hits = [c["evidence"].get(slug(f"{r['level']}-{r['name']}"), {}).get("strength", 0) for c in cands]
            r["coverage"] = sum(h >= 0.5 for h in hits) if r["level"] in ("must", "nice") else None
            r["key"] = slug(f"{r['level']}-{r['name']}")  # evidence key on candidate rows
            # a requirement outside the skill map is matched by exact name only: tell the recruiter
            r["mapped"] = r["type"] != "skill" or any(is_known(o) for o in [r["name"], *r["alternatives"]])
        return {**self.job_summary(jid), "text": meta["text"], "summary": p.get("summary", ""),
                "seniority": p.get("seniority"), "min_years": self.min_years(jid), "ai_min_years": p.get("min_years"),
                "equivalent_experience_allowed": p.get("equivalent_experience_allowed"), "requirements": reqs,
                "threshold": self.threshold(jid), "default_threshold": agent.settings()["t_high"]}

    # ---------------------------------------------------------------- mutations
    def _diff(self, jid: str, before: list[dict]) -> dict:
        b = {c["id"]: c for c in before}
        after = self.candidates(jid)
        entered = [c["id"] for c in after if c["stage"] == "shortlisted" and b.get(c["id"], {}).get("stage") != "shortlisted"]
        left = [c["id"] for c in after if c["stage"] != "shortlisted" and b.get(c["id"], {}).get("stage") == "shortlisted"]
        return {"entered_shortlist": entered, "left_shortlist": left}

    def set_requirements(self, jid: str, reqs: list[dict] | None, min_years="keep", who: str = "recruiter") -> dict:
        with self.lock:
            before = self.candidates(jid)
            js = self.job_state(jid)
            if reqs is not None:
                ai = {r["id"]: r for r in self.requirements(jid)} if js["requirements"] is None else \
                    {r["id"]: r for r in js["requirements"]}
                clean = []
                for r in reqs:
                    lvl = r["level"] if r["level"] in ("must", "nice", "ignored", "unscored") else "ignored"
                    prev = ai.get(r.get("id"))
                    clean.append({"id": r.get("id") or slug(f"{lvl}-{r['name']}"), "name": r["name"].strip(),
                                  "type": r.get("type") or "skill", "alternatives": r.get("alternatives") or [],
                                  "level": lvl, "ai_level": (prev or {}).get("ai_level", "added"),
                                  "source": "ai" if prev and prev.get("ai_level") == lvl else "recruiter"})
                js["requirements"] = clean
            if min_years != "keep":
                js["min_years"] = min_years
            js["history"].append({"at": _now(), "by": who, "candidate": None, "action": "requirements_updated"})
            self.save()
            return self._diff(jid, before)

    def reset(self, jid: str) -> dict:
        with self.lock:
            before = self.candidates(jid)
            js = self.job_state(jid)
            js["requirements"], js["threshold"], js["min_years"] = None, None, "unset"
            js["history"].append({"at": _now(), "by": "recruiter", "candidate": None, "action": "reset_to_ai"})
            self.save()
            return self._diff(jid, before)

    def set_threshold(self, jid: str, t: float) -> dict:
        with self.lock:
            before = self.candidates(jid)
            self.job_state(jid)["threshold"] = round(float(t), 3)
            self.job_state(jid)["history"].append({"at": _now(), "by": "recruiter", "candidate": None,
                                                   "action": f"threshold_set:{round(float(t), 3)}"})
            self.save()
            return self._diff(jid, before)

    def move(self, jid: str, cid: str, stage: str, note: str | None, who: str = "recruiter") -> dict:
        if stage not in STAGES:
            raise ValueError(f"unknown stage {stage}")
        if stage == "rejected" and not (note or "").strip():
            raise ValueError("rejecting a candidate requires a reason")
        with self.lock:
            cur = next(c for c in self.candidates(jid) if c["id"] == cid)
            js = self.job_state(jid)
            js["stages"][cid] = {"stage": stage, "by": who, "at": _now()}
            js["history"].append({"at": _now(), "by": who, "candidate": cid, "action": f"{cur['stage']}→{stage}",
                                  "note": note or ""})
            self.save()
            return {"id": cid, "stage": stage}

    def retry(self, jid: str, cid: str) -> dict:
        """Re-run extraction for a candidate whose parse failed (e.g. API quota). Successful parses are never redone."""
        with self.lock:
            self._extractions.pop(cid, None)
            self._screened = {k: v for k, v in self._screened.items() if k[0] != jid}
            c = self.candidate(jid, cid)
            js = self.job_state(jid)
            js["history"].append({"at": _now(), "by": "recruiter", "candidate": cid,
                                  "action": "retry_parse:" + ("ok" if not c["extraction_error"] else "failed")})
            self.save()
            return {"id": cid, "extraction_error": c["extraction_error"], "score": c["score"], "decision": c["decision"]}

    def unlock(self, jid: str, cid: str) -> dict:
        with self.lock:
            js = self.job_state(jid)
            js["stages"].pop(cid, None)
            js["history"].append({"at": _now(), "by": "recruiter", "candidate": cid, "action": "returned_to_agent"})
            self.save()
            return {"id": cid}

    def _scoring_version(self, jid: str) -> str:
        return json.dumps([self.requirements(jid), self.min_years(jid), self.threshold(jid)], sort_keys=True)

    def _explanation(self, jid: str, cid: str) -> dict:
        """An explanation is only valid for the scoring it described; edits make older ones stale."""
        js = self.job_state(jid)
        mine = js.get("explanations", {}).get(cid)
        if isinstance(mine, dict):
            return {"explanation": mine["text"], "explanation_stale": mine["version"] != self._scoring_version(jid)}
        cached = agent.cached_explanation(jid, cid)  # written for the AI-parsed requirements + default threshold
        pristine = js["requirements"] is None and js["threshold"] is None and js["min_years"] == "unset"
        return {"explanation": cached, "explanation_stale": bool(cached) and not pristine}

    def explain(self, jid: str, cid: str) -> str:
        crit, t = self.criteria(jid), self.threshold(jid)
        up = self.state["uploads"].get(cid, {})
        o = agent.screen(self.pool(jid)[cid], crit, candidate_id=cid, threshold=t,
                         extraction=self._extractions.get(cid), explain=True, received=up.get("at"),
                         html=up.get("html", False), hidden_chars_removed=up.get("hidden_chars_removed", 0))
        if not o.get("explanation"):  # never store an error message as if it were an explanation
            raise RuntimeError(o.get("explanation_error") or "explanation unavailable")
        js = self.job_state(jid)
        js.setdefault("explanations", {})[cid] = {"text": o["explanation"], "version": self._scoring_version(jid)}
        self.save()
        return o["explanation"]

    def upload(self, jid: str, filename: str, data: bytes) -> dict:
        d = agent.read_document(filename, data)
        with self.lock:
            n = len(self.state["uploads"]) + 1
            cid = f"U{n:03d}"
            o = agent.screen(d["text"], self.criteria(jid), candidate_id=cid, html=d["html"],
                             hidden_chars_removed=d["hidden_chars_removed"], threshold=self.threshold(jid),
                             received=_now())
            if o["extraction"] is not None:
                self._extractions[cid] = o["extraction"]
            self.state["uploads"][cid] = {"job_id": jid, "filename": filename, "text": d["text"], "html": d["html"],
                                          "hidden_chars_removed": d["hidden_chars_removed"], "at": _now()}
            self.job_state(jid)["history"].append({"at": _now(), "by": "recruiter", "candidate": cid,
                                                   "action": f"uploaded:{filename}"})
            self.save()
            return {"id": cid, "filename": filename, "score": o["score"], "decision": o["decision"],
                    "reasons": o["reasons"], "extraction_error": o["extraction_error"],
                    "flags": o["sanitizer_flags"], "warning": d.get("warning")}

    def create_job(self, title: str, text: str, location: str = "", job_type: str = "") -> dict:
        p = agent.parse_criteria(text)  # raises if the LLM is unavailable
        with self.lock:
            jid = f"C{len(self.state['custom_jobs']) + 1:02d}"
            self.state["custom_jobs"][jid] = {"title": title or p.get("title") or "Untitled role", "text": text,
                                              "location": location or p.get("location") or "", "job_type": job_type,
                                              "level": p.get("seniority", ""), "at": _now()}
            self.save()
            return {"id": jid}

    def activity(self, jid: str) -> list[dict]:
        return list(reversed(self.job_state(jid)["history"]))[:200]

    def warm(self):
        t = time.time()
        for jid in self.job_ids():
            try:
                self.screened(jid)
            except Exception as e:  # noqa: BLE001
                print("warm failed", jid, e)
        print(f"engine warm in {time.time() - t:.1f}s")
