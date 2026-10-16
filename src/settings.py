"""Runtime-tunable settings: a validated subset of config.yaml that the apps can change while running.

Overrides patch the live `cfg()` dict in place, so every module picks them up on its next call. The defaults are the
values loaded at start-up (config.yaml + tuned thresholds + profile), so `reset()` always restores the reported system.
Nothing here writes config.yaml: the evaluation numbers in results/ stay tied to the committed configuration.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .config import cfg

MODELS = ["gemini-3.1-flash-lite", "gemini-3-flash-preview", "gemini-3.5-flash"]

# key = dotted path into cfg(). kind: float | int | bool | choice. group orders the settings panel.
SPEC: list[dict] = [
    # decision
    {"key": "decide.t_high", "group": "Decision", "label": "Auto-shortlist threshold", "kind": "float", "min": 0, "max": 1, "step": 0.01,
     "help": "Score needed to auto-shortlist (T_high). Tuned on dev to 0.49; a job can still override it."},
    {"key": "decide.delta", "group": "Decision", "label": "Borderline band", "kind": "float", "min": 0, "max": 0.2, "step": 0.01,
     "help": "Scores in [T_high − band, T_high) escalate as BORDERLINE_SCORE instead of flipping on noise."},
    {"key": "decide.t_low", "group": "Decision", "label": "Low-priority cut-off", "kind": "float", "min": 0, "max": 1, "step": 0.01,
     "help": "Below this the candidate is escalated with LOW_FIT and sorted to the bottom of the queue. Never rejected."},
    {"key": "decide.career_switch_blocking", "group": "Decision", "label": "Career switch blocks shortlisting", "kind": "bool",
     "help": "On = frozen v1.0 behaviour. Off (v1.1) = CAREER_SWITCH is shown but never blocks on its own."},
    {"key": "decide.career_switch_relevance", "group": "Decision", "label": "Career switch relevance", "kind": "float", "min": 0, "max": 1, "step": 0.01,
     "help": "Past roles less related than this (with must-haves met) raise CAREER_SWITCH."},
    {"key": "decide.overqualified_junior_only", "group": "Decision", "label": "Overqualified: junior roles only", "kind": "bool",
     "help": "v1.2. Off = flag OVERQUALIFIED for every seniority band."},
    {"key": "decide.under_seniority_blocking", "group": "Decision", "label": "Below-seniority blocks shortlisting", "kind": "bool",
     "help": "v1.3. Senior/lead role with no stated minimum years: escalate when experience is under a fraction of the implied minimum (senior 4y, lead 6y)."},
    {"key": "decide.under_seniority_fraction", "group": "Decision", "label": "Below-seniority fraction", "kind": "float", "min": 0, "max": 1, "step": 0.05,
     "help": "Escalate below this share of the implied minimum (0.5 = under 2y for senior, under 3y for lead)."},
    {"key": "decide.overqualified_years_over", "group": "Decision", "label": "Overqualified margin (years)", "kind": "int", "min": 0, "max": 15, "step": 1,
     "help": "Years above the seniority band's maximum before OVERQUALIFIED is raised."},
    # scoring
    {"key": "score.weights.must_have", "group": "Scoring", "label": "Weight: must-haves", "kind": "float", "min": 0, "max": 1, "step": 0.05,
     "help": "Weights are renormalised over the components present, so they needn't sum to 1."},
    {"key": "score.weights.nice_to_have", "group": "Scoring", "label": "Weight: nice-to-haves", "kind": "float", "min": 0, "max": 1, "step": 0.05},
    {"key": "score.weights.experience", "group": "Scoring", "label": "Weight: experience", "kind": "float", "min": 0, "max": 1, "step": 0.05},
    {"key": "score.weights.role_relevance", "group": "Scoring", "label": "Weight: role relevance", "kind": "float", "min": 0, "max": 1, "step": 0.05},
    {"key": "score.evidence_strength.used", "group": "Scoring", "label": "Credit: used in a role", "kind": "float", "min": 0, "max": 1, "step": 0.05},
    {"key": "score.evidence_strength.listed", "group": "Scoring", "label": "Credit: listed only", "kind": "float", "min": 0, "max": 1, "step": 0.05,
     "help": "Half credit by default, so keyword stuffing gains less."},
    {"key": "score.evidence_strength.learning", "group": "Scoring", "label": "Credit: learning", "kind": "float", "min": 0, "max": 1, "step": 0.05},
    {"key": "score.missing_must_have_cap", "group": "Scoring", "label": "Missing must-have multiplier", "kind": "float", "min": 0, "max": 1, "step": 0.05,
     "help": "fit × this when any must-have has no evidence. 1 = no penalty."},
    {"key": "score.title_skill_weight", "group": "Scoring", "label": "Job-title skill weight", "kind": "float", "min": 1, "max": 5, "step": 0.5,
     "help": "Requirement weight for a technology named in the job title."},
    {"key": "score.internship_weight", "group": "Scoring", "label": "Internship year weight", "kind": "float", "min": 0, "max": 1, "step": 0.05},
    # requirements parsing
    {"key": "score.consolidate_example_lists", "group": "Requirements", "label": "Merge example lists", "kind": "bool",
     "help": "v1.2. \"A, B, C, etc.\" becomes one requirement needing ⌈n/3⌉ (≤ 3) of the items."},
    {"key": "score.split_slash_requirements", "group": "Requirements", "label": "Split a/b requirements", "kind": "bool",
     "help": "v1.2. \"unix/linux\": either part satisfies the requirement."},
    # safety
    {"key": "sanitize.strict_fit_phrase", "group": "Safety", "label": "Strict \"best fit\" injection rule", "kind": "bool",
     "help": "v1.2. \"best fit\" counts as injection only when asserted about the candidate."},
    {"key": "decide.stuffing_min_skills", "group": "Safety", "label": "Keyword-stuffing skill count", "kind": "int", "min": 5, "max": 100, "step": 1,
     "help": "This many listed skills with almost no usage evidence raises SUSPECTED_MANIPULATION."},
    {"key": "sanitize.min_words", "group": "Safety", "label": "Sparse resume word count", "kind": "int", "min": 0, "max": 500, "step": 10},
    # model
    {"key": "llm.offline", "group": "Model", "label": "Cache only (no API calls)", "kind": "bool",
     "help": "On = read the committed cache only. Off = call Gemini for uploads, new jobs and explanations."},
    {"key": "llm.model", "group": "Model", "label": "Extraction model", "kind": "choice", "options": MODELS,
     "help": "The cache is keyed by model: another model needs live calls, and uncached candidates will show errors."},
]
_BY_KEY = {s["key"]: s for s in SPEC}
_DEFAULTS: dict[str, Any] | None = None


def _get(key: str):
    d = cfg()
    for k in key.split("."):
        d = d[k]
    return d


def _set(key: str, value) -> None:
    *head, last = key.split(".")
    d = cfg()
    for k in head:
        d = d[k]
    d[last] = value


def defaults() -> dict[str, Any]:
    global _DEFAULTS
    if _DEFAULTS is None:
        _DEFAULTS = {s["key"]: deepcopy(_get(s["key"])) for s in SPEC}
    return _DEFAULTS


def current() -> dict[str, Any]:
    defaults()
    return {s["key"]: _get(s["key"]) for s in SPEC}


def _coerce(spec: dict, v):
    kind = spec["kind"]
    if kind == "bool":
        if not isinstance(v, bool):
            raise ValueError(f"{spec['key']}: expected true/false")
        return v
    if kind == "choice":
        if v not in spec["options"]:
            raise ValueError(f"{spec['key']}: must be one of {spec['options']}")
        return v
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{spec['key']}: expected a number")
    v = int(v) if kind == "int" else float(v)
    if not spec["min"] <= v <= spec["max"]:
        raise ValueError(f"{spec['key']}: must be between {spec['min']} and {spec['max']}")
    return v


def validate(patch: dict[str, Any]) -> dict[str, Any]:
    """Return the coerced patch, or raise ValueError naming the first bad key. Checks cross-field rules too."""
    unknown = sorted(set(patch) - set(_BY_KEY))
    if unknown:
        raise ValueError(f"unknown setting(s): {', '.join(unknown)}")
    out = {k: _coerce(_BY_KEY[k], v) for k, v in patch.items()}
    merged = {**current(), **out}
    if merged["decide.t_low"] > merged["decide.t_high"] - merged["decide.delta"]:
        raise ValueError("the low-priority cut-off must sit below the borderline band (t_low ≤ T_high − band)")
    if sum(merged[f"score.weights.{k}"] for k in ("must_have", "nice_to_have", "experience", "role_relevance")) <= 0:
        raise ValueError("at least one score weight must be above 0")
    ev = [merged[f"score.evidence_strength.{k}"] for k in ("used", "listed", "learning")]
    if not ev[0] >= ev[1] >= ev[2]:
        raise ValueError("evidence credit must satisfy used ≥ listed ≥ learning")
    return out


def apply(patch: dict[str, Any]) -> dict[str, Any]:
    """Validate and apply a patch. Returns the keys whose value actually changed."""
    out = validate(patch)
    changed = {k: v for k, v in out.items() if _get(k) != v}
    for k, v in changed.items():
        _set(k, v)
    return changed


def overrides() -> dict[str, Any]:
    """Settings that differ from the start-up defaults (what the apps persist)."""
    d = defaults()
    return {k: v for k, v in current().items() if v != d[k]}


def reset() -> None:
    for k, v in defaults().items():
        _set(k, deepcopy(v))


def describe() -> dict:
    """Spec + current + default values, for a settings UI."""
    d, c = defaults(), current()
    return {"settings": [{**s, "value": c[s["key"]], "default": d[s["key"]]} for s in SPEC],
            "overrides": overrides()}
