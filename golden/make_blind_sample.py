"""Build the blind labelling sample for the author: 60 (job, resume) pairs, 6 per job, none of the 40 pairs the author
already reviewed (golden/human_review.csv), and no scores, AI labels, buckets or hard-case tags anywhere in the output.

    .venv/bin/python golden/make_blind_sample.py      # -> golden/blind_sample.md, blind_sample_responses.txt, blind_sample_pairs.csv

Buckets from pairs.csv (BM25 top / middle / random / rule-picked hard) only decide which pairs are sampled: 2 top,
1 middle, 1 random, 2 hard per job (topped up from the rest if a bucket runs short). Jobs and resumes are shuffled
(seed 13), so stopping after any number of jobs still leaves a fair sample.
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED, PER_JOB = 13, 6
QUOTA = {"top": 2, "middle": 1, "random": 1, "hard": 2}


def main() -> None:
    rng = random.Random(SEED)
    seen = {(r["job_id"], r["resume_id"]) for r in csv.DictReader(open(ROOT / "golden" / "human_review.csv"))}
    pairs = [r for r in csv.DictReader(open(ROOT / "golden" / "pairs.csv")) if (r["job_id"], r["resume_id"]) not in seen]
    jds = json.loads((ROOT / "data" / "processed" / "jds.json").read_text())
    res = json.loads((ROOT / "data" / "processed" / "resumes.json").read_text())

    picked: dict[str, list[str]] = {}
    for jid in sorted({p["job_id"] for p in pairs}):
        pool = [p for p in pairs if p["job_id"] == jid]
        rng.shuffle(pool)
        chosen: list[dict] = []
        for bucket, n in QUOTA.items():
            chosen += [p for p in pool if p["bucket"] == bucket and p not in chosen][:n]
        chosen += [p for p in pool if p not in chosen][: PER_JOB - len(chosen)]
        ids = [p["resume_id"] for p in chosen]
        rng.shuffle(ids)
        picked[jid] = ids
    order = list(picked)
    rng.shuffle(order)

    md = ["# Blind labelling sample (60 pairs)\n",
          "You are the labeller. Nothing here shows a system score, an AI label or a hint about the pair. "
          "Judge each resume against its job description with your own reading.\n",
          "**Relevance (0-3)**: 3 = strong fit, 2 = good fit, 1 = weak or partial fit, 0 = no fit. "
          "When unsure between two grades, pick the lower one.\n",
          "**Decision**: `advance` if you would put this candidate on the recruiter's shortlist, `escalate` if a human "
          "should look first. Wrongly passing over a good candidate is worse than shortlisting a weak one, so "
          "escalate means *look at this*, never *reject*.\n",
          "Judge skills, experience and role only. Ignore name, university and address. Use your own view of implied "
          "skills (for example, whether machine learning implies Python) and say so in the note when it decides the grade.\n",
          "**Where to write:** copy `blind_sample_responses.txt` into a notepad and fill in one line per pair "
          "(`JD02/R014: relevance=2 decision=advance note=...`). The jobs are in random order, so if you run out of "
          "time, stop after any job and send what you have.\n", "---\n"]
    rows, tpl = [], []
    for jid in order:
        j = jds[jid]
        md += [f"## {jid}: {j['title']}\n", f"*{j.get('location', '')} · {j.get('job_type', '')} · {j.get('level', '')}*\n",
               "```", j["text"].strip(), "```\n"]
        for rid in picked[jid]:
            md += [f"### {jid} / {rid}\n", "```", res[rid]["text"].strip(), "```\n"]
            rows.append((jid, rid))
            tpl.append(f"{jid}/{rid}: relevance=_ decision=_ note=")
        md.append("---\n")
    (ROOT / "golden" / "blind_sample.md").write_text("\n".join(md))
    (ROOT / "golden" / "blind_sample_responses.txt").write_text("\n".join(tpl) + "\n")
    with open(ROOT / "golden" / "blind_sample_pairs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["job_id", "resume_id"])
        w.writerows(rows)
    print(f"{len(rows)} pairs, {len(picked)} jobs, order {order}")


if __name__ == "__main__":
    main()
