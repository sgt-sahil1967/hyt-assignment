"""End-to-end screening: screen(job_id) -> ranked candidates with score, decision, reasons, evidence, gaps.

    python -m src.pipeline --job JD01 [--top 10] [--explain] [--all-resumes]
"""
from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from . import embed
from .config import ROOT, cfg, path, read_json
from .decide import decide, doc_flags, keyword_stuffing
from .explain import explain
from .extract import extract_jd, extract_resume
from .mask import mask
from .sanitize import sanitize_html, sanitize_text
from .score import rank, score_pair

WORKERS = 4


def load():
    p = path("processed")
    return read_json(p / "jds.json"), read_json(p / "resumes.json")


def ingest_text(rid: str, raw: str, html: bool = False, mask_names: bool | None = None) -> dict:
    """Same ingestion path as data/prepare.py, for synthetic variants (fairness / adversarial)."""
    from langdetect import detect

    s = sanitize_html(raw) if html else sanitize_text(raw)
    mn = cfg()["mask"]["names"] if mask_names is None else mask_names
    text, counts = mask(s.clean_text, mask_names=mn)
    try:
        lang = detect(text)
    except Exception:
        lang = "unknown"
    return {"id": rid, "text": text, "words": len(text.split()), "language": lang, "flags": s.flags,
            "injection_matches": s.injection_matches, "mask_counts": counts}


def jd_extraction(jd: dict, salt: str = "") -> dict | None:
    from .requirements import postprocess

    x, meta = extract_jd(jd["text"], salt=salt)
    return postprocess(x.model_dump(), jd["text"]) if x else None


def resume_extraction(r: dict, salt: str = "") -> tuple[dict | None, dict]:
    x, meta = extract_resume(r["text"], salt=salt)
    return (x.model_dump() if x else None), meta


def extract_many(resumes: dict[str, dict], salt: str = "") -> dict[str, tuple[dict | None, dict]]:
    with ThreadPoolExecutor(WORKERS) as ex:
        out = dict(zip(resumes, ex.map(lambda r: resume_extraction(r, salt), resumes.values())))
    return out


def screen_resumes(job_id: str, jd: dict, resumes: dict[str, dict], *, salt: str = "", with_explanations: bool = False,
                   jd_x: dict | None = None, extractions: dict | None = None) -> list[dict]:
    jd_x = jd_x or jd_extraction(jd, salt="")  # JD extraction is shared across runs (only resumes vary)
    if jd_x is None:
        raise RuntimeError(f"JD extraction failed for {job_id}")
    extractions = extractions or extract_many(resumes, salt)
    rows, scored = [], []
    for rid, r in resumes.items():
        x, xmeta = extractions[rid]
        meta = dict(r)
        if x is not None:
            meta["stuffing"] = keyword_stuffing(x["skills"])
        flags = doc_flags(meta, x, jd_x, jd)
        if x is None:
            x = {"skills": [], "roles": [], "projects": [], "education": []}
        sr = score_pair(job_id, rid, jd_x, x)
        dec = decide(sr, jd_x, flags)
        scored.append(sr)
        rows.append({"sr": sr, "dec": dec, "x": x, "xmeta": xmeta, "r": r, "flags": flags})
    order = {s.resume_id: i for i, s in enumerate(rank(scored))}
    rows.sort(key=lambda row: order[row["sr"].resume_id])

    if with_explanations:
        with ThreadPoolExecutor(WORKERS) as ex:
            exps = list(ex.map(lambda row: explain(row["sr"], row["dec"], jd_x["title"], row["r"]["text"]), rows))
        for row, e in zip(rows, exps):
            row["explanation"] = e
    embed.save()

    out = []
    for i, row in enumerate(rows, 1):
        sr, dec = row["sr"], row["dec"]
        out.append({
            "rank": i, "job_id": job_id, "resume_id": sr.resume_id, "score": sr.score,
            "decision": dec.decision, "queue": dec.queue, "reasons": dec.reasons,
            "components": sr.components, "yoe": sr.yoe, "capped": sr.capped,
            "evidence": [e.model_dump() for e in sr.evidence], "gaps": sr.gaps,
            "flags": row["flags"], "yoe_confidence": sr.yoe_confidence,
            "extraction_attempts": row["xmeta"].get("attempts"), "extraction_error": row["xmeta"].get("error"),
            **({"explanation": row["explanation"]} if "explanation" in row else {}),
        })
    return out


