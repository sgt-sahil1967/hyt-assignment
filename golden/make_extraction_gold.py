"""Extraction gold: 40 resumes (seeded sample) + all 10 JDs.

Resumes follow one rigid template, so the gold fields for them are transcribed from the visible text by a
template parser and spot-checked by hand (no LLM involved). JD gold is the hand annotation in jd_gold.json.
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

G = Path(__file__).resolve().parent
ROOT = G.parent


def parse(text: str) -> dict:
    lines = text.splitlines()
    skills = [s.strip() for s in lines[lines.index("Skills") + 1].split(",")]
    m = re.search(r"^(.*) at (.*) \((\d{4}) - (\w+)\)", text, re.M)
    e = re.search(r"^(BSc|MSc|BA|BEng|PhD)\s+(.*?)\s+–\s+.*\((\d{4})\)", text, re.M)
    return {
        "skills": skills,
        "roles": [{"title": m.group(1), "start": m.group(3), "end": m.group(4), "is_internship": False}],
        "education": [{"degree_level": "bachelor", "field": e.group(2), "year": int(e.group(3))}],
    }


def main():
    res = json.loads((ROOT / "data/processed/resumes.json").read_text())
    ids = sorted(res)
    random.Random(7).shuffle(ids)
    with open(G / "extraction_gold.jsonl", "w") as f:
        for rid in sorted(ids[:40]):
            f.write(json.dumps({"kind": "resume", "id": rid, **parse(res[rid]["text"])}) + "\n")
        for jid, g in json.loads((G / "jd_gold.json").read_text()).items():
            f.write(json.dumps({"kind": "jd", "id": jid, **g}) + "\n")
    print("wrote", G / "extraction_gold.jsonl")


if __name__ == "__main__":
    main()
