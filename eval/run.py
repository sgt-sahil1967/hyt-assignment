"""Evaluation harness (plan §9). Stages (each caches its output in results/):

    python -m eval.run golden       # pipeline on all 200 golden pairs (+ explanations)
    python -m eval.run tune         # T_high on DEV only (cost matrix) -> results/thresholds.json (frozen)
    python -m eval.run metrics      # test-split ranking / decision / explanation / bias metrics, bootstrap CIs
    python -m eval.run baselines    # keyword, TF-IDF, embedding, LLM zero-shot on identical pairs
    python -m eval.run extraction   # extraction P/R/F1 vs gold, YOE MAE, JD must/nice F1, schema-valid rate
    python -m eval.run robustness   # run-to-run variance (fresh extractions, salted cache keys)
    python -m eval.run ablations    # post-hoc diagnostics: oracle JD requirements, CAREER_SWITCH non-blocking
    python -m eval.run all
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

from src import embed
from src.config import ROOT, cfg, path, read_json, write_json
from src.decide import decide
from src.experience import compute_yoe
from src.llm import STATS
from src.normalize import canon
from src.pipeline import (WORKERS, extract_many, jd_extraction, load, resume_extraction, row_to_sr,
                          screen_resumes)

from .metrics import GOOD, bootstrap, decision_metrics, ranking_metrics

R = path("results")


def labels() -> pd.DataFrame:
    return pd.read_csv(ROOT / "golden" / "labels.csv")


# ------------------------------------------------------------------ golden predictions
def run_golden(explain: bool = True) -> pd.DataFrame:
    jds, res = load()
    lab = labels()
    rows = []
    for jid, g in lab.groupby("job_id"):
        pool = {k: res[k] for k in g.resume_id}
        rows += screen_resumes(jid, jds[jid], pool, with_explanations=explain)
        print(f"  {jid}: {len(pool)} pairs", flush=True)
    write_json(R / "golden_predictions.json", rows)
    embed.save()
    return pd.DataFrame(rows)


def preds() -> pd.DataFrame:
    p = pd.DataFrame(read_json(R / "golden_predictions.json"))
    return p.merge(labels(), on=["job_id", "resume_id"], how="inner")


def redecide(df: pd.DataFrame, params: dict | None = None, full: bool = False):
    """Re-apply the decision policy (current config + overrides) to stored score results."""
    jds_x = {jid: jd_extraction(jd) for jid, jd in load()[0].items()}
    ds = [decide(row_to_sr(r), jds_x[r["job_id"]], r["flags"], params) for r in df.to_dict("records")]
    return ds if full else [d.decision for d in ds]


def with_current_policy(df: pd.DataFrame) -> pd.DataFrame:
    ds = redecide(df, full=True)
    return df.assign(decision=[d.decision for d in ds], reasons=[d.reasons for d in ds], queue=[d.queue for d in ds])


# ------------------------------------------------------------------ threshold tuning (dev only)
def tune():
    d = cfg()["decide"]
    df = preds()
    dev = df[df.split == "dev"].reset_index(drop=True)
    grid = np.round(np.arange(0.20, 0.801, 0.01), 2)
    curve = []
    for t in grid:
        dec = redecide(dev, {"t_high": float(t)})
        m = decision_metrics(dev.assign(decision=dec), cost_fn=d["cost_missed_good"], cost_fp=d["cost_advanced_weak"])
        curve.append({"t_high": float(t), "expected_cost": m["expected_cost"], "escalation_rate": m["escalation_rate"],
                      "recall_ideal_advance": m["recall_ideal_advance"]})
    cdf = pd.DataFrame(curve)
    best_cost = cdf.expected_cost.min()
    # among cost-optimal thresholds take the highest (most conservative auto-advance)
    t_best = float(cdf[cdf.expected_cost == best_cost].t_high.max())
    write_json(R / "thresholds.json", {"t_high": t_best})
    write_json(R / "threshold_curve_dev.json", curve)
    _plot_curve(cdf, t_best)
    print(f"T_high tuned on dev = {t_best} (expected cost {best_cost}); frozen in results/thresholds.json")
    cfg.cache_clear()


def _plot_curve(cdf, t):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.plot(cdf.t_high, cdf.expected_cost, label="expected cost (dev)")
    ax2 = ax.twinx()
    ax2.plot(cdf.t_high, cdf.escalation_rate, color="tab:orange", label="escalation rate")
    ax.axvline(t, ls="--", color="grey")
    ax.set_xlabel("T_high"); ax.set_ylabel("cost (FN=5, FP=1)"); ax2.set_ylabel("escalation rate")
    fig.legend(loc="upper center", ncol=2, fontsize=8)
    fig.tight_layout(); fig.savefig(R / "threshold_curve_dev.png", dpi=130); plt.close(fig)


# ------------------------------------------------------------------ test metrics
def metrics():
    d = cfg()["decide"]
    df = with_current_policy(preds())  # stored decisions predate tuning: re-decide with frozen thresholds
    out = {"t_high": d["t_high"], "n_pairs": {s: int((df.split == s).sum()) for s in ("dev", "test")}}
    for split in ("test", "dev"):
        s = df[df.split == split].reset_index(drop=True)
        out[split] = {
            "ranking": bootstrap(s, lambda x: ranking_metrics(x, "score")),
            "spearman_score_vs_relevance": round(float(spearmanr(s.score, s.relevance)[0]), 4),
            "decision": decision_metrics(s, cost_fn=d["cost_missed_good"], cost_fp=d["cost_advanced_weak"]),
            "per_job": {jid: {**ranking_metrics(g, "score"), "spearman": round(float(spearmanr(g.score, g.relevance)[0]), 3)
                              if g.relevance.nunique() > 1 else None}
                        for jid, g in s.groupby("job_id")},
            "reason_counts": dict(Counter(r for rs in s.reasons for r in rs)),
            "queue_counts": dict(Counter(s.queue)),
        }
        if "explanation" in s:
            ex = s.explanation.dropna()
            nq = sum(e["n_quotes"] for e in ex)
            nb = sum(e["n_ungrounded"] for e in ex)
            out[split]["explanation_groundedness"] = {
                "explanations": int(len(ex)), "quotes": int(nq), "ungrounded_quotes": int(nb),
                "groundedness_rate": round(1 - nb / nq, 4) if nq else None,
                "explanations_with_any_ungrounded": int(sum(e["n_ungrounded"] > 0 for e in ex))}
    # bias check: score vs resume length
    res = load()[1]
    t = df[df.split == "test"]
    words = t.resume_id.map(lambda r: res[r]["words"])
    out["bias_length"] = {"pearson_score_vs_words": round(float(pearsonr(t.score, words)[0]), 4),
                          "words_range": [int(words.min()), int(words.max())],
                          "note": "masked corpus resumes span only a few words, so this check has almost no power here"}
    # hard-case slice
    hc = t[t.hard_case_tag.fillna("") != ""]
    out["hard_cases_test"] = {tag: {"n": int(len(g)), "mean_abs_rank_err": None,
                                    "decision_accuracy": round(float((g.decision == g.ideal_decision).mean()), 3)}
                              for tag, g in hc.assign(tag=hc.hard_case_tag.str.split(";")).explode("tag").groupby("tag")}
    write_json(R / "metrics.json", out)
    print(json.dumps({k: out["test"][k] for k in ("ranking", "decision", "spearman_score_vs_relevance")}, indent=1))
    return out


# ------------------------------------------------------------------ baselines
def baselines():
    from baselines import embedding, keyword, llm_zeroshot
    from baselines.tfidf import TfidfScorer

    jds, res = load()
    df = with_current_policy(preds())
    tf = TfidfScorer([j["text"] for j in jds.values()] + [r["text"] for r in res.values()])
    pairs = list(zip(df.job_id, df.resume_id))
    df["keyword"] = [keyword.score(jds[j]["text"], res[r]["text"]) for j, r in pairs]
    df["tfidf"] = [tf.score(jds[j]["text"], res[r]["text"]) for j, r in pairs]
    df["embedding"] = [embedding.score(jds[j]["text"], res[r]["text"]) for j, r in pairs]
    # post-test variant (DECISIONS #15d): whole-document embedding via overlapping chunks; the row above is the evaluated one
    df["embedding_chunked"] = [embedding.score_chunked(jds[j]["text"], res[r]["text"]) for j, r in pairs]
    with ThreadPoolExecutor(WORKERS) as ex:
        z = list(ex.map(lambda p: llm_zeroshot.score(jds[p[0]]["text"], res[p[1]]["text"]), pairs))
    n_missing = sum(s is None for s, _ in z)
    df["llm_zeroshot"] = [s for s, _ in z]
    df["llm_zeroshot_decision"] = [d if d in ("advance", "escalate") else "escalate" for _, d in z]
    embed.save()
    cols = ["score", "keyword", "tfidf", "embedding", "embedding_chunked"] + (["llm_zeroshot"] if n_missing == 0 else [])
    if n_missing:
        print(f"  llm_zeroshot: {n_missing}/{len(z)} pairs unavailable (quota/offline) -> excluded from this run")

    d = cfg()["decide"]
    out = {}
    dev, test = df[df.split == "dev"], df[df.split == "test"]
    for col in cols:
        # baselines have no policy: advance iff score >= threshold tuned on dev with the same cost matrix
        if col == "score":
            dm = decision_metrics(test, "decision", d["cost_missed_good"], d["cost_advanced_weak"])
            t_best = d["t_high"]
        else:
            best = None
            for t in np.unique(np.round(dev[col], 4)):
                m = decision_metrics(dev.assign(_d=np.where(dev[col] >= t, "advance", "escalate")), "_d",
                                     d["cost_missed_good"], d["cost_advanced_weak"])
                if best is None or m["expected_cost"] < best[0] or (m["expected_cost"] == best[0] and t > best[1]):
                    best = (m["expected_cost"], float(t))
            t_best = best[1]
            dm = decision_metrics(test.assign(_d=np.where(test[col] >= t_best, "advance", "escalate")), "_d",
                                  d["cost_missed_good"], d["cost_advanced_weak"])
        out[col] = {"ranking": bootstrap(test, lambda x, c=col: ranking_metrics(x, c)),
                    "spearman": round(float(spearmanr(test[col], test.relevance)[0]), 4),
                    "threshold_dev": t_best, "decision": dm}
    if n_missing:
        out["llm_zeroshot"] = {"status": f"unavailable for {n_missing}/{len(z)} pairs (API quota)"}
    else:
        out["llm_zeroshot_own_decision"] = decision_metrics(test, "llm_zeroshot_decision", d["cost_missed_good"], d["cost_advanced_weak"])
    write_json(R / "baselines.json", out)
    df[["job_id", "resume_id", "split", "relevance", "score", "keyword", "tfidf", "embedding", "embedding_chunked", "llm_zeroshot",
        "llm_zeroshot_decision"]].to_csv(R / "baseline_scores.csv", index=False)
    for k, v in out.items():
        if "ranking" in v:
            print(f"{k:13} ndcg@5={v['ranking']['ndcg@5']['mean']:.3f} [{v['ranking']['ndcg@5']['lo']:.3f},"
                  f"{v['ranking']['ndcg@5']['hi']:.3f}]  spearman={v['spearman']:.3f}  cost={v['decision']['expected_cost']}"
                  f"  esc={v['decision']['escalation_rate']}")


# ------------------------------------------------------------------ post-hoc ablations (diagnostic, NOT headline)
def ablations():
    """Isolate error sources on the test split. These were added after seeing test errors, so they are diagnostics,
    never used to pick the system that the headline numbers describe."""
    from src.score import score_pair

    d = cfg()["decide"]
    jds, res = load()
    gold = read_json(ROOT / "golden" / "jd_gold.json")
    base = with_current_policy(preds())
    test = base[base.split == "test"].reset_index(drop=True)
    xs = extract_many({r: res[r] for r in test.resume_id.unique()})
    jx = {jid: jd_extraction(jds[jid]) for jid in test.job_id.unique()}
    out = {"frozen_system": {"ranking": ranking_metrics(test, "score"),
                             "decision": decision_metrics(test, cost_fn=d["cost_missed_good"], cost_fp=d["cost_advanced_weak"])}}

    # 1) oracle JD requirements: hand-annotated must/nice instead of the LLM's (extraction vs scoring errors)
    rows = []
    for r in test.to_dict("records"):
        g = gold[r["job_id"]]
        jd_o = {**jx[r["job_id"]], **{k: g[k] for k in ("must_have", "nice_to_have", "min_years", "seniority",
                                                        "equivalent_experience_allowed")}}
        for q in jd_o["must_have"] + jd_o["nice_to_have"]:
            q.setdefault("alternatives", [])
        x = xs[r["resume_id"]][0]
        sr = score_pair(r["job_id"], r["resume_id"], jd_o, x)
        dec = decide(sr, jd_o, r["flags"])
        rows.append({"score_oracle": sr.score, "decision_oracle": dec.decision, "reasons_oracle": dec.reasons})
    o = pd.concat([test, pd.DataFrame(rows)], axis=1)
    out["oracle_jd_requirements"] = {"ranking": ranking_metrics(o, "score_oracle"),
                                     "decision": decision_metrics(o, "decision_oracle", d["cost_missed_good"], d["cost_advanced_weak"])}
    # 2) CAREER_SWITCH as information only (its threshold was never tuned on dev)
    nc = with_current_policy(test.assign()).copy()
    ds = redecide(test, {"career_switch_relevance": -1.0}, full=True)
    nc["decision"] = [x.decision for x in ds]
    out["career_switch_non_blocking"] = {"decision": decision_metrics(nc, cost_fn=d["cost_missed_good"], cost_fp=d["cost_advanced_weak"])}
    # 3) both
    ds = [decide(score_pair(r["job_id"], r["resume_id"], {**jx[r["job_id"]], **{k: gold[r["job_id"]][k] for k in
            ("must_have", "nice_to_have", "min_years", "seniority", "equivalent_experience_allowed")}}, xs[r["resume_id"]][0]),
                 {**jx[r["job_id"]], **gold[r["job_id"]]}, r["flags"], {"career_switch_relevance": -1.0}).decision
          for r in test.to_dict("records")]
    out["oracle_jd_and_career_switch_non_blocking"] = {"decision": decision_metrics(test.assign(decision=ds), cost_fn=d["cost_missed_good"], cost_fp=d["cost_advanced_weak"])}
    write_json(R / "ablations.json", out)
    for k, v in out.items():
        print(k, {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.get("ranking", {}).items()},
              {kk: v["decision"][kk] for kk in ("recall_ideal_advance", "precision_auto_advance", "escalation_rate", "expected_cost")})


# ------------------------------------------------------------------ extraction accuracy
def extraction():
    jds, res = load()
    gold = [json.loads(line) for line in open(ROOT / "golden" / "extraction_gold.jsonl")]
    rg = [g for g in gold if g["kind"] == "resume"]
    jg = {g["id"]: g for g in gold if g["kind"] == "jd"}

    # schema-valid rate over every document
    xs = extract_many(res)
    jx = {jid: jd_extraction(jd) for jid, jd in jds.items()}
    attempts = Counter(m.get("attempts") for _, m in xs.values())
    # API/quota failures (no response at all) are not schema failures: report them separately
    unavailable = [k for k, (x, m) in xs.items() if x is None and m.get("error") and not m["error"].startswith("schema")]
    n_docs = len(xs) + len(jx) - len(unavailable)
    valid = sum(x is not None for x, _ in xs.values()) + sum(x is not None for x in jx.values())

    tp = fp = fn = 0
    yoe_err, edu_ok = [], []
    rg = [g for g in rg if xs[g["id"]][0] is not None]
    for g in rg:
        x, _ = xs[g["id"]]
        pred = {canon(s["name"]) for s in x["skills"]}
        gs = {canon(s) for s in g["skills"]}
        tp += len(pred & gs); fp += len(pred - gs); fn += len(gs - pred)
        yoe_err.append(abs(compute_yoe(x["roles"])["yoe"] - compute_yoe(g["roles"])["yoe"]))
        edu_ok.append(bool(x["education"]) and x["education"][0]["degree_level"] == g["education"][0]["degree_level"])
    p, r = tp / max(tp + fp, 1), tp / max(tp + fn, 1)

    def req_set(reqs):
        return {frozenset({canon(q["name"])} | {canon(a) for a in q.get("alternatives", []) or []})
                for q in reqs if q["type"] in ("skill", "degree")}

    def overlap_f1(pred, gold_):
        # a predicted requirement matches a gold one if their option sets intersect (one-to-one greedy)
        gold_left, m = list(gold_), 0
        for pr in pred:
            for i, gr in enumerate(gold_left):
                if pr & gr:
                    m += 1; gold_left.pop(i); break
        pp = m / len(pred) if pred else 1.0
        rr = m / len(gold_) if gold_ else 1.0
        return pp, rr, (2 * pp * rr / (pp + rr) if pp + rr else 0.0)

    jd_rows = {}
    for jid, g in jg.items():
        x = jx[jid]
        must = overlap_f1(req_set(x["must_have"]), req_set(g["must_have"]))
        nice = overlap_f1(req_set(x["nice_to_have"]), req_set(g["nice_to_have"]))
        jd_rows[jid] = {"must_p": round(must[0], 3), "must_r": round(must[1], 3), "must_f1": round(must[2], 3),
                        "nice_f1": round(nice[2], 3), "min_years_ok": x["min_years"] == g["min_years"],
                        "seniority_pred": x["seniority"], "seniority_gold": g["seniority"]}
    out = {
        "schema_valid_rate": round(valid / n_docs, 4),
        "documents_evaluated": n_docs,
        "documents_unavailable_api": unavailable,
        "extraction_attempts_histogram": {str(k): v for k, v in attempts.items()},
        "resume_skill": {"precision": round(p, 4), "recall": round(r, 4), "f1": round(2 * p * r / (p + r), 4),
                         "n_resumes": len(rg)},
        "yoe_mae_years": round(float(np.mean(yoe_err)), 4),
        "education_level_accuracy": round(float(np.mean(edu_ok)), 4),
        "jd": jd_rows,
        "jd_must_f1_macro": round(float(np.mean([v["must_f1"] for v in jd_rows.values()])), 4),
        "jd_nice_f1_macro": round(float(np.mean([v["nice_f1"] for v in jd_rows.values()])), 4),
    }
    from src.normalize import FALLBACK_LOG
    out["embedding_fallback_matches"] = FALLBACK_LOG
    write_json(R / "extraction_metrics.json", out)
    print(json.dumps({k: v for k, v in out.items() if k != "jd"}, indent=1))


# ------------------------------------------------------------------ robustness: run-to-run variance
def robustness(runs: int = 3):
    jds, res = load()
    lab = labels()
    t = lab[lab.split == "test"]
    rows = []
    for k in range(runs):
        salt = f"run{k}"
        for jid, g in t.groupby("job_id"):
            jd_x = jd_extraction(jds[jid], salt=salt)  # JD re-extracted too: requirement drift is part of the noise
            pool = {r: res[r] for r in g.resume_id}
            out = screen_resumes(jid, jds[jid], pool, salt=salt, jd_x=jd_x)
            rows += [{"run": k, "job_id": jid, "resume_id": o["resume_id"], "score": o["score"], "decision": o["decision"]} for o in out]
        print(f"  run {k} done", flush=True)
    df = pd.DataFrame(rows)
    piv = df.pivot_table(index=["job_id", "resume_id"], columns="run", values="score")
    dpiv = df.pivot_table(index=["job_id", "resume_id"], columns="run", values="decision", aggfunc="first")
    flips = (dpiv.nunique(axis=1) > 1).mean()
    rank_corr = []
    for jid, g in piv.groupby(level=0):
        for a in range(runs):
            for b in range(a + 1, runs):
                rank_corr.append(spearmanr(g[a], g[b])[0])
    out = {"runs": runs, "pairs": int(len(piv)),
           "score_std_mean": round(float(piv.std(axis=1).mean()), 4), "score_std_max": round(float(piv.std(axis=1).max()), 4),
           "score_range_max": round(float((piv.max(axis=1) - piv.min(axis=1)).max()), 4),
           "decision_flip_rate": round(float(flips), 4),
           "within_job_rank_spearman_mean": round(float(np.nanmean(rank_corr)), 4)}
    write_json(R / "robustness.json", out)
    df.to_csv(R / "robustness_runs.csv", index=False)
    print(out)
    return out


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    stages = {"golden": run_golden, "tune": tune, "metrics": metrics, "baselines": baselines,
              "extraction": extraction, "robustness": robustness, "ablations": ablations,
              "tune_career_switch": tune_career_switch, "v1_1": v1_1}
    todo = [s for s in stages if s not in ("tune_career_switch", "v1_1")] if stage == "all" else [stage]
    for s in todo:
        print(f"== {s}", flush=True)
        stages[s]()
    print("LLM stats:", {k: v for k, v in STATS.items() if k != "error_samples"}, STATS["error_samples"][:3])



# ------------------------------------------------------------------ CAREER_SWITCH tuning (dev only)
def tune_career_switch():
    """Grid over career_switch_relevance on DEV. Rule fixed before looking: min expected cost; ties -> keep the
    current value if it is in the tie set, else the closest value to it. Test is touched once, afterwards."""
    d = cfg()["decide"]
    current = d["career_switch_relevance"]
    df = preds()
    dev = df[df.split == "dev"].reset_index(drop=True)
    grid = [-1.0] + [round(x, 2) for x in np.arange(0.0, 0.601, 0.05)]
    curve = []
    for t in grid:
        dec = redecide(dev, {"career_switch_relevance": t})
        m = decision_metrics(dev.assign(decision=dec), cost_fn=d["cost_missed_good"], cost_fp=d["cost_advanced_weak"])
        fired = sum("CAREER_SWITCH" in x.reasons for x in redecide(dev, {"career_switch_relevance": t}, full=True))
        curve.append({"threshold": t, "expected_cost": m["expected_cost"], "recall_ideal_advance": m["recall_ideal_advance"],
                      "escalation_rate": m["escalation_rate"], "fired_on_dev": fired})
    cdf = pd.DataFrame(curve)
    best = cdf.expected_cost.min()
    ties = cdf[cdf.expected_cost == best].threshold.tolist()
    chosen = current if current in ties else min(ties, key=lambda t: abs(t - current))
    test = df[df.split == "test"].reset_index(drop=True)
    impact = {}
    for name, t in (("before", current), ("chosen", chosen)):
        dec = redecide(test, {"career_switch_relevance": t})
        impact[name] = decision_metrics(test.assign(decision=dec), cost_fn=d["cost_missed_good"], cost_fp=d["cost_advanced_weak"])
    out = {"rule": "min dev expected cost; ties keep the current value (else closest)", "current": current,
           "dev_curve": curve, "dev_min_cost": best, "tied_thresholds": ties, "chosen": chosen,
           "changed": chosen != current,
           "test_impact": {k: {kk: v[kk] for kk in ("recall_ideal_advance", "precision_auto_advance", "escalation_rate",
                                                    "expected_cost")} for k, v in impact.items()}}
    write_json(R / "career_switch_tuning.json", out)
    print(cdf.to_string(index=False))
    print({k: v for k, v in out.items() if k != "dev_curve"})
    return out



# ------------------------------------------------------------------ post-hoc v1.1 with per-change attribution
def v1_1():
    """Frozen v1.0 vs post-hoc changes, added one at a time, on both splits (scores re-run from cached extractions):
      A  v1.0 frozen           (results/v1_0_frozen)
      B  + framework taxonomy  (DECISIONS #15a; changes scores)
      C  + CAREER_SWITCH info  (DECISIONS #15b; changes decisions only) = v1.1
    """
    from .posthoc import OFF, flags

    d = cfg()["decide"]
    jds, res = load()
    lab = labels()
    rows = []
    with flags(OFF):  # v1.1 = before the v1.2 fixes (see eval/posthoc.py for v1.2)
        for jid, g in lab.groupby("job_id"):
            rows += screen_resumes(jid, jds[jid], {k: res[k] for k in g.resume_id})
    cur = pd.DataFrame(rows).merge(lab, on=["job_id", "resume_id"])
    frozen = pd.DataFrame(read_json(R / "v1_0_frozen" / "golden_predictions.json")).merge(lab, on=["job_id", "resume_id"])
    frozen = frozen.assign(decision=redecide(frozen, {"career_switch_blocking": True, "t_high": d["t_high"]}))
    variants = {
        "A_v1_0_frozen": frozen,
        "B_plus_framework_taxonomy": cur.assign(decision=redecide(cur, {"career_switch_blocking": True, "overqualified_junior_only": False})),
        "C_v1_1_plus_career_switch_informational": cur.assign(decision=redecide(cur, {"career_switch_blocking": False, "overqualified_junior_only": False})),
    }
    out = {"note": "post-hoc changes made after test evaluation; v1.0 remains the headline", "t_high": d["t_high"]}
    for name, df in variants.items():
        out[name] = {}
        for split in ("test", "dev"):
            s = df[df.split == split].reset_index(drop=True)
            out[name][split] = {
                "ranking": bootstrap(s, lambda x: ranking_metrics(x, "score")) if split == "test" else ranking_metrics(s, "score"),
                "spearman": round(float(spearmanr(s.score, s.relevance)[0]), 4),
                "decision": decision_metrics(s, cost_fn=d["cost_missed_good"], cost_fp=d["cost_advanced_weak"]),
            }
    a, c = variants["A_v1_0_frozen"], variants["C_v1_1_plus_career_switch_informational"]
    m = a[["job_id", "resume_id", "decision", "split", "ideal_decision"]].merge(
        c[["job_id", "resume_id", "decision"]], on=["job_id", "resume_id"], suffixes=("_v10", "_v11"))
    flips = m[m.decision_v10 != m.decision_v11]
    out["decision_flips_v1_0_to_v1_1"] = flips.to_dict("records")
    write_json(R / "v1_1.json", out)
    for name in variants:
        t = out[name]["test"]
        print(f"{name:42} spearman={t['spearman']:.4f} ndcg@10={t['ranking']['ndcg@10']['mean']:.4f} "
              f"recall={t['decision']['recall_ideal_advance']:.4f} precision={t['decision']['precision_auto_advance']} "
              f"esc={t['decision']['escalation_rate']:.4f} cost={t['decision']['expected_cost']} | dev cost={out[name]['dev']['decision']['expected_cost']}")
    print("flips:", [(f["job_id"], f["resume_id"], f["decision_v10"], "->", f["decision_v11"], "ideal", f["ideal_decision"]) for f in out["decision_flips_v1_0_to_v1_1"]])
    return out


if __name__ == "__main__":
    main()