def config_hash() -> str:
    return hashlib.sha256((ROOT / "config.yaml").read_bytes()).hexdigest()[:12]


def log_decisions(rows: list[dict], tag: str = "screen") -> None:
    c = cfg()
    f = path("results") / "decision_log.jsonl"
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(f, "a") as fh:
        for r in rows:
            fh.write(json.dumps({
                "ts": stamp, "tag": tag, "job_id": r["job_id"], "resume_id": r["resume_id"], "score": r["score"],
                "decision": r["decision"], "queue": r["queue"], "reasons": r["reasons"], "components": r["components"],
                "model": c["llm"]["model"], "prompt_version": c["llm"]["prompt_version"], "config": config_hash(),
                "t_high": c["decide"]["t_high"],
            }) + "\n")


def screen(job_id: str, resume_ids: list[str] | None = None, explain_top: int = 0) -> list[dict]:
    jds, res = load()
    jd = jds[job_id]
    pool = {k: v for k, v in res.items() if resume_ids is None or k in resume_ids}
    rows = screen_resumes(job_id, jd, pool)
    if explain_top:
        jd_x = jd_extraction(jd)
        from .decide import Decision  # noqa
        top = rows[:explain_top]
        with ThreadPoolExecutor(WORKERS) as ex:
            exps = list(ex.map(lambda r: _explain_row(r, jd_x, pool), top))
        for r, e in zip(top, exps):
            r["explanation"] = e
    return rows


def row_to_sr(row: dict):
    from .schemas import Evidence, ScoreResult

    return ScoreResult(job_id=row["job_id"], resume_id=row["resume_id"], score=row["score"], components=row["components"],
                       evidence=[Evidence(**e) for e in row["evidence"]], gaps=row["gaps"], yoe=row["yoe"],
                       yoe_confidence=row.get("yoe_confidence", "high"), capped=row["capped"])


def _explain_row(row: dict, jd_x: dict, pool: dict) -> dict:
    from .schemas import Decision

    dec = Decision(decision=row["decision"], reasons=row["reasons"], queue=row["queue"])
    return explain(row_to_sr(row), dec, jd_x["title"], pool[row["resume_id"]]["text"])


def main():
    ap = argparse.ArgumentParser(description="Screen resumes for one job")
    ap.add_argument("--job", required=True)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--explain", type=int, default=3, help="explain the top N (0 = none)")
    ap.add_argument("--golden-only", action="store_true", help="only the 20 golden-set candidates for this job")
    a = ap.parse_args()

    ids = None
    if a.golden_only:
        import pandas as pd
        lab = pd.read_csv(ROOT / "golden" / "labels.csv")
        ids = list(lab[lab.job_id == a.job].resume_id)
    rows = screen(a.job, ids, explain_top=a.explain)
    log_decisions(rows)
    jds, _ = load()
    print(f"\n{a.job}: {jds[a.job]['title']}  ({len(rows)} candidates, T_high={cfg()['decide']['t_high']})\n")
    print(f"{'#':>3} {'resume':7} {'score':>6}  {'decision':9} {'must':>5} {'nice':>5} {'exp':>5} {'role':>5}  reasons")
    for r in rows[: a.top]:
        c = r["components"]
        f = lambda v: "  -  " if v is None else f"{v:5.2f}"  # noqa: E731
        print(f"{r['rank']:>3} {r['resume_id']:7} {r['score']:6.3f}  {r['decision']:9} {f(c['must_have'])} "
              f"{f(c['nice_to_have'])} {f(c['experience'])} {f(c['role_relevance'])}  {','.join(r['reasons'])}")
    for r in rows[: a.explain]:
        print(f"\n--- {r['resume_id']} (rank {r['rank']}, {r['decision']})")
        ev = [f"{e['requirement']}={e['strength']:.2f}[{e['basis']}]" for e in r["evidence"] if e["level"] == "must"]
        print("  must-haves:", "; ".join(ev))
        print("  gaps:", "; ".join(r["gaps"]) or "none")
        if "explanation" in r:
            print("  explanation:", r["explanation"]["explanation"])


if __name__ == "__main__":
    main()
