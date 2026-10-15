"""Years of experience from role date ranges (plan §5.4). Code, never the LLM.

- union of role intervals (overlaps merged); "Present"/"Current" = as-of date
- year-only dates -> mid-year (1 July); seasons -> mid-season month
- internships count x internship_weight, only for time not already covered by full-time roles
- future / reversed / unparseable dates -> clamped or skipped, confidence "low"
"""
from __future__ import annotations

import re
from datetime import date

from .config import as_of, cfg

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}
SEASONS = {"spring": 4, "summer": 7, "fall": 10, "autumn": 10, "winter": 1}
# entries an extractor may list as "roles" that are not employment (found by the fairness suite: a caregiving
# break was counted as a year of experience)
NON_WORK = re.compile(r"career break|sabbatical|caregiv|parental leave|maternity|paternity|gap year|travell?ing|"
                      r"career gap|time off|unemployed|medical leave", re.I)
PRESENT = re.compile(r"^(present|current(ly)?|now|today|till date|to date|ongoing|date)$", re.I)


def parse_date(s: str, ref: date | None = None) -> tuple[date | None, bool]:
    """Return (date, exact). exact=False when only the year (or a season) is known."""
    ref = ref or as_of()
    s = (s or "").strip().lower().replace(",", " ").replace(".", " ")
    s = re.sub(r"\s+", " ", s)
    if not s:
        return None, False
    if PRESENT.match(s):
        return ref, True
    m = re.match(r"^(\d{4})[-/](\d{1,2})(?:[-/]\d{1,2})?$", s)  # 2019-03
    if m:
        return _safe(int(m.group(1)), int(m.group(2))), True
    m = re.match(r"^(\d{1,2})[-/](\d{4})$", s)  # 03/2019
    if m:
        return _safe(int(m.group(2)), int(m.group(1))), True
    m = re.match(r"^([a-z]+)\s*'?(\d{2}|\d{4})$", s)  # Mar 2019, march 2019, Summer 2020, Jan '21
    if m:
        y = int(m.group(2))
        y = y + 2000 if y < 100 and y <= ref.year % 100 + 1 else (y + 1900 if y < 100 else y)
        w = m.group(1)
        if w[:3] in MONTHS:
            return _safe(y, MONTHS[w[:3]]), True
        if w in SEASONS:
            return _safe(y, SEASONS[w]), False
    m = re.match(r"^(?:q([1-4])\s*)?(\d{4})$", s)  # 2019, Q3 2019
    if m:
        y = int(m.group(2))
        if m.group(1):
            return _safe(y, (int(m.group(1)) - 1) * 3 + 2), False
        return _safe(y, 7), False
    return None, False


def _safe(y: int, mth: int) -> date | None:
    if 1950 <= y <= 2100 and 1 <= mth <= 12:
        return date(y, mth, 1)
    return None


def _merge(iv: list[tuple[date, date]]) -> list[tuple[date, date]]:
    out: list[list[date]] = []
    for s, e in sorted(iv):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return [(s, e) for s, e in out]


def _years(iv) -> float:
    return sum((e - s).days for s, e in iv) / 365.25


def _subtract(iv, cover):
    """Parts of intervals iv not covered by (merged) intervals cover."""
    out = []
    for s, e in iv:
        cur = s
        for cs, ce in cover:
            if ce <= cur or cs >= e:
                continue
            if cs > cur:
                out.append((cur, cs))
            cur = max(cur, ce)
        if cur < e:
            out.append((cur, e))
    return out


def compute_yoe(roles: list[dict], ref: date | None = None) -> dict:
    """roles: [{start, end, is_internship}] -> {yoe, confidence, issues, intervals}"""
    ref = ref or as_of()
    w_intern = cfg()["score"]["internship_weight"]
    full, intern, issues = [], [], []
    for r in roles:
        if NON_WORK.search(r.get("title", "") or ""):
            continue  # not employment: never counted as experience, and never penalised
        s, _ = parse_date(r.get("start", ""), ref)
        e, _ = parse_date(r.get("end", "") or "present", ref)
        if s is None or e is None:
            issues.append(f"unparseable:{r.get('start')}-{r.get('end')}")
            continue
        if s > ref:
            issues.append(f"future_start:{r.get('start')}")
            continue
        if e > ref:
            issues.append(f"future_end_clamped:{r.get('end')}")
            e = ref
        if e < s:
            issues.append(f"end_before_start:{r.get('start')}-{r.get('end')}")
            s, e = e, s
        (intern if r.get("is_internship") else full).append((s, e))
    full_m = _merge(full)
    intern_only = _merge(_subtract(_merge(intern), full_m))
    yoe = _years(full_m) + w_intern * _years(intern_only)
    return {
        "yoe": round(yoe, 2),
        "confidence": "low" if issues else "high",
        "issues": issues,
        "n_roles": len(roles),
    }
