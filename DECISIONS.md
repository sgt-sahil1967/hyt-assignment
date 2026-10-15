# Decision log

Non-obvious decisions, with the alternative considered and why it lost. Numbers refer to `results/`.

### 1. No auto-reject: advance or escalate only
The agent sends the strongest candidates to a recruiter and everything else to a human queue, with a reason code.
`LOW_FIT` only lowers queue priority. A wrongly rejected candidate is invisible and unrecoverable; a wrong escalation
costs a few minutes of recruiter time.

### 2. The LLM reads, code judges
Gemini only (a) turns documents into schema-validated JSON and (b) writes the explanation prose. Years of
experience, coverage, score, threshold and decision are deterministic Python. This makes every number traceable to a
line of code and a quote, makes the decision immune to persuasion in the resume, and lets the evaluation separate
extraction errors from scoring errors (see #17).

### 3. Experience computed from dates, not by the LLM
Date strings are copied verbatim by the LLM and parsed in `experience.py`: interval union, "Present" = a pinned
as-of date, year-only dates = 1 July, internships ×0.5, and unparseable/future dates give low confidence and escalate.
LLMs are poor at date arithmetic and inconsistent across runs.

### 4. "Present" = 2024-01-15, not today
The JDs were posted in Dec 2023–Jan 2024. Measured from today (Oct 2026), every candidate would have ≥ 3.3 years and
the junior/senior distinction in the corpus would disappear. The date is pinned in `config.yaml`, so results do not drift.

### 5. Evidence-strength weighting, with "used" verified by code
used = 1.0, listed = 0.5, learning = 0.25. The LLM's "used" claim is downgraded unless the skill appears in a role or
project bullet, and a skill named in a bullet is upgraded even if the LLM missed it. In this corpus almost everything
is "listed" (identical bullets on every resume), so this weighting barely separates candidates here. It still halves
the gain from keyword stuffing (see `results/adversarial.json`).

### 6. Multiplicative cap for a missing must-have (plan said "cap at 0.6")
`fit *= 0.6` instead of `fit = min(fit, 0.6)`. With a hard ceiling, every candidate missing a must-have would tie at
0.6, and the ranking within a job would collapse. This matters because 6 of the 10 JDs have a must-have nobody in the
pool meets. The multiplicative form still guarantees ≤ 0.6 and keeps the order.

### 7. Title technologies weigh ×2 inside must-have coverage
The technology in the job title ("Software Engineer (C++)", "Java Software Engineer") is the core of the role.
Without this, "C++" counted as much as "REST API", which every resume has. The rule is set a priori, not fitted:
on dev it changed only JD08 (Spearman 0.11 → 0.28 before the plural bug fix, 0.48 after).

### 8. Implied minimum years from seniority when the JD gives none
mid = 2y, senior = 4y. This feeds `experience_fit` only and never raises `MISSING_MUST_HAVE` (that needs an explicit
minimum). Without it, a 0.5-year "Senior" title scored identically to a 5.5-year one on senior JDs.

### 9. Cost-matrix threshold tuned on dev only, then frozen
`T_high` minimises expected cost (missed good = 5, advanced weak = 1) over a grid on the 60 dev pairs. Among
equal-cost thresholds the highest is taken (most conservative auto-advance). Result: 0.49, written to
`results/thresholds.json` and never re-tuned after looking at test. Escalation rate is always reported next to it.

### 10. Buffer band below the threshold
`[T_high − 0.05, T_high)` escalates as `BORDERLINE_SCORE` rather than flipping on extraction noise. The noise floor
(`results/robustness.json`) is the evidence for its width.

### 11. Labels written blind to scores, before the scorer
The 200 labels (`golden/make_labels.py`) were written from `labelling_sheet.md` (JD text and resume title/years/skills,
no scores) before `score.py` existed. Honest caveat: the labeller (Claude, at the user's request) also designed the
scoring formula in the plan. One rubric-application slip was found later (JD07/R090 should be 1, not 0). It was
**left uncorrected** to avoid post-hoc label editing, and is reported in the failure analysis.

### 12. Split by job, each resume in exactly one split
Resumes are partitioned 30/70 (seed 13) before pair sampling. JDs are 3 dev / 7 test. No resume text seen during
tuning appears in test (validated in `make_labels.py`).

### 13. BM25 seeds the candidate pools, not our scorer
Top/middle buckets come from BM25 rank, so the pools aren't selected by the system under test. Random and
rule-picked hard cases (title inflation/deflation, child-skill-only, ML-without-Python) add coverage.

### 14. A different judge model, but the same vendor
Only free-tier Gemini keys were available, so the explanation judge is `gemini-3.5-flash` (a larger model than the
`gemini-3.1-flash-lite` generator) and the second golden-set labeller is `gemini-3-flash-preview`. `gemini-2.5-pro` and
`2.5-flash` are retired for new projects, 3.1 Pro has a free quota of 0, and judge-capable models allow ~20 requests/day
per key, so the judge rates only the 40 reference-rated explanations (the ones agreement needs). Self-preference bias is reduced, not eliminated. The judge is to be validated against the
author's ratings of 40 explanations (the current reference ratings were made by the AI assistant).

### 15. Code-based groundedness check in addition to the judge
Every quoted span in an explanation must fuzzy-match (partial ratio ≥ 90) the visible resume text, or it is removed
and counted. The explainer never sees the raw resume, only scorer output. Trailing punctuation inside quotes produced
3 false hallucinations in the first run; the check now strips it.

### 16. Noise floor before fairness deltas
Each fairness original is re-extracted with fresh (salted) calls. A counterfactual delta is only meaningful above
that run-to-run variance.

### 17. Post-hoc ablations kept out of the headline
After seeing test errors, an oracle-JD-requirements run and a non-blocking `CAREER_SWITCH` run were added to
*explain* them (`results/ablations.json`). The headline numbers remain those of the frozen system.

### 18. Blind scoring as fairness mitigation; location as a flag only
Production masks names, contacts and street address (city kept for the flag). The mitigation mode also removes
institution, pronouns, gendered group names and graduation year. Location never enters the score;
`LOCATION_MISMATCH` (onsite JD, different city) is shown to the recruiter but never blocks an advance on its own.

### 19. Injection handled by architecture first, detection second
Delimiters and an "untrusted data" instruction; the LLM has no tools and never outputs a score; hidden text is stripped
before the LLM sees it; detection routes to `SUSPECTED_MANIPULATION` → always escalate. Detection is regex-based and
deliberately conservative ("you are the owner of…" must not fire); `results/adversarial.json` shows what it misses.

### 20. Rejected: "ideal resume" vector retrieval
Similarity to a prototype resume isn't fit, and gives no evidence or gaps to explain. The embedding baseline
(`results/baselines.json`) shows what similarity alone achieves. Revisit only as a recall stage at ~50k applicants.

### 21. Masked text only to APIs; cache committed
Only masked text is ever sent to Gemini. Responses are cached by `sha256(model, prompt version, schema, prompt, salt)`
in `cache/llm/`, and sentence embeddings in `cache/embeddings.json`, so `make reproduce` needs no API key.

### 22. Kaggle datasets replaced by the local corpus
At the user's request the pipeline uses `data/resume/*.docx` (100 templated synthetic resumes) and
`data/jd/postings2.csv` (LinkedIn postings, 10 UK JDs hand-picked). `data/download.py` and `data/subsample.py` from
the plan are replaced by `data/prepare.py`.

### 23. An API failure is missing data, never an empty resume
In production a failed extraction escalates (`EXTRACTION_FAILED`), which is safe. Inside the evaluation harness, the
first fairness run let quota failures through as "resume with no skills". That made every blind-mode comparison an
identical 0, which looked like perfect fairness. The harness now marks those rows `available=False`, compares only
variant pairs where both sides really ran, and reports coverage next to every result. Robustness and adversarial
runs were re-checked: they had no failures.

### 24. Non-employment entries never count as experience
The fairness suite caught the extractor recording "Career break – full-time family caregiving (2016–2017)" as a role,
which added about 1 year of experience. `experience.py` now skips career breaks, sabbaticals, caregiving and parental
leave: they are never counted and never penalised. All 200 golden-set scores were re-checked and are unchanged (the
corpus has no such entries), so no headline number moved.

### 25. Framework categories in the skill map (post-test fix, impact measured)
A real uploaded resume listing Express.js and FastAPI got no credit for "web development frameworks such as Django or
Flask". The requirement was cleaned down to `web`, and the taxonomy had no framework category. Added
`web framework` / `frontend framework` parents (Express.js, FastAPI, Django, Flask, Spring Boot, NestJS, Rails…) and
aliases for common JD phrasings. "Such as" examples are examples, so any framework satisfies. A language alone does not.
The requirements panel now flags any requirement outside the skill map ("exact matches only"), so this class of
miss is visible instead of silent. On the golden set this changed 5 JD06 test scores and 0 decisions (Spearman
0.648 → 0.646). The headline numbers stay those of the frozen system.

### 26. CAREER_SWITCH tuned on dev: data cannot calibrate it, so the value stays 0.25
Grid over `career_switch_relevance` (off, 0.00–0.60) on the 60 dev pairs, with the rule fixed before looking: minimum
expected cost, ties keep the current value. Dev cost is 0 for every value from "off" up to 0.30 (the flag never fires
on dev there) and rises to 25–50 from 0.35 (it starts blocking good JD02 candidates, whose role relevance is ≥ 0.347).
So dev only gives an upper bound, and the rule keeps 0.25 (`results/career_switch_tuning.json`; test impact: none).
Root cause: the corpus has no genuine career switchers, so a blocking flag for them can't be validated here, and
role relevance is computed from titles plus identical template bullets, which is not comparable across jobs (dev JD08
median 0.12 vs JD07 0.55). Recommended next step: make the flag informational until labelled switchers exist.
That is a policy choice; the post-hoc test ablation (recall 0.43 → 0.61) must not be the reason to make it.

### 27. CAREER_SWITCH is informational in v1.1 (policy change, made after test, measured separately)
Reason: a blocking flag needs evidence that it catches what it targets. The corpus has no genuine career switchers, and
dev tuning (#26) could not calibrate it. The post-hoc test ablation was not the justification. The flag is still
computed and shown to the recruiter ("ⓘ information only"); it no longer blocks auto-advance.
`decide.career_switch_blocking: true` restores v1.0. Measured on test, added after #25: recall 0.43 → 0.61,
precision 1.00 (10/10 → 14/14), escalation 0.93 → 0.90, cost 65 → 45. Exactly 4 decisions changed, all escalate →
advance and all labelled "advance". Dev is unchanged. Frozen v1.0 artefacts are archived in `results/v1_0_frozen/`;
v1.1 measurements, with per-change attribution, are in `results/v1_1.json`. Reported side by side; the headline stays v1.0.
Cost of the change: the "fake skills in the skills list" attack goes from 2/4 to 4/4 auto-advanced, because the flag
had been incidentally blocking two of them. The next mitigation is to require ≥ 1 "used" must-have to auto-advance.
