"""Compare the author's hand labels on the blind sample with the AI-drafted golden labels.

    python -m eval.review_labels --parse golden/blind_sample_responses_author.txt   # -> golden/human_labels.csv
    python -m eval.review_labels                                                    # -> results/human_label_agreement.json,
                                                                                    #    golden/label_disagreements.csv

The 60 pairs (golden/blind_sample.md) were shown with no scores, AI labels or hints. `golden/labels.csv` is NOT changed:
the frozen headline is measured against it. This script reports how far the author's labels agree with it, and how the
system's numbers on those 60 pairs move if the author's labels are used instead (a sensitivity check, not a new headline).
"""
from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HYT_OFFLINE", "1")

LINE = re.compile(r"^(JD\d+)/(R\d+):\s*relevance=(\d)\s+decision=(advance|escalate)\s+note=(.*)$")


def parse(path: str) -> None:
    rows = []
    for n, ln in enumerate(Path(path).read_text().splitlines(), 1):
        if not ln.strip():
            continue
        m = LINE.match(ln.strip())
        if not m:
            raise SystemExit(f"line {n} does not match 'JD01/R023: relevance=2 decision=advance note=...': {ln[:80]}")
        rows.append(m.groups())
    expected = {tuple(r.values()) for r in csv.DictReader(open(ROOT / "golden" / "blind_sample_pairs.csv"))}
    got = {(r[0], r[1]) for r in rows}
    if got != expected or len(rows) != len(expected):
        raise SystemExit(f"pairs differ from the blind sample: missing {sorted(expected - got)[:5]}, extra {sorted(got - expected)[:5]}")
    with open(ROOT / "golden" / "human_labels.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["job_id", "resume_id", "relevance", "ideal_decision", "note"])
        w.writerows(rows)
    print(f"parsed {len(rows)} labels -> golden/human_labels.csv")


def dump(which: str) -> None:
    """Child mode: print {pair: [score, decision]} for the frozen or current predictions under the active profile."""
    import pandas as pd

    from eval.run import redecide
    from src.config import read_json

    src = ROOT / "results" / ("v1_0_frozen" if which == "frozen" else ".") / "golden_predictions.json"
    df = pd.DataFrame(read_json(src))
    out = {f"{r.job_id}/{r.resume_id}": [r.score, d] for r, d in zip(df.itertuples(), redecide(df))}
    print(json.dumps(out))


def system(which: str) -> dict:
    env = {**os.environ, "HYT_OFFLINE": "1", "PYTHONPATH": str(ROOT)}
    if which == "frozen":
        env["HYT_PROFILE"] = "v1.0"
    else:
        env.pop("HYT_PROFILE", None)
    r = subprocess.run([sys.executable, "-m", "eval.review_labels", "--dump", which], capture_output=True, text=True, env=env, cwd=ROOT)
    if r.returncode:
        raise SystemExit(r.stderr[-1500:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def main() -> None:
    import numpy as np
    from scipy.stats import spearmanr
    from sklearn.metrics import cohen_kappa_score

    human = {(r["job_id"], r["resume_id"]): r for r in csv.DictReader(open(ROOT / "golden" / "human_labels.csv"))}
    ai = {(r["job_id"], r["resume_id"]): r for r in csv.DictReader(open(ROOT / "golden" / "labels.csv"))}
    keys = sorted(human)
    h_rel = np.array([int(human[k]["relevance"]) for k in keys]); a_rel = np.array([int(ai[k]["relevance"]) for k in keys])
    h_dec = np.array([human[k]["ideal_decision"] for k in keys]); a_dec = np.array([ai[k]["ideal_decision"] for k in keys])

    out: dict = {"n_pairs": len(keys), "note": "author's blind hand labels vs the AI-drafted golden labels; labels.csv is unchanged",
                 "relevance": {
                     "exact_agreement": round(float((h_rel == a_rel).mean()), 3),
                     "within_one": round(float((abs(h_rel - a_rel) <= 1).mean()), 3),
                     "weighted_kappa_quadratic": round(float(cohen_kappa_score(h_rel, a_rel, weights="quadratic")), 3),
                     "spearman": round(float(spearmanr(h_rel, a_rel)[0]), 3),
                     "author_higher": int((h_rel > a_rel).sum()), "author_lower": int((h_rel < a_rel).sum()),
                     "mean_author_minus_ai": round(float((h_rel - a_rel).mean()), 3),
                     "author_distribution": {str(g): int((h_rel == g).sum()) for g in range(4)},
                     "ai_distribution": {str(g): int((a_rel == g).sum()) for g in range(4)}},
                 "decision": {
                     "agreement": round(float((h_dec == a_dec).mean()), 3),
                     "kappa": round(float(cohen_kappa_score(h_dec, a_dec)), 3),
                     "author_advance": int((h_dec == "advance").sum()), "ai_advance": int((a_dec == "advance").sum()),
                     "both_advance": int(((h_dec == "advance") & (a_dec == "advance")).sum()),
                     "author_only_advance": int(((h_dec == "advance") & (a_dec == "escalate")).sum()),
                     "ai_only_advance": int(((h_dec == "escalate") & (a_dec == "advance")).sum())},
                 "per_job_exact_relevance_agreement": {j: round(float((h_rel[[k[0] == j for k in keys]] == a_rel[[k[0] == j for k in keys]]).mean()), 2)
                                                       for j in sorted({k[0] for k in keys})}}

    def score_system(sysd: dict, lab_rel, lab_dec) -> dict:
        sc = np.array([sysd[f"{k[0]}/{k[1]}"][0] for k in keys]); dc = np.array([sysd[f"{k[0]}/{k[1]}"][1] for k in keys])
        adv, ideal = dc == "advance", lab_dec == "advance"
        tp = int((adv & ideal).sum())
        return {"spearman": round(float(spearmanr(sc, lab_rel)[0]), 3), "system_advanced": int(adv.sum()), "ideal_advance": int(ideal.sum()),
                "true_advances": tp, "precision": round(tp / adv.sum(), 3) if adv.sum() else None,
                "recall": round(tp / ideal.sum(), 3) if ideal.sum() else None}

    out["system_on_these_pairs"] = {}
    for which, name in (("frozen", "v1_0_headline"), ("current", "current_v1_3")):
        sd = system(which)
        out["system_on_these_pairs"][name] = {"against_ai_labels": score_system(sd, a_rel, a_dec),
                                              "against_author_labels": score_system(sd, h_rel, h_dec)}
    (ROOT / "results" / "human_label_agreement.json").write_text(json.dumps(out, indent=2))

    with open(ROOT / "golden" / "label_disagreements.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["job_id", "resume_id", "author_relevance", "ai_relevance", "author_decision", "ai_decision", "author_note", "ai_note"])
        for k in keys:
            if human[k]["relevance"] != ai[k]["relevance"] or human[k]["ideal_decision"] != ai[k]["ideal_decision"]:
                w.writerow([*k, human[k]["relevance"], ai[k]["relevance"], human[k]["ideal_decision"], ai[k]["ideal_decision"],
                            human[k]["note"], ai[k]["notes"]])
    print(json.dumps({k: v for k, v in out.items() if k != "per_job_exact_relevance_agreement"}, indent=1))


if __name__ == "__main__":
    if "--parse" in sys.argv:
        parse(sys.argv[sys.argv.index("--parse") + 1])
    elif "--dump" in sys.argv:
        dump(sys.argv[sys.argv.index("--dump") + 1])
    else:
        main()
