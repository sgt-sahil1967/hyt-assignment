"""Evidence-weighted fit score (plan §5.5). Deterministic; every number is traceable to evidence."""
from __future__ import annotations

import re
from typing import Optional

from .config import cfg
from .embed import cosine
from .experience import compute_yoe
from .normalize import canon, satisfies
from .schemas import Evidence, ScoreResult

# default minimum years when the JD states none (seniority band floor); never triggers MISSING_MUST_HAVE
IMPLIED_MIN_YEARS = {"intern": 0, "junior": 0, "mid": 2, "senior": 4, "lead": 6, "unspecified": 0}
TECH_FIELDS = re.compile(r"comput|software|engineer|math|statist|physics|informat|data|electr|science|stem|technolog", re.I)
DEGREE_RANK = {"none": 0, "diploma": 1, "other": 1, "bachelor": 2, "master": 3, "phd": 4}


def _mentions(text: str, surface: str, canonical: str) -> bool:
    t = text.lower()
    for s in {surface.lower(), canonical}:
        if s and re.search(r"(?<![\w.+#])" + re.escape(s.lower()) + r"(?:e?s)?(?![\w+#])", t):
            return True
    return False


def candidate_skills(res: dict) -> dict[str, dict]:
    """canonical skill -> {strength, basis, quote, surface}. 'used' is verified by code against role/project text."""
    st = cfg()["score"]["evidence_strength"]
    usage_text = "\n".join([r.get("description_evidence", "") for r in res.get("roles", [])] +
                           [p.get("evidence", "") for p in res.get("projects", [])])
    project_skills = {canon(s) for p in res.get("projects", []) for s in p.get("skills", [])}
    out: dict[str, dict] = {}

    def put(c, prof, quote, surface):
        s = st[prof]
        if c not in out or s > out[c]["strength"]:
            out[c] = {"strength": s, "basis": prof, "quote": quote, "surface": surface}

    for sk in res.get("skills", []):
        c = canon(sk["name"])
        prof = sk.get("proficiency", "listed")
        if prof == "used" and not _mentions(usage_text, sk["name"], c) and c not in project_skills:
            prof = "listed"  # LLM said used but no role/project text shows it: downgrade (anti-hallucination)
        if prof != "learning" and _mentions(usage_text, sk["name"], c):
            prof = "used"
        put(c, prof, sk.get("evidence") or sk["name"], sk["name"])
    for p in res.get("projects", []):
        for s in p.get("skills", []):
            put(canon(s), "used", p.get("evidence") or p.get("name"), s)
    # skills that only appear in bullets (e.g. "Built REST APIs") without a skills-list entry
    for phrase, c in (("REST API", "rest api"),):
        if c not in out and _mentions(usage_text, phrase, c):
            put(c, "used", phrase, phrase)
    return out


def _match(req: dict, skills: dict[str, dict]) -> tuple[float, Optional[str], str, Optional[str]]:
    options = [canon(req["name"])] + [canon(a) for a in req.get("alternatives", []) or []]
    if cfg()["score"].get("split_slash_requirements", False) and "/" in req["name"] and canon(req["name"]) != "ci/cd":
        # v1.2: "unix/linux", "html/css" -> either part satisfies (the combined string is rarely in the skill map)
        options += [canon(p) for p in req["name"].split("/") if p.strip()]
    best = (0.0, None, "missing", None)
    need = int(req.get("min_matches") or 1)
    if need > 1:  # example-list group: proportional credit until `need` distinct items are evidenced
        hits = []
        for opt in dict.fromkeys(options[1:]):
            for c, info in skills.items():
                if satisfies(c, opt):
                    hits.append((info["strength"], c, info["basis"], info["quote"]))
                    break
        if not hits:
            return best
        top = max(hits)
        frac = min(1.0, len(hits) / need)
        return (round(top[0] * frac, 4), top[1], f"{top[2]}+group:{len(hits)}/{need}", top[3])
    for opt in options:
        for c, info in skills.items():
            how = satisfies(c, opt)
            if how and info["strength"] > best[0]:
                basis = info["basis"] if how == "exact" else f"{info['basis']}+taxonomy:{c}->{opt}"
                best = (info["strength"], c, basis, info["quote"])
    return best


def _degree_strength(req: dict, res: dict, eq_allowed: bool, yoe: float) -> tuple[float, str]:
    eds = res.get("education", [])
    best = max((DEGREE_RANK.get(e.get("degree_level", "none"), 0) for e in eds), default=0)
    tech = any(TECH_FIELDS.search(e.get("field", "") or "") for e in eds)
    if best >= 2 and (tech or "degree" == req["name"].strip()):
        return 1.0, "degree"
    if best >= 2:
        return 0.5, "degree:unrelated_field"
    if eq_allowed and yoe >= 3:
        return 1.0, "equivalent_experience"
    return 0.0, "missing"


