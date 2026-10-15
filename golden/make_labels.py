"""Writes golden/labels.csv from the labeller's hand-assigned relevance grades below.

Grades and notes are the labeller's judgement, written from labelling_sheet.md with rubric.md before any scorer
existed. This script only does the bookkeeping (must_haves_met list, ideal_decision rule, validation).
It deliberately does not import anything from src/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

G = Path(__file__).resolve().parent
ROOT = G.parent

# job -> resume -> (relevance, note)
LABELS: dict[str, dict[str, tuple[int, str]]] = {
    "JD01": {
        "R065": (3, "Spring Boot (implies Java) + K8s, 5.5y"), "R066": (0, "no Java/Spring"),
        "R023": (1, "Java + Docker but no Spring"), "R024": (0, "no Java"),
        "R056": (1, "Spring Boot but 0.5y for mid-senior"), "R047": (1, "Java, Docker, K8s; no Spring"),
        "R054": (1, "Java, K8s; no Spring"), "R084": (3, "Spring Boot + Docker, 5.5y"),
        "R082": (1, "Java, 0.5y, no Spring; senior title inflated"), "R069": (1, "Java, no Spring"),
        "R033": (3, "Spring Boot + Docker + K8s, 2.5y"), "R088": (3, "Spring Boot + K8s, backend 3.5y"),
        "R061": (1, "Java + Docker, no Spring"), "R039": (2, "Java + Spring Boot, 1.5y; senior title inflated"),
        "R028": (0, "no Java"), "R052": (2, "Java + Spring Boot, 4.5y, no containers"),
        "R096": (2, "Java + Spring Boot, 1.5y"), "R063": (1, "Java + containers, no Spring"),
        "R086": (2, "Java + Spring Boot, 1.5y"), "R091": (0, "no Java"),
    },
    "JD02": {
        "R059": (0, "no Python"), "R060": (0, "no Python; SQL/K8s only"), "R003": (2, "Python/Django + Docker, 2.5y"),
        "R005": (3, "Django + K8s + SQL, 2.5y"), "R032": (0, "no Python"), "R021": (2, "Django + Docker, 3.5y"),
        "R027": (1, "Python but 0.5y"), "R068": (0, "no Python"), "R067": (2, "Django + AWS, 1.5y"),
        "R062": (3, "Django + K8s + Docker, 4.5y"), "R014": (3, "Django + AWS + SQL, 2.5y"),
        "R076": (1, "no Python but SQL/Docker/K8s"), "R037": (2, "Python + Django, no infra"),
        "R016": (3, "Django + Docker + K8s + AWS, 2.5y"), "R006": (2, "Python + Django + Docker, 1.5y"),
        "R022": (1, "Django + AWS but 0.5y"), "R087": (1, "no Python but SQL/Docker/K8s"),
        "R057": (0, "no Python"), "R071": (3, "Python + Django + SQL, senior 5.5y"), "R079": (0, "no Python"),
    },
    "JD03": {
        "R055": (1, "no Node; SQL/Git/JS"), "R072": (0, "no Node, 0.5y"), "R002": (1, "Node + React + SQL + Docker but 0.5y"),
        "R008": (1, "no Node; strong web/devops set"), "R046": (1, "Node + Docker but 0.5y"), "R036": (0, "no Node, 0.5y"),
        "R043": (1, "no Node; Git/JS/React"), "R081": (2, "Node + Docker + JS, 5.5y (<7y)"),
        "R080": (1, "no Node; React/AWS/Docker/Git"), "R075": (1, "Node + Git, 0.5y"),
        "R028": (2, "Node + AWS + Docker + SQL, 5.5y (<7y)"), "R092": (0, "no Node"), "R047": (0, "no Node"),
        "R029": (1, "Node + full stack set but 2.5y vs 7+"), "R012": (1, "Node + React + Docker, 2.5y"),
        "R041": (1, "no Node; Git/JS/React"), "R097": (1, "Node + AWS + React + Git, 3.5y"),
        "R048": (1, "Node + Git, 2.5y"), "R091": (1, "no Node; JS/React/Docker"), "R093": (0, "no Node"),
    },
    "JD04": {
        "R064": (0, "no AWS/Spring/containers"), "R065": (1, "Spring + Python + K8s; no AWS"),
        "R009": (0, "containers + Python, no AWS/Spring"), "R011": (1, "Spring + AWS only"), "R043": (0, "K8s only"),
        "R030": (0, "Python + K8s, no AWS/Spring"), "R035": (1, "AWS + Python + Docker; no Spring"),
        "R084": (2, "AWS + Spring + Python + Docker; no IaC/CI"), "R081": (0, "Python + containers, no AWS/Spring"),
        "R072": (1, "AWS + containers + Python, 0.5y"), "R028": (1, "AWS + Docker + Python; no Spring"),
        "R088": (1, "Spring + Python + K8s; no AWS"), "R052": (1, "Spring + AWS + Python; no containers"),
        "R029": (1, "AWS + Docker"), "R023": (0, "Python + Docker only"), "R033": (0, "Spring + containers, no AWS"),
        "R097": (1, "Spring + AWS"), "R053": (0, "Python + containers, no AWS"), "R086": (0, "Spring + Python only"),
        "R095": (1, "Spring + K8s + Python; no AWS"),
    },
    "JD05": {
        "R044": (0, "no ML"), "R048": (1, "ML, 2.5y, no SQL"), "R008": (0, "no ML/SQL"),
        "R009": (1, "no ML but SQL + Docker + K8s, 5.5y"), "R034": (0, "no ML/SQL"), "R026": (0, "ML but 0.5y, no SQL"),
        "R033": (1, "ML, 2.5y, no SQL"), "R064": (2, "ML + SQL, 5.5y; no C#"), "R061": (1, "ML, 5.5y, no SQL"),
        "R050": (1, "ML + SQL but 0.5y"), "R023": (0, "no ML/SQL"), "R081": (0, "no ML/SQL"),
        "R036": (1, "ML + SQL but 0.5y"), "R024": (2, "ML + SQL, 2.5y; no C#"), "R010": (0, "no ML/SQL"),
        "R028": (0, "SQL only"), "R091": (1, "ML, 2.5y, no SQL"), "R041": (0, "no ML"),
        "R078": (0, "ML but 1.5y, no SQL"), "R082": (0, "ML but 0.5y, no SQL"),
    },
    "JD06": {
        "R055": (3, "Python + Git + SQL/JS"), "R064": (0, "no Python/Git"), "R002": (2, "Python + SQL, no Git"),
        "R011": (0, "no Python/Git"), "R047": (2, "Django, no Git; 4.5y"), "R041": (3, "Python + Git + JS"),
        "R046": (0, "no Python/Git"), "R093": (2, "Django, no Git; 5.5y overqualified"),
        "R082": (3, "Python + Git + JS, 0.5y"), "R066": (3, "Python + Git + SQL/JS"),
        "R019": (2, "Python + Django, no Git"), "R096": (3, "Python + Git + SQL"), "R051": (0, "no Python/Git"),
        "R034": (1, "Git + web skills, no Python"), "R017": (2, "Python + SQL, no Git; 5.5y overqualified"),
        "R044": (2, "Python + Django + SQL, no Git"), "R100": (2, "Python + Django, no Git"),
        "R054": (0, "no Python/Git"), "R094": (3, "Python + Git + SQL"), "R099": (1, "Git + SQL, no Python"),
    },
    "JD07": {
        "R032": (1, "JS + Node; no TS/React"), "R059": (0, "JS only"), "R003": (0, "no front-end"),
        "R005": (1, "React"), "R025": (0, "no front-end"), "R020": (1, "React + Node"),
        "R022": (1, "React + Node + AWS"), "R071": (1, "React + JS"), "R068": (0, "Node only"),
        "R067": (0, "no front-end"), "R007": (0, "JS only"), "R085": (0, "JS only"), "R027": (1, "React + JS"),
        "R014": (0, "no front-end"), "R006": (0, "Node only"), "R021": (1, "JS + Node"), "R090": (0, "Node only"),
        "R031": (1, "React + JS"), "R079": (1, "JS + Node + AWS"), "R087": (0, "JS only"),
    },
    "JD08": {
        "R059": (0, "no C++"), "R062": (1, "C++, 4.5y; no SQL/AWS"), "R001": (2, "C++ + SQL + AWS, 5.5y; no Boost/Linux"),
        "R005": (1, "C++ + SQL, 2.5y"), "R031": (0, "no C++"), "R021": (0, "no C++"), "R027": (1, "C++, 0.5y"),
        "R071": (0, "no C++"), "R070": (0, "no C++"), "R067": (1, "C++ + AWS, 1.5y"), "R014": (1, "C++ + AWS + SQL, 2.5y"),
        "R079": (0, "no C++"), "R032": (1, "C++ + SQL + AWS, 2.5y"), "R015": (1, "C++, 2.5y"), "R007": (0, "no C++"),
        "R022": (0, "no C++"), "R087": (0, "no C++"), "R037": (1, "C++, 2.5y"), "R076": (1, "C++ + SQL + containers, 4.5y; no cloud"),
        "R085": (0, "no C++"),
    },
    "JD09": {
        "R054": (0, "Node only"), "R066": (1, "Python + AWS"), "R004": (1, "Python + React"), "R008": (1, "React + AWS"),
        "R043": (0, "React only"), "R029": (1, "Node + React + AWS, 2.5y"), "R041": (1, "Python + React"),
        "R080": (1, "Python + React + AWS, 1.5y"), "R078": (1, "Python + Node + React + AWS but 1.5y for senior"),
        "R075": (0, "Node only"), "R019": (2, "Python + Node + AWS, 4.5y; no Vue"), "R084": (1, "Python + AWS"),
        "R050": (1, "Python + React"), "R026": (0, "React only"), "R010": (1, "Node + React + AWS, 1.5y"),
        "R035": (1, "Python + AWS"), "R099": (1, "Node + AWS"), "R053": (0, "Python only"), "R082": (1, "Python + React"),
        "R098": (0, "Python only"),
    },
    "JD10": {
        "R054": (1, "no SQL"), "R061": (1, "no SQL"), "R002": (2, "SQL + Python, 0.5y"), "R004": (1, "no SQL"),
        "R045": (1, "no SQL"), "R039": (2, "SQL + Java, 1.5y"), "R042": (1, "no SQL"), "R093": (1, "no SQL"),
        "R080": (1, "no SQL"), "R064": (3, "SQL + Java, 5.5y"), "R023": (1, "no SQL"), "R095": (1, "no SQL"),
        "R049": (2, "SQL + Java, 0.5y"), "R028": (3, "SQL + C++/Python, 5.5y"), "R017": (3, "SQL + Python, 5.5y"),
        "R040": (1, "no SQL"), "R100": (1, "no SQL"), "R050": (2, "SQL + Python, 0.5y"), "R094": (3, "SQL + Python, 2.5y"),
        "R096": (2, "SQL + Java/Python, 1.5y"),
    },
}

# labeller conventions (rubric.md): child skill satisfies parent
IMPLIES = {"spring boot": ["spring", "java"], "django": ["python"], "react": ["javascript"], "node.js": ["javascript"]}
ALIASES = {"rest apis": "rest api", "machine learning": "machine learning"}
START_YOE = {2018: 5.5, 2019: 4.5, 2020: 3.5, 2021: 2.5, 2022: 1.5, 2023: 0.5}


def resume_facts(text: str):
    lines = text.splitlines()
    skills = {ALIASES.get(s.strip().lower(), s.strip().lower()) for s in lines[lines.index("Skills") + 1].split(",")}
    skills.add("rest api")  # "Built REST APIs" bullet on every resume
    for s in list(skills):
        skills.update(IMPLIES.get(s, []))
    import re
    m = re.search(r"\((\d{4}) - ", text)
    return skills, START_YOE[int(m.group(1))]


def main():
    pairs = pd.read_csv(G / "pairs.csv")
    jd_gold = json.loads((G / "jd_gold.json").read_text())
    res = json.loads((ROOT / "data/processed/resumes.json").read_text())
    rows = []
    for _, p in pairs.iterrows():
        rel, note = LABELS[p.job_id][p.resume_id]
        jd = jd_gold[p.job_id]
        skills, yoe = resume_facts(res[p.resume_id]["text"])
        met, missing = [], []
        for m in jd["must_have"]:
            if m["type"] == "degree":
                ok = True  # every resume: BSc Computer Science
            else:
                ok = bool({m["name"], *m.get("alternatives", [])} & skills)
            (met if ok else missing).append(m["name"])
        if jd["min_years"] and yoe < jd["min_years"]:
            missing.append(f"{jd['min_years']}+ years")
        overq = jd["seniority"] == "junior" and yoe > 5
        decision = "advance" if rel >= 2 and not missing and not overq else "escalate"
        rows.append({"job_id": p.job_id, "resume_id": p.resume_id, "relevance": rel, "ideal_decision": decision,
                     "must_haves_met": ";".join(met), "must_haves_missing": ";".join(missing),
                     "hard_case_tag": p.hard_case_tag if isinstance(p.hard_case_tag, str) else "",
                     "bucket": p.bucket, "notes": note, "split": p.split})
    df = pd.DataFrame(rows)
    # validation
    assert len(df) == len(pairs) == sum(len(v) for v in LABELS.values()), "label/pair count mismatch"
    assert df.notna().all().all()
    sp = pd.read_csv(G / "resume_splits.csv").set_index("resume_id").split
    assert (df.resume_id.map(sp) == df.split).all(), "resume split leakage"
    assert df.groupby("resume_id").split.nunique().max() == 1
    df.to_csv(G / "labels.csv", index=False)
    print(df.groupby("split").relevance.value_counts().unstack(fill_value=0))
    print(df.groupby(["job_id"]).ideal_decision.value_counts().unstack(fill_value=0))


if __name__ == "__main__":
    sys.exit(main())
