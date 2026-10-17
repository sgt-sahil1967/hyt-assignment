# HYT AI Screening Agent (Software Engineering / IT)

An AI screening agent that **extracts → matches → explains → decides** for (JD, resume) pairs, plus an evaluation
harness that measures whether it can be trusted.

> **The LLM reads, code judges.** Gemini only turns documents into schema-validated JSON and writes explanation prose.
> Experience, coverage, score and decision are deterministic Python, traceable to quoted evidence.
> The agent never rejects: it **auto-advances** or **escalates to a human with a reason code**.

See [REPORT.pdf](REPORT.pdf) for results and [DECISIONS.md](DECISIONS.md) for the decision log.

![How it works: one resume through the pipeline (Clean, Read, Normalise, Score, Decide, Explain), from the workspace's How it works page](docs/img/how-it-works.webp)

## Quick start

```bash
make setup                     # Python 3.11 venv + pinned deps (uv if present, else pip)
echo GEMINI_API_KEY=your-key > .env   # optional: only needed for live Gemini calls
make data                      # data/resume/*.docx + data/jd/postings2.csv -> sanitised, masked data/processed/
make test                      # unit tests (sanitise, mask, dates, taxonomy)
python -m src.pipeline --job JD02 --top 10 --explain 3
make app                       # Streamlit → "Load sample data"
```

The pipeline CLI prints ranked candidates with score, components (must / nice / experience / role), decision, reason
codes, must-have evidence, gaps and an explanation. Every run is appended to `results/decision_log.jsonl`
(model, prompt version, config hash, threshold).

### Windows (PowerShell)

`make` isn't available on Windows, so use these commands instead. You need **Python 3.11** (from python.org or
`winget install Python.Python.3.11`) and git. Run everything from the repository root:

```powershell
git clone https://github.com/sgt-sahil1967/hyt-assignment.git
cd hyt-assignment

py -3.11 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass   # only if activation is blocked; affects this window only
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

$env:PYTHONUTF8 = "1"       # read the repo's UTF-8 files correctly (Windows defaults to cp1252)
$env:HYT_OFFLINE = "1"      # run from the committed cache: no API key needed
streamlit run app\app.py
```

Then open http://localhost:8501 and press **⚡ Load sample data**.

* **Without activating the venv:** run `.\.venv\Scripts\python.exe -m streamlit run app\app.py` (after setting the two
  `$env:` variables above in the same window).
* **New terminal windows** need `.\.venv\Scripts\Activate.ps1` and the `$env:` lines again; they don't persist.
* **First run:** it downloads the local embedding model (`all-MiniLM-L6-v2`, about 90 MB) from Hugging Face once, so it
  needs internet that time only. `pip install` also downloads PyTorch, which is large.
* **`py` not found:** use the full path to `python.exe` from your Python 3.11 install instead.
* **Live Gemini calls** (optional): `Set-Content .env "GEMINI_API_KEY=your-key"`, and turn on "Allow live
  Gemini calls" in the app's sidebar.

Other `make` targets on Windows (venv activated, same window):

```powershell
python -m pytest -q tests                                      # make test

# make reproduce-v1.0  (headline numbers, offline)
$env:PYTHONUTF8 = "1"; $env:HYT_OFFLINE = "1"; $env:HYT_PROFILE = "v1.0"
python -m eval.run golden; python -m eval.run tune; python -m eval.run metrics
python -m eval.run baselines; python -m eval.run ablations; python -m eval.adversarial
python eval\compare_v1_0.py
Remove-Item Env:HYT_PROFILE                                    # back to the current system

python -m eval.real_set run                                    # make real-set
uvicorn web.backend.main:app --port 8765                       # make api (keep this window open)
```

For the React workspace, open a second PowerShell window and run
`npm --prefix web/frontend install; npm --prefix web/frontend run dev` (Node.js 20+), then go to http://localhost:5180.
These Windows steps haven't been tested on a Windows machine; the commands mirror the `Makefile` targets.

## Two ways to see it

Both apps call the same function, `agent.screen(candidate_text, criteria) -> dict` in [`agent.py`](agent.py), and both
run from the cache by default (no API key needed).

