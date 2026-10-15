"""Phase 0: build processed, masked inputs from the local data folder.

- JDs: rows chosen in config.yaml from data/jd/postings2.csv
- Resumes: data/resume/*.docx -> sanitise (hidden runs, unicode) -> PII mask -> dedup -> language check
Writes data/processed/{jds.json, resumes.json, manifest.json}. Raw files are never copied.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from langdetect import DetectorFactory, detect
from rapidfuzz import fuzz

from src.config import ROOT, cfg, path, sha, write_json
from src.mask import mask
from src.sanitize import sanitize_docx, sanitize_text

DetectorFactory.seed = 0
NEAR_DUP = 97  # token_sort_ratio on masked text; templated resumes share ~80% boilerplate


def resume_id(p: Path) -> str:
    n = int(re.search(r"(\d+)\.docx$", p.name).group(1))
    return f"R{n:03d}"


def prepare_resumes(mask_names: bool | None = None) -> dict:
    c = cfg()
    mask_names = c["mask"]["names"] if mask_names is None else mask_names
    files = sorted((ROOT / c["paths"]["resumes_dir"]).glob("*.docx"), key=resume_id)
    out, seen, dups = {}, {}, []
    for f in files:
        rid = resume_id(f)
        s = sanitize_docx(f)
        masked, counts = mask(s.clean_text, mask_names=mask_names)
        h = sha(re.sub(r"\s+", " ", masked.lower()))
        if h in seen:
            dups.append({"id": rid, "duplicate_of": seen[h], "kind": "exact"})
            continue
        near = next((o for o, r in out.items() if fuzz.token_sort_ratio(r["text"], masked) >= NEAR_DUP
                     and r["text"] != masked and _same_content(r["text"], masked)), None)
        if near:
            dups.append({"id": rid, "duplicate_of": near, "kind": "near"})
            continue
        seen[h] = rid
        try:
            lang = detect(masked)
        except Exception:
            lang = "unknown"
        out[rid] = {
            "id": rid,
            "source": f.name,
            "text": masked,
            "text_hash": h,
            "words": len(masked.split()),
            "language": lang,
            "flags": s.flags,
            "injection_matches": s.injection_matches,
            "mask_counts": counts,
        }
    return {"resumes": out, "duplicates": dups}


def _same_content(a: str, b: str) -> bool:
    """Near-dup only if skills + experience lines match (boilerplate alone is not duplication)."""
    def core(t):
        return [ln for ln in t.splitlines() if " at " in ln or "," in ln]
    return core(a) == core(b)


def prepare_jds() -> dict:
    c = cfg()
    df = pd.read_csv(ROOT / c["paths"]["jd_csv"])
    jds = {}
    for jid, spec in c["jobs"].items():
        r = df.loc[spec["row"]]
        body = str(r.job_summary)
        # postings sometimes carry recruiter contacts: mask them too (same masker, no name masking)
        body, _ = mask(body, mask_names=False)
        s = sanitize_text(body)
        jds[jid] = {
            "id": jid,
            "row": int(spec["row"]),
            "split": spec["split"],
            "title": str(r.job_title),
            "location": str(r.job_location),
            "job_type": str(r.job_type),
            "level": str(r["job level"]),
            "text": f"Title: {r.job_title}\nLocation: {r.job_location} ({r.job_type})\nLevel: {r['job level']}\n\n{s.clean_text}",
            "listed_skills": [x.strip() for x in str(r.job_skills).strip("[]").replace("'", "").split(",") if x.strip()],
        }
    return jds


def main():
    p = path("processed")
    c = cfg()
    raw_ok = (ROOT / c["paths"]["resumes_dir"]).exists() and (ROOT / c["paths"]["jd_csv"]).exists()
    if not raw_ok:
        if (p / "resumes.json").exists() and (p / "jds.json").exists():
            print("raw data/ not present: using the committed masked data in data/processed/ (no PII)")
            return
        raise SystemExit("raw data missing and no data/processed/*.json: see README > Data")
    jds = prepare_jds()
    res = prepare_resumes()
    write_json(p / "jds.json", jds)
    write_json(p / "resumes.json", res["resumes"])
    manifest = {
        "n_jds": len(jds),
        "n_resume_files": len(res["resumes"]) + len(res["duplicates"]),
        "n_resumes": len(res["resumes"]),
        "duplicates": res["duplicates"],
        "non_english": [r["id"] for r in res["resumes"].values() if r["language"] != "en"],
        "hidden_text": [r["id"] for r in res["resumes"].values() if r["flags"]["hidden_text_removed"]],
        "injection": [r["id"] for r in res["resumes"].values() if r["flags"]["injection_suspected"]],
        "mask_totals": {k: sum(r["mask_counts"].get(k, 0) for r in res["resumes"].values())
                        for k in ["[NAME]", "[EMAIL]", "[PHONE]", "[ADDRESS]", "[URL]", "[DOB]"]},
    }
    write_json(path("results") / "data_manifest.json", manifest)
    print(manifest)


if __name__ == "__main__":
    main()
