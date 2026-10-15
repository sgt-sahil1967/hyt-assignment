"""Build the golden-set candidate pools (plan §8, adapted to a 100-resume corpus).

1. Resumes are split once (seeded) into dev (30%) and test (70%) pools: each resume lives in one split.
2. Each JD draws 20 resumes from its split's pool:
   top-6 / middle-6 by BM25 rank, 4 random from the rest, 4 rule-picked hard cases.
   BM25 (not the system under test) seeds the pool, so labels are not anchored on our scorer.
3. Writes golden/pairs.csv and golden/labelling_sheet.md (what the labeller sees: no scores).
"""
from __future__ import annotations

import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from rank_bm25 import BM25Okapi

from src.config import ROOT, cfg, path, read_json

TOK = re.compile(r"[a-z0-9+#.]+")


def toks(t: str) -> list[str]:
    return [w.strip(".") for w in TOK.findall(t.lower()) if len(w.strip(".")) > 1]


def features(text: str) -> dict:
    lines = text.splitlines()
    skills = lines[lines.index("Skills") + 1] if "Skills" in lines else ""
    m = re.search(r"^(.*) at (.*) \((\d{4}) - (\w+)\)", text, re.M)
    return {
        "skills": [s.strip() for s in skills.split(",") if s.strip()],
        "title": m.group(1) if m else "",
        "start": int(m.group(3)) if m else None,
    }


def hard_tags(f: dict) -> list[str]:
    s = {x.lower() for x in f["skills"]}
    tags = []
    if f["title"].startswith("Senior") and f["start"] and f["start"] >= 2022:
        tags.append("title_inflation")
    if f["title"].startswith("Junior") and f["start"] and f["start"] <= 2019:
        tags.append("title_deflation")
    if ("django" in s and "python" not in s) or ("spring boot" in s and "java" not in s):
        tags.append("child_skill_only")
    if "machine learning" in s and not ({"python"} & s):
        tags.append("ml_without_python")
    return tags


def main():
    c = cfg()
    rng = random.Random(c["seed"])
    jds = read_json(path("processed") / "jds.json")
    res = read_json(path("processed") / "resumes.json")
    ids = sorted(res)
    rng.shuffle(ids)
    n_dev = round(len(ids) * c["golden"]["dev_resume_fraction"])
    split_of = {rid: ("dev" if i < n_dev else "test") for i, rid in enumerate(ids)}
    b = c["golden"]["buckets"]

    rows = []
    for jid, jd in jds.items():
        pool = sorted(r for r in res if split_of[r] == jd["split"])
        bm = BM25Okapi([toks(res[r]["text"]) for r in pool])
        scores = bm.get_scores(toks(jd["text"]))
        ranked = [r for _, r in sorted(zip(scores, pool), key=lambda x: (-x[0], x[1]))]
        chosen: dict[str, str] = {}
        for r in ranked[: b["top"]]:
            chosen[r] = "top"
        mid = len(ranked) // 2
        for r in ranked[mid - b["middle"] // 2: mid + (b["middle"] + 1) // 2]:
            chosen.setdefault(r, "middle")
        rest = [r for r in ranked if r not in chosen]
        hard = [r for r in rest if hard_tags(features(res[r]["text"]))]
        rng.shuffle(hard)
        for r in hard[: b["hard"]]:
            chosen[r] = "hard"
        rest = [r for r in ranked if r not in chosen]
        for r in rng.sample(rest, min(b["random"], len(rest))):
            chosen[r] = "random"
        for r, bucket in chosen.items():
            f = features(res[r]["text"])
            rows.append({"job_id": jid, "resume_id": r, "split": jd["split"], "bucket": bucket,
                         "hard_case_tag": ";".join(hard_tags(f))})

    df = pd.DataFrame(rows).sort_values(["job_id", "resume_id"])
    df.to_csv(ROOT / "golden" / "pairs.csv", index=False)
    pd.DataFrame([{"resume_id": r, "split": s} for r, s in sorted(split_of.items())]).to_csv(
        ROOT / "golden" / "resume_splits.csv", index=False)

    # labelling sheet: JD text + compact resume facts, rows shuffled within job, no model output
    out = ["# Labelling sheet (blind: no model scores)\n"]
    for jid, g in df.groupby("job_id"):
        jd = jds[jid]
        out.append(f"\n## {jid} — {jd['title']} ({jd['level']}, {jd['job_type']}, {jd['location']}) [{jd['split']}]\n")
        out.append("```\n" + jd["text"][:3500] + "\n```\n")
        out.append("| resume | title | since | skills |\n|---|---|---|---|")
        for r in g.sample(frac=1, random_state=c["seed"]).resume_id:
            f = features(res[r]["text"])
            out.append(f"| {r} | {f['title']} | {f['start']} | {', '.join(f['skills'])} |")
    (ROOT / "golden" / "labelling_sheet.md").write_text("\n".join(out))
    print(df.groupby(["split", "bucket"]).size(), len(df))


if __name__ == "__main__":
    main()
