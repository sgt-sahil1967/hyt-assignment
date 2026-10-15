"""Post-test changes measured one at a time (v1.1 and v1.2), on every evaluation set. Headline stays v1.0.

    python -m eval.posthoc        # -> results/posthoc.json  (offline, from cache)

Variants (each row = previous row + one change, except D*, which are C + exactly one v1.2 fix):
  A  v1.0 frozen (archive)
  B  + framework categories in the skill map                         DECISIONS #15a
  C  + CAREER_SWITCH informational                         = v1.1    DECISIONS #15b
  D1 C + injection fit-phrase only when asserted about the candidate        (v1.2 fix 3)
  D2 C + OVERQUALIFIED only for junior roles                                (v1.2 fix 2)
  D3 C + slash requirements ("unix/linux") accept either part               (v1.2 fix 4)
  D4 C + example lists ("A, B, C, etc.") collapsed into one any-of requirement (v1.2 fix 1)
  E  C + all four                                          = v1.2
"""
from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("HYT_OFFLINE", "1")

from src.config import cfg, path, read_json, write_json  # noqa: E402

from .metrics import decision_metrics, ranking_metrics  # noqa: E402

FIXES = {"strict_fit_phrase": ("sanitize", "strict_fit_phrase"),
         "overqualified_junior_only": ("decide", "overqualified_junior_only"),
         "split_slash_requirements": ("score", "split_slash_requirements"),
         "consolidate_example_lists": ("score", "consolidate_example_lists")}
OFF = {k: False for k in FIXES}
VARIANTS = {
    "B_plus_framework_taxonomy": {"career_switch_blocking": True, **OFF},
    "C_v1_1": {"career_switch_blocking": False, **OFF},
    "D1_fit_phrase": {"career_switch_blocking": False, **OFF, "strict_fit_phrase": True},
    "D2_overqualified_junior_only": {"career_switch_blocking": False, **OFF, "overqualified_junior_only": True},
    "D3_slash_requirements": {"career_switch_blocking": False, **OFF, "split_slash_requirements": True},
    "D4_example_lists": {"career_switch_blocking": False, **OFF, "consolidate_example_lists": True},
    "E_v1_2": {"career_switch_blocking": False, **{k: True for k in FIXES}},
}


@contextmanager
def flags(v: dict):
    c = cfg()
    saved = {}
    for k, val in v.items():
        sec, key = FIXES.get(k, ("decide", k))
        saved[(sec, key)] = c[sec].get(key)
        c[sec][key] = val
    try:
        yield
    finally:
        for (sec, key), val in saved.items():
            c[sec][key] = val


def golden() -> pd.DataFrame:
    from src.pipeline import load, screen_resumes

    jds, res = load()
    lab = pd.read_csv(ROOT / "golden" / "labels.csv")
    rows = []
    for jid, g in lab.groupby("job_id"):
        rows += screen_resumes(jid, jds[jid], {k: res[k] for k in g.resume_id})
    return pd.DataFrame(rows).merge(lab, on=["job_id", "resume_id"])


def real() -> pd.DataFrame:
    import agent

    from .real_set import DATA, LAB, MODEL

    c = cfg()["llm"]
    prev = c["model"]
    c["model"] = MODEL
    try:
        res = json.loads((DATA / "resumes.json").read_text())
        jds = json.loads((DATA / "jds.json").read_text())
        pairs = pd.read_csv(DATA / "pairs.csv")
        rows = []
        for _, p in pairs.iterrows():
            o = agent.screen(res[p.resume_id]["text"], jds[p.job_id]["text"], candidate_id=p.resume_id, private=False)
            rows.append({"job_id": p.job_id, "resume_id": p.resume_id, "score": o["score"], "decision": o["decision"],
                         "reasons": o["reasons"]})
    finally:
        c["model"] = prev
    lab = pd.read_csv(LAB)[["job_id", "resume_id", "relevance", "ideal_decision"]]
    return pd.DataFrame(rows).merge(lab, on=["job_id", "resume_id"])


def adversarial() -> dict:
    from . import adversarial as adv

    adv.main()
    a = read_json(path("results") / "adversarial.json")
    return {"detection": a["overall_detection_rate"], "auto_advance": a["overall_auto_advance_rate"],
            "fake_skills_auto_advance": a["per_attack"]["fake_skills_in_list"]["auto_advance_rate"]}


def summarise(df: pd.DataFrame) -> dict:
    d = cfg()["decide"]
    m = decision_metrics(df, cost_fn=d["cost_missed_good"], cost_fp=d["cost_advanced_weak"])
    from collections import Counter
    return {"spearman": round(float(spearmanr(df.score, df.relevance)[0]), 4),
            "ndcg@10": round(ranking_metrics(df, "score")["ndcg@10"], 4),
            **{k: m[k] for k in ("recall_ideal_advance", "precision_auto_advance", "escalation_rate", "expected_cost")},
            "advanced": int((df.decision == "advance").sum()),
            "wrong_advances": m["confusion"]["ideal_escalate&advanced"],
            "reason_counts": dict(Counter(r for rs in df.reasons for r in rs))}


def main():
    out = {"note": "post-test changes, measured one at a time; the headline stays the frozen v1.0",
           "A_v1_0_frozen": {"golden_test": read_json(path("results") / "v1_0_frozen" / "metrics.json")["test"]["decision"]}}
    flips = {}
    for name, v in VARIANTS.items():
        with flags(v):
            g = golden()
            r = real()
            out[name] = {"golden_test": summarise(g[g.split == "test"]), "golden_dev": summarise(g[g.split == "dev"]),
                         "real_set": summarise(r), "adversarial": adversarial()}
            flips[name] = {"golden": g.set_index(["job_id", "resume_id"]).decision, "real": r.set_index(["job_id", "resume_id"]).decision}
        t, rr = out[name]["golden_test"], out[name]["real_set"]
        print(f"{name:30} TEST spearman={t['spearman']:.3f} recall={t['recall_ideal_advance']:.2f} prec={t['precision_auto_advance']} "
              f"esc={t['escalation_rate']:.2f} wrong={t['wrong_advances']} | DEV cost={out[name]['golden_dev']['expected_cost']} "
              f"| REAL spearman={rr['spearman']:.3f} adv={rr['advanced']} wrong={rr['wrong_advances']} esc={rr['escalation_rate']:.2f} "
              f"| ADV det={out[name]['adversarial']['detection']:.2f} auto={out[name]['adversarial']['auto_advance']:.2f}")
    for split in ("golden", "real"):
        a, b = flips["C_v1_1"][split].sort_index(), flips["E_v1_2"][split].sort_index()
        b = b.reindex(a.index)
        ch = a[a != b]
        out[f"decision_changes_v1_1_to_v1_2_{split}"] = [{"pair": "/".join(k), "from": a[k], "to": b[k]} for k in ch.index]
    write_json(path("results") / "posthoc.json", out)
    print("changes v1.1->v1.2:", {k: v for k, v in out.items() if k.startswith("decision_changes")})
    # leave results/adversarial.json describing the current system (all v1.2 flags on, as in config.yaml)
    from . import adversarial as adv
    adv.main()


if __name__ == "__main__":
    main()
