# Labelling rubric: real-resume sanity set

Same scale and decision rule as the main golden set (`golden/rubric.md`), applied to real, messy resumes.

**Who labelled:** Claude Sonnet, as separate agents per job, at the author's request. **Pending the author's review.**
The labelling agents saw only the job description, the resume text and this rubric: never the pipeline's
extractions, scores or decisions.

## What is judged
Only skills, experience, projects and role history. Ignore names, schools, locations, citizenship and company names.

## Must-haves
Take the job's must-haves from what the posting states as required ("required", "must have", "basic
qualifications", "requirements", minimum years). "Preferred", "plus" and "nice to have" are not must-haves. Soft skills
and generic traits (communication, problem solving, US citizenship) are not scored. A skill counts as **met** when the
resume names it, listed or used; evidence of use in a role or project is stronger. An explicit minimum of years
counts as a must-have; estimate total professional software/IT experience from the dates on the resume.

## Relevance (0–3)
| grade | meaning |
|---|---|
| 3 strong | meets the core must-haves (or nearly all), experience suits the level, and the role history fits |
| 2 good | meets the core technical must-haves but thin elsewhere (short on years, few nice-to-haves, adjacent role) |
| 1 weak | real overlap with the stack, but a core must-have is clearly missing |
| 0 no fit | the primary technology or role type is missing |

When unsure between two grades, choose the lower one.

## Ideal decision
`advance` iff relevance ≥ 2 **and** no stated must-have (including explicit minimum years) is clearly missing **and**
the candidate is not clearly overqualified for a junior/entry role. Otherwise `escalate`. The system never rejects.
