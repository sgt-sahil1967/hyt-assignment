# Decision log

The 15 non-obvious decisions, each with the alternative considered and why it lost. Numbers refer to `results/`.

### 1. Never auto-reject: advance or escalate only
The agent sends the strongest candidates to a recruiter and everyone else to a human queue with a reason code. `LOW_FIT`
only lowers queue priority. A wrongly rejected candidate is invisible and unrecoverable; a wrong escalation costs a
few minutes of recruiter time.

### 2. The LLM reads, code judges
Gemini only turns documents into schema-validated JSON and writes the explanation prose. Experience, coverage, score,
threshold and decision are deterministic Python, so every number traces to a line of code and a quote. The decision
can't be swayed by persuasion in the resume, and the evaluation can separate extraction errors from scoring errors
(#14). The zero-shot ablation shows the alternative: the same LLM deciding directly advanced 72 test candidates, and
52 of them were wrong. *Rejected:* "ideal resume" vector retrieval. Similarity isn't fit and gives no evidence or
gaps to explain; worth revisiting only as a recall stage at ~50k applicants.

### 3. Experience comes from dates in code, and "Present" = the date the application was received
The LLM copies date strings verbatim; `experience.py` merges overlapping intervals, sets year-only dates to 1 July,
weights internships ×0.5, and gives unparseable or future dates low confidence (which escalates). Benchmark resumes
are dated 2024-01-15 (the JDs' posting era: from today every candidate would have ≥ 3.3 years and junior vs senior
would vanish); uploaded resumes use their upload date. Career breaks, sabbaticals, caregiving and parental leave are
never counted and never penalised (the fairness suite caught a caregiving break being counted as a year of work).

### 4. Evidence strength, with "used" verified by code
used = 1.0, listed = 0.5, learning = 0.25. The LLM's "used" claim is downgraded unless the skill appears in a role or
project bullet, and upgraded when a bullet shows it. Children satisfy parents (Spring Boot ⇒ Java), never the
reverse. Listed-only credit halves the gain from keyword stuffing; it can't stop a candidate who simply lies (#11).

### 5. Multiplicative cap for a missing must-have
`fit *= 0.6` instead of the planned `min(fit, 0.6)`. A hard ceiling would tie every candidate missing a must-have at
0.6 and collapse the ranking. That matters because 6 of 10 JDs have a must-have nobody meets. The multiplicative
form still guarantees ≤ 0.6 and keeps the order.

### 6. Role-core weighting: title technologies ×2, implied minimum years
The technology named in the job title is the core of the role. Without the ×2 weight, "C++" counted as much as
"REST API", which every resume has. Set a priori, it changed only JD08 on dev (Spearman 0.11 → 0.48). When a JD gives
no minimum, seniority implies one (mid 2y, senior 4y). This feeds `experience_fit` only and never raises
`MISSING_MUST_HAVE`; otherwise a 0.5-year "Senior" scored the same as a 5.5-year one.

### 7. Cost-matrix threshold tuned on dev only, frozen, with a buffer band
`T_high` minimises expected cost (missed good = 5, advanced weak = 1) over a grid on the 60 dev pairs. Ties take the
highest (most conservative) value, giving 0.49, which was never re-tuned after test. `[T_high − 0.05, T_high)`
escalates as `BORDERLINE_SCORE` instead of flipping on noise. Escalation rate is always reported next to it.

### 8. Golden set: labels before the scorer, split by job, pools not chosen by the system
The 200 labels were written from a sheet showing no scores, before `score.py` existed. They were drafted by the AI
assistant at the author's request. The author then hand-labelled 60 pairs blind: they were more generous than the
draft on 37 pairs and stricter on none (kappa 0.60), so `labels.csv` is kept as drafted for the frozen headline and the
difference is reported in REPORT §10. The second rater is in REPORT §3. Resumes
were partitioned 30/70 (seed 13) *before* sampling pairs, so each resume is in exactly one split (validated). Pools
are BM25-seeded plus random and rule-picked hard cases, so the system under test didn't choose its own candidates.
One rubric slip found later (JD07/R090) was left unchanged rather than edit labels post hoc.

### 9. Explanations: scorer output only, code-checked quotes, judge from a different model family
The explainer never sees the raw resume. Every quoted span must fuzzy-match the visible resume (partial ratio ≥ 90) or
it's removed and counted. The LLM judge is **Claude Sonnet** (low effort, run as a separate agent with a fixed rubric
and blind to the reference ratings), a different family from the Gemini generator, which limits self-preference bias.
Earlier Gemini judges were abandoned: free-tier quotas allowed only 7 of 40 items. Trade-off: the agent judge can't be
re-run by `make`, so its scores and exact prompt are committed (`results/judge_scores.csv`, `eval/judge_prompt_sonnet.md`).

