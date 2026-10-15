"""Check that `make reproduce-v1.0` regenerated the frozen headline numbers.

Compares results/v1_0_reproduced/ against results/v1_0_frozen/ on every headline figure in REPORT §4–§5 and §8.
Point estimates must match exactly; bootstrap CI bounds may differ by ≤ 0.01 (resampling order). Exit code 1 on mismatch.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
F, R = ROOT / "results" / "v1_0_frozen", ROOT / "results" / "v1_0_reproduced"


def get(d, path):
    for p in path.split("."):
        d = d[p]
    return d


CHECKS = [  # (file, json path, exact?)
    ("thresholds.json", "t_high", True),
    ("metrics.json", "test.spearman_score_vs_relevance", True),
    *[("metrics.json", f"test.ranking.{m}.mean", True) for m in ("ndcg@5", "ndcg@10", "p@5", "mrr")],
    *[("metrics.json", f"test.ranking.{m}.{b}", False) for m in ("ndcg@5", "ndcg@10") for b in ("lo", "hi")],
    *[("metrics.json", f"test.decision.{k}", True) for k in
      ("recall_ideal_advance", "precision_auto_advance", "escalation_rate", "expected_cost")],
    ("metrics.json", "test.explanation_groundedness.groundedness_rate", True),
    ("metrics.json", "test.explanation_groundedness.quotes", True),
    *[("baselines.json", f"{s}.spearman", True) for s in ("keyword", "tfidf", "embedding", "llm_zeroshot")],
    *[("baselines.json", f"{s}.ranking.ndcg@5.mean", True) for s in ("keyword", "tfidf", "embedding", "llm_zeroshot")],
    *[("ablations.json", f"{v}.decision.recall_ideal_advance", True) for v in
      ("frozen_system", "oracle_jd_requirements", "career_switch_non_blocking", "oracle_jd_and_career_switch_non_blocking")],
    ("adversarial.json", "overall_detection_rate", True),
    ("adversarial.json", "overall_auto_advance_rate", True),
]


def main() -> int:
    bad = 0
    print(f"{'figure':58} {'frozen':>9} {'reproduced':>11}  ok")
    for f, p, exact in CHECKS:
        a, b = get(json.loads((F / f).read_text()), p), get(json.loads((R / f).read_text()), p)
        ok = (a == b) if exact or not isinstance(a, (int, float)) else abs(a - b) <= 0.01
        bad += not ok
        print(f"{f.split('.')[0] + ':' + p:58} {a!s:>9} {b!s:>11}  {'✓' if ok else '✗'}")
    print(f"\n{len(CHECKS) - bad}/{len(CHECKS)} headline figures reproduced" + ("" if not bad else "  <-- MISMATCH"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
