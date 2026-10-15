# Labelling rubric

Labels in `labels.csv` were written by the labeller (Claude, at the user's request) from `labelling_sheet.md`.
That sheet shows only the JD text and the resume's title, start year and skills, with **no model scores**.
All 200 labels were written **before** `score.py` / `decide.py` existed. The scoring *formula* was already
fixed in the implementation plan, so the labeller was not blind to the design. REPORT §10 discusses this.

## What is judged
Only skills, experience and role type. Name, university, address/location and email are ignored. The JD05
requirement "Russell Group/Red Brick university" is ignored as a prestige proxy (see REPORT §7).

## Evidence conventions for this corpus
The 100 resumes are templated. Each lists 6 skills and one role ("X at Company (YYYY - Present)"), and the
same three bullets appear on every resume. Usage evidence therefore can't be told apart from a listing, so:

* A listed skill counts as **met (listed)**. REST APIs count as met for everyone ("Built REST APIs" bullet).
* **Child skills satisfy parents** (a recruiter would accept this): Spring Boot ⇒ Spring, Java; Django ⇒ Python;
  React, Node.js ⇒ JavaScript. A parent never satisfies a child (Java does not imply Spring Boot).
* Years of experience = as-of 2024-01-15 (JD posting era) minus start year mid-point:
  2018→5.5, 2019→4.5, 2020→3.5, 2021→2.5, 2022→1.5, 2023→0.5.
* Requirements nobody in the corpus could show (CI/CD, IaC, TypeScript, Boost, Linux, Vue, C#…) still count as
  **missing**. JDs whose must-haves nobody meets have **no "advance" labels**.

## Relevance (0–3)
| grade | meaning |
|---|---|
| 3 strong | all core must-haves met, experience suits the level, plus relevant nice-to-haves |
| 2 good | core must-haves met but thin elsewhere (few nice-to-haves / short experience), **or** best available profile when an unmeetable must-have caps the job |
| 1 weak | partial: a core must-have is missing but there is a real overlap with the stack |
| 0 no fit | the primary technology is missing and there is little overlap |

When unsure between two grades, choose the lower one.

## Ideal decision
`advance` iff relevance ≥ 2 **and** no must-have is missing **and** the candidate is not clearly overqualified for a
junior role (> 5 years). Otherwise `escalate`. The system never rejects.

## Per-JD application notes (core must-haves in **bold**)
* **JD01 Java/Spring Boot**: **Java, Spring Boot**; nice REST, Docker, Kubernetes, CI. 3 = core + container skill + ≥2.5y.
* **JD02 Python**: **Python**; nice AWS, SQL, Docker, Kubernetes. 3 = Python + ≥2 nice + ≥2.5y (or senior Python).
  Without Python: 1 if ≥3 infra nice-to-haves, else 0.
* **JD03 Senior full-stack Node**: **Node.js, SQL, Git, Docker, CI/CD, 7+ years**. Nobody reaches 7y or has CI/CD,
  so max 2. 2 = Node + ≥2 of (SQL, Git, Docker, AWS, React) + ≥4.5y. No Node: 1 if ≥3 web skills and ≥1.5y.
* **JD04 SRE**: **AWS, Spring, scripting (Python/Bash), containers, IaC, CI/CD**. Nobody has IaC or CI/CD, so max 2.
  All four available ⇒ 2; three ⇒ 1; two including AWS ⇒ 1; otherwise 0.
* **JD05 AI developer**: **Machine Learning, C#, SQL, degree, 2+ years**. Nobody has C#, so max 2. 2 = ML + SQL + ≥2y;
  1 = ML with SQL or ≥2y, or SQL + ≥2y + ≥2 nice; else 0.
* **JD06 Junior Python**: **Python, Git, degree (or equivalent)**. 3 = Python + Git + a nice-to-have; Python without
  Git = 2 (escalate: missing must-have); no Python: 1 if Git + web skills.
* **JD07 Front-end**: **TypeScript, prototyping tools, JS, Node, React, Redux, CSS, animation library, AWS**.
  Core front-end must-haves are absent from the corpus, so max 1. 1 = React, or JS + Node.
* **JD08 Senior C++**: **C++, Boost, REST, Linux, cloud, networking, SQL + NoSQL**. Boost and Linux are absent, so max 2.
  2 = C++ + SQL + AWS + ≥3.5y; 1 = any C++; 0 = no C++.
* **JD09 Senior SWE**: **Python, Vue.js, Node.js, React, AWS, CS degree**. Vue is absent, so max 2. Count of the other
  four: 4 or 3 (with ≥2.5y / ≥3.5y) ⇒ 2; 2–3 ⇒ 1; ≤1 ⇒ 0.
* **JD10 Vague SWE**: **SQL, any programming language, degree or equivalent**. 3 = SQL + ≥2.5y; 2 = SQL with less
  experience; 1 = developer without SQL.
