# HYT AI Screening Agent (Software Engineering / IT)

An AI screening agent that **extracts → matches → explains → decides** for (JD, resume) pairs, plus an evaluation
harness that measures whether it can be trusted.

> **The LLM reads, code judges.** Gemini only turns documents into schema-validated JSON and writes explanation prose.
> Experience, coverage, score and decision are deterministic Python, traceable to quoted evidence.
> The agent never rejects: it **auto-advances** or **escalates to a human with a reason code**.

See [REPORT.md](REPORT.md) for results and [DECISIONS.md](DECISIONS.md) for the decision log.

## Quick start

```bash
make setup                     # Python 3.11 venv + pinned deps (uv if present, else pip)
cp .env.example .env           # GEMINI_API_KEY=..., LLM_PROVIDER=gemini, GEMINI_MODEL=gemini-3.1-flash-lite
make data                      # data/resume/*.docx + data/jd/postings2.csv -> sanitised, masked data/processed/
make test                      # unit tests (sanitise, mask, dates, taxonomy)
python -m src.pipeline --job JD02 --top 10 --explain 3
make app                       # Streamlit → "Load sample data"
```

The pipeline CLI prints ranked candidates with score, components (must / nice / experience / role), decision, reason
codes, must-have evidence, gaps and an explanation. Every run is appended to `results/decision_log.jsonl`
(model, prompt version, config hash, threshold).

## Two ways to see it

Both apps call the same function, `agent.screen(candidate_text, criteria) -> dict` in [`agent.py`](agent.py), and both
run from the cache by default (no API key needed).

| | Streamlit (`make app`) | Full-stack workspace (`make api` + `make web`) |
|---|---|---|
| Purpose | Replicate the project in seconds | Show the product as a recruiter would use it |
| Start | `.venv/bin/streamlit run app/app.py`, then press **⚡ Load sample data** | `make api` (port 8765) and `make web-install && make web` (port 5180) |
| What you get | Screen any JD + resumes; benchmark jobs; all evaluation dashboards | Jobs → workspace with parsed requirements (left), ranked candidates (middle), evidence drawer (right) |

**Workspace flow** (`web/`, React 19 + Vite + Tailwind, FastAPI):
* **Requirements panel**: the agent's parsed must-haves and nice-to-haves, with how many applicants show evidence for
  each. A recruiter can switch any requirement between Must / Nice / Off, add one, or set minimum years. The job
  re-ranks instantly from cached extractions, with no LLM call. This is the fix for the evaluation's #1 failure
  mode: on JD01, demoting two wrongly extracted must-haves shortlists all 8 good candidates.
* **Stages**: Suggested → Shortlisted → Ready to interview, or → Rejected. The agent only ever moves a
  candidate *into* Shortlisted (every must-have met and score ≥ threshold). Interview and Reject are human-only,
  rejecting requires a written reason, and human moves are locked, so re-scoring never overrides them. A
  **Needs review** tab shows the agent's escalation queue.
* **Threshold slider** with a live preview of who enters or leaves the shortlist. **Filters**: years, education,
  minimum score, "must show evidence for X", hide flagged.
* **Candidate drawer**: score breakdown, per-requirement evidence (used / listed / implied by taxonomy), reason codes in
  plain English, a manipulation alert, the masked resume with evidence highlighted, the explanation (flagged as
  *outdated* once requirements change), and the audit trail.
* **Coverage matrix** (candidates × requirements), **resume upload** (PDF, .docx, .html or .txt; hidden text and
  injection are stripped and flagged), **Insights** page with the evaluation results. Candidates are shown blind, by ID.

## Reproduce the results (no API key, no raw data, ~2 minutes)

```bash
make setup                     # once: Python 3.11 venv + pinned dependencies
make reproduce-v1.0            # HEADLINE numbers (REPORT §4-5, §8): frozen v1.0 system
make reproduce                 # current system (v1.2, REPORT §5b-5c) + fairness, adversarial, judge, real set
```

* Both run fully **offline** (`HYT_OFFLINE=1`): every LLM response comes from the committed `cache/llm/` and every
  embedding from `cache/embeddings.json`. A call that isn't cached raises `CacheMiss`; it never hits the API.
* The raw resumes/JDs are **not** in the repo. The pipeline starts from the committed, PII-masked
  `data/processed/*.json`; `make data` re-derives those only if the raw `data/` folder is present.
* `reproduce-v1.0` writes `results/v1_0_reproduced/` and finishes with `eval/compare_v1_0.py`, which checks every
  headline figure against the frozen archive `results/v1_0_frozen/` (exact match; bootstrap CI bounds ±0.01).
* Measured on a fresh clone: `reproduce-v1.0` 55 s (30/30 headline figures exact), `reproduce` 121 s (after `make setup`).

## Layout