def role_text(res: dict) -> str:
    parts = [r.get("title", "") for r in res.get("roles", [])]
    parts += [r.get("description_evidence", "") for r in res.get("roles", [])]
    parts += [f"{p.get('name', '')}: {p.get('evidence', '')}" for p in res.get("projects", [])]
    return "\n".join(p for p in parts if p)


def score_pair(job_id: str, resume_id: str, jd: dict, res: dict, as_of=None) -> ScoreResult:
    """as_of: date "Present" resolves to = when the application was received (default: config as_of_date)."""
    c = cfg()["score"]
    skills = candidate_skills(res)
    exp = compute_yoe(res.get("roles", []), as_of)
    yoe = exp["yoe"]

    must = [r for r in jd.get("must_have", []) if r["type"] in ("skill", "degree")]
    nice = [r for r in jd.get("nice_to_have", []) if r["type"] == "skill"]
    must_w_scale = 1.0
    if not [r for r in must if r["type"] == "skill"] and nice:
        must, nice, must_w_scale = must + nice, [], c["vague_jd_must_weight"]  # vague JD (edge case 5)

    evidence: list[Evidence] = []
    gaps: list[str] = []

    title = jd.get("title", "") or ""

    def req_weight(r) -> float:
        """Technologies named in the job title are the core of the role (e.g. 'Software Engineer (C++)')."""
        if r["type"] != "skill":
            return 1.0
        opts = [r["name"]] + list(r.get("alternatives") or [])
        return c["title_skill_weight"] if any(_mentions(title, o, canon(o)) for o in opts) else 1.0

    def cover(reqs, level):
        vals, ws = [], []
        for r in reqs:
            if r["type"] == "degree":
                s, basis = _degree_strength(r, res, jd.get("equivalent_experience_allowed", False), yoe)
                ev = Evidence(requirement=r["name"], level=level, matched_skill=None, strength=s, basis=basis)
            else:
                s, m, basis, quote = _match(r, skills)
                ev = Evidence(requirement=r["name"], level=level, matched_skill=m, strength=s, basis=basis, quote=quote)
            evidence.append(ev)
            vals.append(min(1.0, s))
            ws.append(req_weight(r))
            if s == 0:
                gaps.append(f"missing {level}-have: {r['name']}")
            elif s < 0.5:
                gaps.append(f"weak evidence ({ev.basis}) for {level}-have: {r['name']}")
        return sum(v * w for v, w in zip(vals, ws)) / sum(ws) if vals else None

    must_cov = cover(must, "must")
    nice_cov = cover(nice, "nice")

    # experience fit; over-qualification not penalised
    min_years = jd.get("min_years")
    implied = min_years is None
    target = IMPLIED_MIN_YEARS.get(jd.get("seniority", "unspecified"), 0) if implied else float(min_years)
    yoe_eff = yoe
    if jd.get("seniority") in ("intern", "junior") and any(p.get("skills") for p in res.get("projects", [])):
        yoe_eff += c["entry_level_project_substitution_years"]
    exp_fit = 1.0 if not target else min(1.0, yoe_eff / target)
    if exp_fit < 1.0:
        gaps.append(f"experience {yoe:.1f}y below {'implied ' if implied else ''}{target:g}y")

    # role relevance: what the candidate has been doing vs what the role is
    rt = role_text(res)
    if rt.strip():
        raw = cosine(rt, f"{jd.get('title', '')}. {jd.get('summary', '')}")
        lo, hi = c["role_relevance_rescale"]
        rel = max(0.0, min(1.0, (raw - lo) / (hi - lo)))
    else:
        rel = None

    w = dict(c["weights"])
    w["must_have"] *= must_w_scale
    comps = {"must_have": must_cov, "nice_to_have": nice_cov, "experience": exp_fit, "role_relevance": rel}
    present = {k: v for k, v in comps.items() if v is not None}
    tot_w = sum(w[k] for k in present)
    fit = sum(w[k] * v for k, v in present.items()) / tot_w if tot_w else 0.0

    capped = any(e.level == "must" and e.strength == 0 for e in evidence)
    if capped:
        fit *= c["missing_must_have_cap"]  # multiplicative cap: never above 0.6, order preserved

    return ScoreResult(job_id=job_id, resume_id=resume_id, score=round(fit, 4),
                       components={k: (round(v, 4) if v is not None else None) for k, v in comps.items()},
                       evidence=evidence, gaps=gaps, yoe=yoe, yoe_confidence=exp["confidence"], capped=capped)


def rank(results: list[ScoreResult]) -> list[ScoreResult]:
    """Deterministic: score desc, then must-have coverage desc, then resume id."""
    return sorted(results, key=lambda r: (-r.score, -(r.components.get("must_have") or 0), r.resume_id))
