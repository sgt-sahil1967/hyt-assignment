"""Real-resume sanity set (Kaggle resumes + arshkon postings), evaluated with the FROZEN scoring and threshold.

    python -m eval.real_set install SRC_DIR   # load Sonnet-agent extractions into cache/llm (model 'claude-sonnet-agent')
    python -m eval.real_set run               # offline: pipeline + baselines on 50 pairs -> results/real_set*.json

Differences from the main evaluation, stated in REPORT:
  * extraction by Claude Sonnet run as background agents (Gemini quota), cached under its own model name;
  * labels by Claude Sonnet agents, blind to the pipeline, pending the author's review (golden_real/labels.csv);
  * nothing is tuned on this set: T_high = the dev-tuned 0.49; both v1.0 and v1.1 policies are reported.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HYT_OFFLINE", "1")

from src.config import cfg, path, sha, write_json  # noqa: E402

from .metrics import GOOD, bootstrap, decision_metrics, ranking_metrics  # noqa: E402

MODEL = "claude-sonnet-agent"
DATA = ROOT / "data" / "processed_real"
LAB = ROOT / "golden_real" / "labels.csv"


def _load():
    return (json.loads((DATA / "resumes.json").read_text()), json.loads((DATA / "jds.json").read_text()),
            pd.read_csv(DATA / "pairs.csv"))


def install(src: str):
    """Validate agent outputs against the pipeline schemas and write them as cache entries for the exact prompts."""
    from src.extract import GUARD, JD_PROMPT, RESUME_PROMPT
    from src.pipeline import ingest_text
    from src.schemas import JDExtraction, ResumeExtraction

    c = cfg()["llm"]
    res, jds, pairs = _load()
    jobs = []
    for rid in sorted(pairs.resume_id.unique()):
        jobs.append((rid, RESUME_PROMPT.format(guard=GUARD, text=ingest_text(rid, res[rid]["text"])["text"]), ResumeExtraction))
    for jid, jd in jds.items():
        jobs.append((jid, JD_PROMPT.format(guard=GUARD, text=jd["text"].strip()), JDExtraction))
    ok, bad = 0, []
    cache = path("cache") / "llm"
    for doc_id, prompt, schema in jobs:
        f = next(Path(src).rglob(f"out/{doc_id}.json"), None)
        if f is None:
            bad.append((doc_id, "missing"))
            continue
        try:
            obj = schema.model_validate_json(f.read_text())
        except Exception as e:  # noqa: BLE001
            bad.append((doc_id, str(e)[:120]))
            continue
        key = sha(MODEL, c["prompt_version"], schema.__name__, prompt, "", str(c["temperature"]))
        (cache / f"{key}.json").write_text(json.dumps({"model": MODEL, "prompt_version": c["prompt_version"], "salt": "",
                                                        "text": obj.model_dump_json()}))
        ok += 1
    print(f"installed {ok}/{len(jobs)} extractions" + (f"; problems: {bad}" if bad else ""))
    return 0 if not bad else 1


def run():
    import agent
    from baselines import embedding, keyword
    from baselines.tfidf import TfidfScorer

    c = cfg()
    c["llm"]["model"] = MODEL
    c["llm"]["offline"] = True
    d = c["decide"]
    res, jds, pairs = _load()
    lab = pd.read_csv(LAB)
    rows = []
    for _, p in pairs.iterrows():
        jd = jds[p.job_id]
        o = agent.screen(res[p.resume_id]["text"], jd["text"], candidate_id=p.resume_id, private=False)
        rows.append({"job_id": p.job_id, "resume_id": p.resume_id, "resume_pool": p.resume_pool, "score": o["score"],
                     "decision": o["decision"], "reasons": o["reasons"], "years": o["years_experience"],
                     "components": o["components"], "n_skills": len(o["profile"]["skills"]),
                     "extraction_error": o["extraction_error"]})
    lab = lab[["job_id", "resume_id", "relevance", "ideal_decision", "must_haves_met", "must_haves_missing", "notes"]]
    df = pd.DataFrame(rows).merge(lab, on=["job_id", "resume_id"], how="inner")
    assert len(df) == len(pairs), "every pair needs a label"
    # same scores, but CAREER_SWITCH also blocks (the v1.0 policy); per-version results are in results/posthoc.json
    df["decision_career_switch_blocking"] = ["escalate" if set(r) - {"LOCATION_MISMATCH"} else "advance" for r in df.reasons]

    corpus = [j["text"] for j in jds.values()] + [r["text"] for r in res.values()]
    tf = TfidfScorer(corpus)
    df["keyword"] = [keyword.score(jds[j]["text"], res[r]["text"]) for j, r in zip(df.job_id, df.resume_id)]
    df["tfidf"] = [tf.score(jds[j]["text"], res[r]["text"]) for j, r in zip(df.job_id, df.resume_id)]
    df["embedding"] = [embedding.score(jds[j]["text"], res[r]["text"]) for j, r in zip(df.job_id, df.resume_id)]
    df["embedding_chunked"] = [embedding.score_chunked(jds[j]["text"], res[r]["text"]) for j, r in zip(df.job_id, df.resume_id)]

    cm = dict(cost_fn=d["cost_missed_good"], cost_fp=d["cost_advanced_weak"])
    out = {"n_pairs": int(len(df)), "n_jobs": int(df.job_id.nunique()), "n_resumes": int(df.resume_id.nunique()),
           "extraction_model": MODEL, "labeller": "claude-sonnet agents (blind), pending author review",
           "t_high": d["t_high"], "label_distribution": df.relevance.value_counts().sort_index().to_dict(),
           "ideal_advance": int((df.ideal_decision == "advance").sum()),
           "extraction_failures": int(df.extraction_error.notna().sum()), "systems": {}}
    for col in ["score", "keyword", "tfidf", "embedding", "embedding_chunked"]:  # embedding_chunked: post-test variant
        out["systems"][col] = {"ranking": bootstrap(df, lambda x, c=col: ranking_metrics(x, c)),
                               "spearman": round(float(spearmanr(df[col], df.relevance)[0]), 4)}
    out["decision_current"] = decision_metrics(df, "decision", **cm)  # config.yaml system (v1.2)
    out["decision_career_switch_blocking"] = decision_metrics(df, "decision_career_switch_blocking", **cm)
    out["by_pool"] = {pool: {"n": int(len(g)), "mean_score": round(float(g.score.mean()), 3),
                             "mean_label": round(float(g.relevance.mean()), 2),
                             "advanced": int((g.decision == "advance").sum())} for pool, g in df.groupby("resume_pool")}
    out["per_job"] = {jid: {"spearman": round(float(spearmanr(g.score, g.relevance)[0]), 3) if g.relevance.nunique() > 1 else None,
                            "ideal_advance": int((g.ideal_decision == "advance").sum()),
                            "advanced_v1_1": int((g.decision == "advance").sum())} for jid, g in df.groupby("job_id")}
    from collections import Counter
    out["reason_counts"] = dict(Counter(r for rs in df.reasons for r in rs))
    write_json(path("results") / "real_set.json", out)
    df.drop(columns=["components"]).to_csv(path("results") / "real_set_pairs.csv", index=False)
    s = out["systems"]
    for k, v in s.items():
        print(f"{k:10} spearman={v['spearman']:+.3f}  ndcg@5={v['ranking']['ndcg@5']['mean']:.3f} "
              f"[{v['ranking']['ndcg@5']['lo']:.2f},{v['ranking']['ndcg@5']['hi']:.2f}]  p@5={v['ranking']['p@5']['mean']:.2f}")
    for k in ("decision_career_switch_blocking", "decision_current"):
        m = out[k]
        print(k, {x: m[x] for x in ("recall_ideal_advance", "precision_auto_advance", "escalation_rate", "expected_cost")}, m["confusion"])
    print("labels", out["label_distribution"], "ideal advance", out["ideal_advance"], "| by pool", out["by_pool"])
    print("reasons", out["reason_counts"])
    return 0


if __name__ == "__main__":
    cmd = sys.argv[1]
    sys.exit(install(sys.argv[2]) if cmd == "install" else run())