```
agent.py                 public API: screen(candidate_text, criteria) -> dict (+ helpers for UIs)
app/app.py               Streamlit UI (UI only)
web/backend/             FastAPI: jobs, editable requirements, stages, audit log, uploads (wraps agent.screen)
web/frontend/            React + Vite + Tailwind workspace
samples/                 one JD + 8 masked resumes for the "Load sample data" button
config.yaml              models, weights, thresholds, selected JDs, as-of date (single source of truth)
data/prepare.py          JD selection + resume sanitise -> mask -> dedup -> language check
src/
  sanitize.py            NFKC, invisible/tag chars, hidden HTML/DOCX/PDF text (vanish, <4pt, white, off-page), injection flags
  mask.py                email/phone/URL/street/postcode/DOB/name masking (city kept for the location flag)
  llm.py                 Gemini client + sha256-keyed disk cache + schema retry
  schemas.py             Pydantic models (resume, JD, evidence, score, decision)
  extract.py             extraction prompts (untrusted-data delimiters)
  skills.yaml            ~190 aliases + parent/child taxonomy
  normalize.py           alias -> taxonomy -> embedding fallback (logged)
  experience.py          date parsing, interval union, internships x0.5, confidence
  score.py               evidence-weighted fit score
  decide.py              decision policy + reason codes
  explain.py / grounded.py  evidence-only explanation + quote verification
  pipeline.py            screen(job_id) -> ranked results; CLI
baselines/               keyword Jaccard, TF-IDF, embedding cosine, LLM zero-shot (ablation)
golden/                  rubric, sampler, labels (200 pairs), extraction gold, ratings, relabels
eval/                    run.py (metrics, tuning, baselines, robustness, ablations), judge.py, fairness.py, adversarial.py
synthetic/               SYNTHETIC fairness / adversarial variants (never in the golden set)
cache/                   LLM responses (masked inputs only) + embeddings
results/                 JSON / CSV / PNG consumed by REPORT.md
```

## Resume formats

`agent.read_document(filename, bytes)` accepts **PDF** (pdfplumber), **.docx**, **.html** and **.txt**. For PDFs, white
text, fonts under 4pt and lines placed entirely off the page are dropped and counted, so the resume is escalated as
`SUSPECTED_MANIPULATION`. A line that merely overflows the margin is kept, not flagged. A PDF with no text layer (a
scan) is escalated as `SPARSE_RESUME` without calling the LLM; OCR is deliberately not attempted. Password-protected or
corrupt files return a clear error.

## Data

* **Resumes**: `data/resume/software_engineer_cv_{1..100}.docx`, **synthetic** and templated (6 skills from a pool of
  15, one role, the same three bullets, BSc CS 2017, UK addresses). Supplied by the author; they are *not* the
  brief's primary Kaggle Resume Dataset (*snehaanbhawal/resume-dataset*), and this is the main limitation (REPORT §10).
* **JDs**: `data/jd/postings2.csv`: 9,380 real LinkedIn software-engineering postings (US/UK/CA/AU, all first seen
  25 Dec 2023), with columns `job_title, company, job_location, job_link, first_seen, search_city, search_country,
  job level, job_type, job_summary, job_skills, date_posted`. The schema matches a subset of the Kaggle
  **"1.3M LinkedIn Jobs & Skills (2024)"** dataset by *asaniczka*, **not** the brief's *arshkon/linkedin-job-postings*.
  10 UK postings were hand-picked (`config.yaml: jobs`).
* **Real-resume sanity set** (REPORT §5c): `data/prepare_real.py` samples 45 resumes from Kaggle
  *snehaanbhawal/resume-dataset* (selected by content, not category) and 5 postings from *arshkon/linkedin-job-postings*
  into 50 pairs. Only the masked subset (`data/processed_real/`) and Sonnet-agent labels (`golden_real/`, pending author
  review) are committed. `make real-set` re-runs it offline; the raw Kaggle CSVs (`data/kaggle/`) are gitignored.
* Neither raw file is committed. The pipeline runs from the committed, PII-masked `data/processed/*.json`, and only
  masked text is ever sent to an LLM API or stored in the cache.

## Models

| role | model |
|---|---|
| extraction + explanation | `gemini-3.1-flash-lite` (temperature 0) |
| LLM judge (40 explanations) | Claude Sonnet, low effort, run as a separate agent (`eval/judge_prompt_sonnet.md`) |
| second golden-set labeller | `gemini-3-flash-preview` |
| embeddings (role relevance, normalisation fallback, baseline) | `sentence-transformers/all-MiniLM-L6-v2` (local) |

## Credits

* **Job postings**: LinkedIn postings, apparently from Kaggle "1.3M LinkedIn Jobs & Skills (2024)" (asaniczka). See Data.
* **AI assistance**: built with Claude Code (Anthropic) as a coding assistant. The golden labels and the 40 reference
  explanation ratings were drafted with it (REPORT §3, §6). The LLM judge is Claude Sonnet; the pipeline's LLM is Gemini.
* Skill alias list and taxonomy: hand-written for this project.
* Fairness name lists: hand-picked common names; no external list was used.
* Libraries: see `requirements.txt` (pydantic, google-genai, sentence-transformers, rank_bm25, rapidfuzz, scikit-learn,
  scipy, pandas, python-docx, langdetect).
