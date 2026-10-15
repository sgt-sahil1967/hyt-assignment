"""Ranking / decision / agreement metrics + stratified bootstrap CIs."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

GOOD = 2  # relevance >= 2 counts as a good candidate


def dcg(rels: list[float], k: int) -> float:
    return sum((2 ** r - 1) / math.log2(i + 2) for i, r in enumerate(rels[:k]))


def ndcg_at(rels_in_pred_order: list[float], k: int) -> float:
    ideal = dcg(sorted(rels_in_pred_order, reverse=True), k)
    return dcg(rels_in_pred_order, k) / ideal if ideal > 0 else float("nan")


def precision_at(rels, k):
    return float(np.mean([r >= GOOD for r in rels[:k]]))


def mrr(rels):
    for i, r in enumerate(rels):
        if r >= GOOD:
            return 1 / (i + 1)
    return float("nan")


def order_rels(g: pd.DataFrame, score_col: str) -> list[float]:
    """Relevance in predicted order; ties broken by resume id (deterministic, same rule as the pipeline)."""
    g = g.sort_values([score_col, "resume_id"], ascending=[False, True])
    return list(g.relevance)


def ranking_metrics(df: pd.DataFrame, score_col: str) -> dict:
    per = []
    for jid, g in df.groupby("job_id"):
        r = order_rels(g, score_col)
        per.append({"job_id": jid, "ndcg@5": ndcg_at(r, 5), "ndcg@10": ndcg_at(r, 10), "p@5": precision_at(r, 5), "mrr": mrr(r)})
    per = pd.DataFrame(per)
    return {k: float(np.nanmean(per[k])) for k in ["ndcg@5", "ndcg@10", "p@5", "mrr"]}


def bootstrap(df: pd.DataFrame, fn, n: int = 1000, seed: int = 13) -> dict:
    """Stratified bootstrap: resample candidates within each job, recompute fn (dict of metrics). 95% CI."""
    rng = np.random.default_rng(seed)
    groups = [g for _, g in df.groupby("job_id")]
    point = fn(df)
    samples = {k: [] for k in point}
    for _ in range(n):
        bs = pd.concat([g.iloc[rng.integers(0, len(g), len(g))] for g in groups])
        m = fn(bs)
        for k, v in m.items():
            samples[k].append(v)
    return {k: {"mean": round(point[k], 4), "lo": round(float(np.nanpercentile(samples[k], 2.5)), 4),
                "hi": round(float(np.nanpercentile(samples[k], 97.5)), 4)} for k in point}


def decision_metrics(df: pd.DataFrame, pred_col: str = "decision", cost_fn: float = 5, cost_fp: float = 1) -> dict:
    ideal_adv = df.ideal_decision == "advance"
    pred_adv = df[pred_col] == "advance"
    good = df.relevance >= GOOD
    tp = int((ideal_adv & pred_adv).sum())
    fp = int((~ideal_adv & pred_adv).sum())
    fn = int((ideal_adv & ~pred_adv).sum())
    tn = int((~ideal_adv & ~pred_adv).sum())
    return {
        "confusion": {"ideal_advance&advanced": tp, "ideal_escalate&advanced": fp,
                      "ideal_advance&escalated": fn, "ideal_escalate&escalated": tn},
        "recall_ideal_advance": round(tp / max(tp + fn, 1), 4),
        "precision_auto_advance": round(tp / max(tp + fp, 1), 4) if tp + fp else None,
        "advanced_with_relevance>=2": round(float((pred_adv & good).sum() / max(pred_adv.sum(), 1)), 4) if pred_adv.sum() else None,
        "recall_good_relevance>=2_advanced": round(float((pred_adv & good).sum() / max(good.sum(), 1)), 4),
        "escalation_rate": round(float((~pred_adv).mean()), 4),
        "expected_cost": float(cost_fn * fn + cost_fp * fp),
        "expected_cost_per_pair": round((cost_fn * fn + cost_fp * fp) / len(df), 4),
        "n": int(len(df)),
    }


def weighted_kappa(a, b, labels=None) -> float:
    from sklearn.metrics import cohen_kappa_score

    return float(cohen_kappa_score(a, b, weights="quadratic", labels=labels))