### 10. Fairness: noise floor first, blind-scoring mitigation, location as a flag only
Counterfactual deltas only count above run-to-run variance (measured as 0 at temperature 0). Name, gender cues,
institution and age never enter the score. The mitigation mode also strips institution, pronouns, gendered group
names and graduation year. Location never enters the score: `LOCATION_MISMATCH` is shown to the recruiter but never
blocks an advance on its own.

### 11. Injection is handled by architecture first, detection second
Inputs are delimited and labelled untrusted; the LLM has no tools and never outputs a score; hidden text (HTML/DOCX/PDF
white, tiny, off-page, zero-width) is stripped before the LLM sees it. Detection is a regex that routes to
`SUSPECTED_MANIPULATION`, which always escalates. It's deliberately conservative ("you are the owner of…" must not
fire). `results/adversarial.json` shows what gets through: trigger-free injection and fake listed skills.

### 12. Privacy and reproducibility: masked data only, committed cache, private uploads
Only PII-masked text reaches an API. LLM responses are cached by `sha256(model, prompt version, schema, prompt, salt)`.
The cache, embeddings and masked processed data are committed, so `make reproduce-v1.0` needs no key and no raw data.
LLM calls for real uploaded resumes are cached in `cache/private/` (gitignored), so real applicants never reach the repo.

### 13. Data: a local corpus instead of the brief's Kaggle datasets
At the author's request, the pipeline uses 100 templated synthetic `.docx` resumes and 10 hand-picked UK postings from a
local LinkedIn postings file (not the *arshkon* dataset named in the brief). This is disclosed throughout and is the main
limitation in REPORT §10. A 50-pair real-resume sanity set from the brief's own Kaggle datasets (§5.2) checks it. Resumes
are picked by *content*, because Kaggle's category label is unreliable: only 18 of 120 "IT" resumes are developers.

### 14. Evaluation integrity: frozen headline, diagnostics kept separate, failures are missing data
The headline is the system frozen before test (archived in `results/v1_0_frozen/`, reproducible exactly). Ablations
added after seeing test errors (oracle JD requirements, non-blocking `CAREER_SWITCH`) only *explain* errors. In the
harness, an API failure is missing data, never an empty resume: the first fairness run scored quota failures as
"no skills" and looked perfectly fair. Rows are now marked unavailable and coverage is reported.

### 15. Post-test v1.1 changes, each measured separately and kept out of the headline
(a) **Framework categories** in the skill map: a real resume's Express.js/FastAPI got no credit for "web frameworks
such as Django or Flask". 5 test scores changed, 0 decisions. (b) **`CAREER_SWITCH` informational.** Dev tuning was
flat from "off" to 0.30 (the corpus has no career switchers), so the pre-committed rule kept 0.25. Making it non-blocking
is a policy choice justified by that missing evidence, not by the test ablation. Test: recall 0.43 → 0.61, precision
1.00 (14/14), 4 decisions changed, all correct; dev unchanged. **Cost:** the fake-skills attack goes from 2/4 to 4/4
auto-advanced. The next mitigation is to require ≥ 1 "used" must-have to auto-advance. (c) **v1.2, four real-data fixes**
(REPORT §5.2): example lists become one requirement needing ⌈n/3⌉ ≤ 3 items, because a first "any one" version advanced
5 weak candidates; `OVERQUALIFIED` applies only to junior roles; the "best fit" injection false positive is fixed; and
"a/b" requirements accept either part. All are deterministic code behind flags that are off in the v1.0 profile. Golden
decisions are unchanged; on the real set the one good candidate is advanced with 0 wrong advances. The real set
informed the design, so it is not a clean test of v1.2. (d) **v1.3, `UNDER_SENIORITY`:** a senior/lead role with no stated
minimum escalates candidates below half the implied years (senior 4y, lead 6y); before, the shortfall only lowered
`experience_fit`, and a 2.6-year candidate was shortlisted for a Lead role. 0 golden or real-set decisions change. A
**chunked embedding** variant (whole document, not the first 256 tokens) is reported next to the evaluated baseline,
never in its place: better on long real resumes, worse on the short synthetic ones.
