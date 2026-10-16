PY := .venv/bin/python
export PYTHONPATH := .

.PHONY: review-labels report setup data golden test run eval fairness adversarial judge reproduce reproduce-v1.0 real-set app api web web-install

setup:            ## create venv + install pinned deps
	uv venv -p 3.11 .venv || python3.11 -m venv .venv
	uv pip install -p .venv -r requirements.txt || .venv/bin/pip install -r requirements.txt

data:             ## sanitise + mask resumes, select JDs -> data/processed/
	$(PY) data/prepare.py

golden:           ## sample pairs, build labels + extraction gold (labels are hand-assigned in golden/make_labels.py)
	$(PY) golden/sample.py
	$(PY) golden/make_labels.py
	$(PY) golden/make_extraction_gold.py

report:           ## REPORT.md -> REPORT.pdf (LaTeX via Tectonic; max 6 pages)
	$(PY) tools/report_pdf.py

test:             ## unit tests
	$(PY) -m pytest -q tests

app:              ## Streamlit app (UI only; logic in agent.py). Click "Load sample data".
	.venv/bin/streamlit run app/app.py

api:              ## FastAPI backend for the full-stack app (http://localhost:8765/docs)
	.venv/bin/uvicorn web.backend.main:app --port 8765

web-install:
	npm --prefix web/frontend install

web:              ## React/Vite workspace (http://localhost:5180); run `make api` in another terminal
	npm --prefix web/frontend run dev

run:              ## example: screen one job
	$(PY) -m src.pipeline --job JD02 --top 10 --explain 2

eval:             ## full evaluation harness on the golden set
	$(PY) -m eval.run golden
	$(PY) -m eval.run tune
	$(PY) -m eval.run metrics
	$(PY) -m eval.run baselines
	$(PY) -m eval.run extraction
	$(PY) -m eval.run robustness
	$(PY) -m eval.run ablations

fairness:
	$(PY) -m eval.fairness

adversarial:
	$(PY) -m eval.adversarial

review-labels:    ## author's blind hand labels vs the AI-drafted golden labels -> results/human_label_agreement.json
	$(PY) -m eval.review_labels

judge:            ## judge = Claude Sonnet agent (scores committed, see eval/judge_prompt_sonnet.md); recompute stats only
	$(PY) -m eval.judge summary
	$(PY) -m eval.judge agree
	$(PY) -m eval.judge labels

# HEADLINE (REPORT §4-5, §8): the frozen v1.0 system, from the committed cache and masked data.
# No API key, no raw data. Writes results/v1_0_reproduced/ and checks it against results/v1_0_frozen/.
reproduce-v1.0: export HYT_OFFLINE=1
reproduce-v1.0: export HYT_PROFILE=v1.0
reproduce-v1.0: data
	env -u HYT_PROFILE $(PY) -m pytest -q tests
	$(PY) -m eval.run golden
	$(PY) -m eval.run tune
	$(PY) -m eval.run metrics
	$(PY) -m eval.run baselines
	$(PY) -m eval.run ablations
	$(PY) -m eval.adversarial
	$(PY) eval/compare_v1_0.py

real-set:         ## real-resume sanity set (Kaggle resumes + arshkon postings), offline from cache
	HYT_OFFLINE=1 $(PY) -m eval.real_set run

# Everything from the committed cache: no API key, no network for the LLM.
# (needs the raw data/ folder for ingestion; the sentence-embedding cache is committed too)
reproduce: export HYT_OFFLINE=1
reproduce: data golden test eval fairness adversarial judge
	$(PY) -m eval.run v1_1
	$(PY) -m eval.real_set run
	$(PY) -m eval.posthoc
	@echo "reproduced the current system (v1.3, REPORT §5.1-5.2) from cache -> results/"
