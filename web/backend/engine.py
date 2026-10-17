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
        self._baselines: dict[tuple, dict] = {}  # (job, jd text, pool) -> {cid: {system: score}}; filled on demand
        self._labels = {(r["job_id"], r["resume_id"]): r for r in agent.golden_labels()}
        agent.settings_spec()  # capture the start-up defaults before any override
        try:
            agent.update_settings(self.state.get("settings", {}))
        except ValueError as e:  # a stale or hand-edited override: fall back to the defaults
            print("ignoring saved settings:", e)
            self.state["settings"] = {}

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
            p = agent.parse_criteria(crit, variant="v2" if meta["kind"] == "custom" else "v1")
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
                           sorted(self.pool(jid)), agent.settings_spec()["overrides"]], sort_keys=True)

    # ---------------------------------------------------------------- candidates
    def pool(self, jid: str) -> dict[str, str]:
        """Candidates for a role. Benchmark roles: the fixed golden-set pool + uploads. A new role starts empty and
        holds only the library resumes a recruiter picked (`custom_jobs[jid]["pool"]`) + resumes uploaded to it."""
        ups = {cid: u["text"] for cid, u in self.state["uploads"].items() if u["job_id"] == jid}
        cj = self.state["custom_jobs"].get(jid)
        if cj is None or cj.get("pool") is None:  # benchmark role, or a role created before pools existed
            return {**self._texts, **ups}
        lib = self._library_texts()
        return {**{c: lib[c] for c in cj["pool"] if c in lib}, **ups}

    def _library_texts(self) -> dict[str, str]:
        return {**self._texts, **{cid: u["text"] for cid, u in self.state["uploads"].items()}}

    def library(self, jid: str) -> list[dict]:
        """Every already-parsed resume (benchmark corpus + uploads), with a short profile, for the pool picker."""
        prof: dict[str, dict] = {}
        for j in [next(iter(self._bench))] + sorted({u["job_id"] for u in self.state["uploads"].values()}):
            if j in self.job_ids():
                for o in self.screened(j):  # profiles come from cached extractions: no LLM call
                    prof.setdefault(o["candidate_id"], o)
        mine = set(self.pool(jid))
        out = []
        for cid in self._library_texts():
            o = prof.get(cid)
            up = self.state["uploads"].get(cid)
            out.append({"id": cid, "title": o["profile"]["title"] if o else "", "years": o["years_experience"] if o else None,
                        "skills": (o["profile"]["skills"] if o else [])[:8], "parsed": bool(o) and not o["extraction_error"],
                        "source": f"uploaded · {up['filename']}" if up else "benchmark corpus", "in_pool": cid in mine,
                        "own_upload": bool(up) and up["job_id"] == jid})
        return out

    def set_pool(self, jid: str, ids: list[str]) -> dict:
        cj = self.state["custom_jobs"].get(jid)
        if cj is None:
            raise ValueError("benchmark roles keep their golden-set candidate pool")
        lib = self._library_texts()
        own = {c for c, u in self.state["uploads"].items() if u["job_id"] == jid}
        unknown = [c for c in ids if c not in lib]
        if unknown:
            raise ValueError(f"unknown resume(s): {', '.join(unknown[:5])}")
        with self.lock:
            before = set(self.pool(jid))
            cj["pool"] = sorted(c for c in dict.fromkeys(ids) if c not in own)
            after = set(self.pool(jid))
            added, removed = sorted(after - before), sorted(before - after)
            if added or removed:
                self.job_state(jid)["history"].append({"at": _now(), "by": "recruiter", "candidate": None,
                                                       "action": f"pool:+{len(added)}/-{len(removed)}"})
            self.save()
            return {"added": added, "removed": removed, "size": len(after)}

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
        p = agent.parse_criteria(text, variant="v2")  # raises if the LLM is unavailable
        with self.lock:
            jid = f"C{len(self.state['custom_jobs']) + 1:02d}"
            self.state["custom_jobs"][jid] = {"title": title or p.get("title") or "Untitled role", "text": text,
                                              "location": location or p.get("location") or "", "job_type": job_type,
                                              "level": p.get("seniority", ""), "at": _now(), "pool": []}
            self.save()
            return {"id": jid}

    def activity(self, jid: str) -> list[dict]:
        return list(reversed(self.job_state(jid)["history"]))[:200]

    # ---------------------------------------------------------------- baseline comparison (on demand only)
    def _pool_baselines(self, jid: str) -> dict:
        meta, pool = self.job_meta(jid), self.pool(jid)
        key = (jid, meta["text"], tuple(sorted(pool)))
        if key not in self._baselines:
            # same TF-IDF corpus as eval.run baselines (all benchmark JDs + resumes), plus this role's extra documents
            corpus = [j["text"] for j in self._bench.values()] + list(self._texts.values())
            corpus += ([meta["text"]] if meta["kind"] == "custom" else []) + [t for c, t in pool.items() if c not in self._texts]
            scores = agent.baseline_scores(meta["text"], pool, corpus)  # outside the lock: may take a few seconds
            with self.lock:
                self._baselines = {k: v for k, v in self._baselines.items() if k[0] != jid}
                self._baselines[key] = scores
        return self._baselines[key]

    def compare(self, jid: str, cid: str, run_llm: bool = False) -> dict:
        """How each baseline would have ranked and decided this candidate, next to the pipeline.

        Runs only when a recruiter asks. Keyword/TF-IDF/embedding are scored once per role (needed for ranks) and
        cached; LLM zero-shot is read from the cache unless `run_llm` allows one API call for this pair.
        """
        rows = self.screened(jid)
        me = next(o for o in rows if o["candidate_id"] == cid)
        meta, n = self.job_meta(jid), len(rows)
        bs = self._pool_baselines(jid)
        thr = agent.baseline_thresholds()
        lab = self._labels.get((jid, cid))
        ideal = lab["ideal_decision"] if lab else None

        def entry(key, score, rank, threshold, decision, **extra):
            name, how = (("HYT pipeline", "Evidence-weighted fit from extracted requirements; every must-have and the threshold must pass.")
                         if key == "pipeline" else agent.BASELINES[key])
            return {"key": key, "name": name, "how": how, "score": score, "rank": rank, "threshold": threshold,
                    "decision": decision, "agrees": None if ideal is None or decision is None else decision == ideal, **extra}

        out = [entry("pipeline", me["score"], 1 + sum(o["score"] > me["score"] for o in rows), self.threshold(jid), me["decision"])]
        for k in ("keyword", "tfidf", "embedding", "embedding_chunked"):
            v = bs[cid][k]
            t = thr.get(k)
            if v is None:  # lite mode: no embedding model for this text
                out.append(entry(k, None, None, t, None, status="unavailable"))
                continue
            out.append(entry(k, round(v, 4), 1 + sum(x[k] is not None and x[k] > v for x in bs.values()), t,
                             None if t is None else ("advance" if v >= t else "escalate")))
        up = self.state["uploads"].get(cid)
        z = agent.zero_shot(meta["text"], self.pool(jid)[cid], allow_call=run_llm and not agent.settings()["offline"],
                            private=up is not None)
        zt = thr.get("llm_zeroshot")
        if z["status"] == "ok":
            out.append(entry("llm_zeroshot", z["score"], None, zt, "advance" if z["score"] >= zt else "escalate",
                             own_decision=z["own_decision"], status="ok"))
        else:
            out.append(entry("llm_zeroshot", None, None, zt, None, status=z["status"]))
        return {"pool_size": n, "systems": out,
                "label": {"relevance": lab["relevance"], "ideal": ideal} if lab else None,
                "live": not agent.settings()["offline"]}

    # ---------------------------------------------------------------- runtime settings
    def update_settings(self, patch: dict | None, reset: bool = False) -> dict:
        """Apply (or reset) runtime settings. Every job re-screens on next read; human stage moves are kept."""
        with self.lock:
            if reset:
                agent.reset_settings()
                changed = {"reset": True}
            else:
                changed = agent.update_settings(patch or {})
            if changed:
                self._parsed.clear()  # requirement post-processing flags apply at parse time
                self._screened.clear()
                self.state["settings"] = agent.settings_spec()["overrides"]
                self.state.setdefault("settings_history", []).append({"at": _now(), "by": "recruiter", "changed": changed})
                self.save()
            return {"changed": changed, **self.settings_view()}

    def settings_view(self) -> dict:
        return {**agent.settings_spec(), "history": self.state.get("settings_history", [])[-20:][::-1]}

    def warm(self):
        t = time.time()
        for jid in self.job_ids():
            try:
                self.screened(jid)
            except Exception as e:  # noqa: BLE001
                print("warm failed", jid, e)
        print(f"engine warm in {time.time() - t:.1f}s")
