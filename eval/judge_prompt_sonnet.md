# LLM-as-judge prompt (Claude Sonnet, low effort)

Run on 15 Oct 2026 as a separate Claude Code agent (model: Sonnet, effort: low). It saw only
`golden/explanation_rating_sheet.md` and was told never to open the reference ratings or `results/`. Its output is
`results/judge_scores.csv`. A different model family from the Gemini generator was chosen to limit self-preference.
Because it is an agent rather than an API call, `make` can't re-run it: the scores and this exact prompt are committed instead.

---

You are acting as an independent LLM-as-judge for a research evaluation. Your job: score 40 automated recruiting
explanations against a fixed rubric and write the scores to a CSV file. Work only from the files named below.

INPUT (read this file only): golden/explanation_rating_sheet.md
It contains a rubric, then 40 items. Each item has a heading "## JDxx / Ryyy — <job title>", a "Scorer output" JSON
block (this is the ground truth the explanation must be faithful to: score, decision, reason_codes, components,
years_experience, evidence with strengths 0..1, gaps), a masked "Resume" block, and the "Explanation" (a quoted
paragraph) you must audit.

DO NOT open or read any other file in the repository. In particular, never read golden/explanation_human_ratings.csv,
anything under results/, or any *ratings* / *judge* file. Your scores must be independent.

RUBRIC: score each explanation 1-5 (integers) on four criteria:
- groundedness: every claim is supported by the scorer output / resume. 5 = fully supported; 1 = invents skills or
  facts. Penalise claims that contradict the scorer output (e.g. saying a requirement is missing when its strength is
  > 0, or wrong numbers such as years of experience or experience gaps).
- gap_correctness: the gaps it names are the real missing or weak requirements in the scorer output, none invented,
  none important omitted. 5 = exact; 1 = wrong or misses the main gap.
- specificity: names concrete requirements, evidence and reasons rather than generic statements. 5 = very specific.
- usefulness: a recruiter could act on it: they understand why it was advanced or escalated, and what to check.
  5 = very useful.

Be strict and calibrated, and use the whole scale. Check each claim against the scorer output. Specifically, check
that reason codes are described correctly. CAREER_SWITCH means "skills match but past role titles look unrelated",
not that the person has a history of changing careers. LOW_FIT means the candidate goes to a low-priority queue.
MISSING_MUST_HAVE means a must-have has zero evidence. Also check that the stated cause of the decision matches the
reason codes, and that experience numbers and gap arithmetic are right (e.g. "0.5 years" of total experience is not
"0.5 years short"). Generic filler such as "escalated for further review" with no actionable guidance should lower
usefulness. Do not give everything 5.

OUTPUT: a CSV with header job_id,resume_id,groundedness,gap_correctness,specificity,usefulness,rationale and exactly
40 rows in sheet order; rationale = one short sentence naming the main issue found.
