"""Real-resume sanity set from the brief's primary Kaggle datasets (added after the test evaluation).

Resumes: snehaanbhawal/resume-dataset (data/kaggle/Resume/Resume.csv). Selected by CONTENT, not by Kaggle category:
only 18 of 120 "INFORMATION-TECHNOLOGY" resumes are software developers, while ~85 developer resumes are spread over
other categories. Pool = 30 software-developer resumes (any category) + 15 non-developer IT resumes (hard negatives).
Jobs: arshkon/linkedin-job-postings (data/kaggle/JD/postings.csv), 5 IT-tagged software postings fixed below.
Pairs: 5 jobs x 10 resumes = 50, per job BM25 top-4 + middle-3 + random-3 (seeded), as in the main golden set.

Writes the committed, masked subset to data/processed_real/ (the raw Kaggle CSVs are never committed).
"""
from __future__ import annotations

import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from rank_bm25 import BM25Okapi

from src.config import ROOT, write_json
from src.mask import mask
from src.sanitize import sanitize_text

KAGGLE = ROOT / "data" / "kaggle"
OUT = ROOT / "data" / "processed_real"
SEED = 13
JOBS = {  # archetype -> arshkon job_id (chosen for a stated level and explicit requirements)
    "K01": (3887485935, "backend / Python"),
    "K02": (3886896623, "full-stack"),
    "K03": (3884930756, "data engineering"),
    "K04": (3887101757, "SRE / DevOps"),
    "K05": (3894406051, "junior .NET"),
}
DEV_PHRASE = re.compile(r"\b(?:software (?:developer|engineer)|web developer|java developer|python|javascript|"
                        r"\.net developer|full[- ]stack|programmer)\b")
CODE = re.compile(r"\b(?:java|python|javascript|c\+\+|c#|sql|react|angular|node|django|spring|php|html|css)\b")
TOK = re.compile(r"[a-z0-9+#.]+")


def toks(t: str) -> list[str]:
    return [w.strip(".") for w in TOK.findall(t.lower()) if len(w.strip(".")) > 1]


def clean(text: str) -> str:
    """Sanitise + mask contacts. Names are not masked: the dataset is already anonymised, and the name-line rule
    would wrongly mask all-caps section titles such as 'INFORMATION TECHNOLOGY'."""
    return mask(sanitize_text(text).clean_text, mask_names=False)[0]


def main():
    rng = random.Random(SEED)
    r = pd.read_csv(KAGGLE / "Resume" / "Resume.csv")
    low = r.Resume_str.str.lower()
    is_dev = low.str.contains(DEV_PHRASE) & (low.str.count(CODE) >= 3)
    dev_ids = sorted(r[is_dev].ID.tolist())
    infra_ids = sorted(r[(r.Category == "INFORMATION-TECHNOLOGY") & ~is_dev].ID.tolist())
    pool = sorted(rng.sample(dev_ids, 30)) + sorted(rng.sample(infra_ids, 15))
    sel = r[r.ID.isin(pool)].set_index("ID")
    resumes = {}
    for rid in pool:
        row = sel.loc[rid]
        text = clean(row.Resume_str)
        resumes[f"K{rid}"] = {"id": f"K{rid}", "kaggle_id": int(rid), "kaggle_category": row.Category,
                              "pool": "developer" if rid in dev_ids else "it_non_developer",
                              "text": text, "words": len(text.split())}

    p = pd.read_csv(KAGGLE / "JD" / "postings.csv",
                    usecols=["job_id", "title", "description", "formatted_experience_level", "location",
                             "formatted_work_type", "remote_allowed", "company_name"])
    jds = {}
    for jid, (kid, arche) in JOBS.items():
        row = p[p.job_id == kid].iloc[0]
        body = clean(" ".join(str(row.description).split()))
        remote = "Remote" if row.remote_allowed == 1 else (row.formatted_work_type or "")
        jds[jid] = {"id": jid, "kaggle_job_id": int(kid), "archetype": arche, "title": row.title,
                    "location": row.location, "job_type": "Remote" if row.remote_allowed == 1 else "Onsite",
                    "level": row.formatted_experience_level if isinstance(row.formatted_experience_level, str) else "",
                    "text": f"Title: {row.title}\nLocation: {row.location} ({remote})\n"
                            f"Level: {row.formatted_experience_level}\n\n{body}"}

    rows = []
    ids = sorted(resumes)
    bm = BM25Okapi([toks(resumes[i]["text"]) for i in ids])
    for jid, jd in jds.items():
        sc = bm.get_scores(toks(jd["text"]))
        ranked = [i for _, i in sorted(zip(sc, ids), key=lambda x: (-x[0], x[1]))]
        chosen = {i: "top" for i in ranked[:4]}
        mid = len(ranked) // 2
        for i in ranked[mid - 1: mid + 2]:
            chosen.setdefault(i, "middle")
        rest = [i for i in ranked if i not in chosen]
        for i in rng.sample(rest, 3):
            chosen[i] = "random"
        rows += [{"job_id": jid, "resume_id": i, "bucket": b, "resume_pool": resumes[i]["pool"]} for i, b in chosen.items()]

    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / "resumes.json", resumes)
    write_json(OUT / "jds.json", jds)
    pairs = pd.DataFrame(rows).sort_values(["job_id", "resume_id"])
    pairs.to_csv(OUT / "pairs.csv", index=False)
    print(f"{len(resumes)} resumes ({sum(v['pool'] == 'developer' for v in resumes.values())} developer), "
          f"{len(jds)} jobs, {len(pairs)} pairs; resumes used in pairs: {pairs.resume_id.nunique()}")
    print(pairs.groupby(["job_id", "resume_pool"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
