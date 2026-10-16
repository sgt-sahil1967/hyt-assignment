# HYT AI Screening Agent: Report

The report is **[REPORT.pdf](REPORT.pdf)** (6 pages). Its source is [`report/main.tex`](report/main.tex), written in the
ACM SIGGRAPH template (`report/styles/`). Rebuild it with `make report` (needs [Tectonic](https://tectonic-typesetting.github.io/)).

The section numbers other files refer to are the PDF's:

| § | content |
|---|---|
| 1 | Problem framing |
| 2 | How it works |
| 3 | Data and golden set |
| 4 | Results against baselines |
| 5, 5.1, 5.2 | Decision policy, changes made after the test, check on real resumes |
| 6 | Explanation quality |
| 7 | Fairness |
| 8 | Prompt injection and adversarial resumes |
| 9 | Failure analysis (top 5) |
| 10 | What is misleading about my headline number |
| 11 | What I would do with one more week |

In short: the agent shortlists or escalates (it never rejects). On the 140 held-out test pairs it ranks better than the
keyword, TF-IDF and embedding baselines and than asking the LLM directly, and all 10 candidates it shortlisted were good,
but it misses many good candidates (recall 0.43 against the AI-drafted labels, and lower against my own). The main test
data is synthetic, and the golden labels were drafted by Claude; I hand-labelled 60 pairs blind and I am more generous than
the draft (`golden/human_labels.csv`, `make review-labels`). Claude Code wrote most of the code under my direction.

Reproduce the headline numbers with `make reproduce-v1.0` (about a minute, offline, no API key).