| | Streamlit (`make app`) | Full-stack workspace (`make api` + `make web`) |
|---|---|---|
| Purpose | Replicate the project in seconds | Show the product as a recruiter would use it |
| Start | `.venv/bin/streamlit run app/app.py`, then press **⚡ Load sample data** | `make api` (port 8765) and `make web-install && make web` (port 5180) |
| What you get | Screen any JD + resumes; benchmark jobs; all evaluation dashboards; ⚙️ Settings in the sidebar | Jobs table → workspace with ranked candidates, a requirements sheet, a candidate panel, Insights and Settings |

**Workspace flow** (`web/`, React 19 + Vite + Tailwind, FastAPI):
* **Requirements** (button in each job's header): the agent's parsed must-haves and nice-to-haves, with how many applicants show evidence for
  each. A recruiter can switch any requirement between Must / Nice / Off, add one, or set minimum years. The job
  re-ranks instantly from cached extractions, with no LLM call. This is the fix for the evaluation's #1 failure
  mode: on JD01, demoting two wrongly extracted must-haves shortlists all 8 good candidates.
* **Stages**: Suggested → Shortlisted → Ready to interview, or → Rejected. The agent only ever moves a
  candidate *into* Shortlisted (every must-have met and score ≥ threshold). Interview and Reject are human-only,
  rejecting requires a written reason, and human moves are locked, so re-scoring never overrides them. A
  **Needs review** tab shows the agent's escalation queue.
* **Threshold slider** with a live preview of who enters or leaves the shortlist. **Filters**: years, education,
  minimum score, "must show evidence for X", hide flagged.
* **Candidate panel** (tabs: Summary, Evidence, Resume, Activity): score breakdown, per-requirement evidence (used / listed / implied by taxonomy), reason codes in
  plain English, a manipulation alert, the masked resume with evidence highlighted, the explanation (flagged as
  *outdated* once requirements change), and the audit trail.
* **Coverage matrix** (candidates × requirements), **resume upload** (PDF, .docx, .html or .txt; hidden text and
  injection are stripped and flagged), **Insights** page with the evaluation results. Candidates are shown blind, by ID.
* **New roles start empty.** A **Candidates** picker adds already-parsed resumes (benchmark corpus + earlier uploads),
  searched and selected individually or all at once, with no new LLM call. Benchmark roles keep their golden-set pool.
* **Compare tab** in the candidate panel: on request only, shows how keyword, TF-IDF, embedding and LLM zero-shot would
  have ranked and decided this candidate, plus a chunked-embedding variant that reads the whole document (dev-tuned cut-offs, agreement with the golden label when there is one). The
  three cheap baselines are scored once per role; zero-shot is read from the cache, and a live call needs a second click.
* **Settings** page: change the agent while it runs (no code edits). It covers the threshold, borderline band and
  low-priority cut-off, score weights and evidence credit, the missing-must-have multiplier, career-switch and
  overqualified rules, the four v1.2 flags, the v1.3 below-seniority rule, safety thresholds, cache-only mode and the extraction model. Values are
  validated (e.g. used ≥ listed ≥ learning), every job re-screens on apply, human stage moves are kept, and overrides
  persist in the gitignored `web/backend/state.json`. `config.yaml` and the reported numbers never change; Insights
  warns while any setting differs from the default. The same settings are in the Streamlit sidebar
  (`src/settings.py`; API: `GET/PUT /api/settings/runtime`).

## Reproduce the results (no API key, no raw data, ~2 minutes)

```bash
make setup                     # once: Python 3.11 venv + pinned dependencies
make reproduce-v1.0            # HEADLINE numbers (REPORT §4-5, §8): frozen v1.0 system
make reproduce                 # current system (v1.3, REPORT §5.1-5.2) + fairness, adversarial, judge, real set
```

* Both run fully **offline** (`HYT_OFFLINE=1`): every LLM response comes from the committed `cache/llm/` and every
  embedding from `cache/embeddings.json`. A call that isn't cached raises `CacheMiss`; it never hits the API.
* The raw resumes/JDs are **not** in the repo. The pipeline starts from the committed, PII-masked
  `data/processed/*.json`; `make data` re-derives those only if the raw `data/` folder is present.
* `reproduce-v1.0` writes `results/v1_0_reproduced/` and finishes with `eval/compare_v1_0.py`, which checks every
  headline figure against the frozen archive `results/v1_0_frozen/` (exact match; bootstrap CI bounds ±0.01).
* `reproduce` regenerates the top-level `results/` for the **current** system, and on a fresh clone leaves every
  tracked file byte-identical (`git status` clean). The headline lives only in `results/v1_0_frozen/`, which no
  target rewrites; REPORT §4-5 and §8, the Streamlit evaluation pages and the web Insights page read it from there.
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
golden/                  rubric, sampler, labels (200 pairs, AI-drafted), extraction gold, ratings, relabels, and my own
                         review: human_labels.csv (60 blind labels, from blind_sample_responses_author.txt), human_review_raw.md (40 verdicts)
eval/                    run.py (metrics, tuning, baselines, robustness, ablations), judge.py, fairness.py, adversarial.py
synthetic/               SYNTHETIC fairness / adversarial variants (never in the golden set)
cache/                   LLM responses (masked inputs only) + embeddings
results/                 current-system JSON / CSV / PNG (`make reproduce`); v1_0_frozen/ = headline (REPORT §4-5, §8)
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
* **Real-resume sanity set** (REPORT §5.2): `data/prepare_real.py` samples 45 resumes from Kaggle
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

## Sources and citations

Everything the project borrowed, used or consulted is listed here; the report only points to this section.

**Datasets**

* Kaggle, *Resume Dataset* (snehaanbhawal): <https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset>. 45 resumes in the
  real-resume sanity set (REPORT §5.2), selected by content.
* Kaggle, *LinkedIn Job Postings* (arshkon): <https://www.kaggle.com/datasets/arshkon/linkedin-job-postings>. 5 postings in the
  same set.
* Kaggle, *1.3M LinkedIn Jobs & Skills (2024)* (asaniczka): <https://www.kaggle.com/datasets/asaniczka/1-3m-linkedin-jobs-and-skills-2024>.
  The local postings file has this schema; 10 UK postings were hand-picked from it (see Data).
* Jiechieu, K.F.F., Tsopze, N. *Skills prediction based on multi-label resume classification using CNN with model predictions
  explanation.* Neural Comput & Applic (2020), <https://doi.org/10.1007/s00521-020-05302-x>. Dataset: `resume_corpus`,
  <https://github.com/florex/resume_corpus>. Used for a local pilot only (`eval/corpus_set.py`, never committed).
* Further public datasets reviewed as sources:
  * Kaggle, *Resume Dataset* (jithinjagadeesh): <https://www.kaggle.com/datasets/jithinjagadeesh/resume-dataset>
  * CVParserPro, *Software Engineering Dataset*: <https://cvparserpro.io/software-engineering-dataset>
  * Kaggle, *Software Engineering Jobs Dataset* (yazeedfares): <https://www.kaggle.com/datasets/yazeedfares/software-engineering-jobs-dataset>
* The 100 main-test resumes are synthetic and were supplied by the author (see Data).

**Models and services**

* Google Gemini API, `gemini-3.1-flash-lite` (extraction and explanations) and `gemini-3-flash-preview` (second labeller).
* Anthropic Claude Sonnet (LLM judge, extraction and labelling for the real-resume set) and Claude Code (coding assistant).
  The golden labels and the 40 reference explanation ratings were drafted with it (REPORT §3, §6).
* Sentence embeddings: `sentence-transformers/all-MiniLM-L6-v2`, <https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2>;
  Reimers & Gurevych, *Sentence-BERT*, EMNLP 2019, <https://arxiv.org/abs/1908.10084>.

**Software and templates**

* Python libraries: see `requirements.txt` (pydantic, google-genai, sentence-transformers, rank_bm25, rapidfuzz,
  scikit-learn for TF-IDF, scipy, pandas, python-docx, pdfplumber, langdetect, FastAPI, Streamlit).
* Frontend: React, Vite, Tailwind CSS, lucide-react.
* Report: the ACM SIGGRAPH LaTeX template (`report/styles/acmsiggraph.cls`, unmodified), built with Tectonic.
* FastAPI Cloud documentation was used for deployment: <https://fastapicloud.com/docs/>.

**Written for this project:** the skill alias list and taxonomy; the fairness name lists (hand-picked common names, no
external list).
