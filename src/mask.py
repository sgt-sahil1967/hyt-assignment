"""PII masking (plan §5.2). Never logs originals; returns per-document replacement counts."""
from __future__ import annotations

import re
from collections import Counter

EMAIL = re.compile(r"\S+@\S+\.\w+")  # whole token: names often hide in handles
URL = re.compile(
    r"(https?://\S+|www\.\S+|\b(?:linkedin|github|gitlab|behance|bitbucket)\.(?:com|io)/\S*|\b[\w-]+\.(?:dev|io|me|com|co\.uk)/\S*)",
    re.IGNORECASE,
)
PHONE = re.compile(
    r"(?<![\w-])(?:\+\d{1,3}[\s-]?)?(?:\(?\d{2,5}\)?[\s-]?)?\d{3,5}[\s-]?\d{3,6}(?![\w-])"
)
DOB = re.compile(
    r"\b(?:d\.?o\.?b\.?|date of birth|born(?: on)?)\s*[:\-]?\s*[\w ,./-]{4,20}\d{2,4}", re.IGNORECASE
)
ADDRESS_LINE = re.compile(r"^\s*(?:address|location of residence|residence)\s*[:\-].*$", re.IGNORECASE | re.MULTILINE)
STREET = re.compile(
    r"\b\d{1,5}[A-Za-z]?\s+(?:[A-Z][a-z]+\s){1,3}(?:Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Drive|Dr|Close|Way|Court|Place|Nagar|Marg)\b\.?(?:,\s*[A-Z][\w ]+)*"
)
UK_POSTCODE = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b")
IN_PIN = re.compile(r"\b(?:pin(?:code)?|pin code)\s*[:\-]?\s*\d{6}\b|\b\d{3}\s?\d{3}\b(?=\s*(?:india|$))", re.IGNORECASE)
US_ZIP = re.compile(r"\b[A-Z]{2}\s\d{5}(?:-\d{4})?\b")
YEARS_RANGE = re.compile(r"\b(19|20)\d{2}\s*[-–]\s*(?:(19|20)\d{2}|present|current)\b", re.IGNORECASE)
NAME_LINE = re.compile(r"^[A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){1,3}$")
SECTION_WORDS = {"professional summary", "summary", "skills", "experience", "education", "projects", "profile"}


def _protect_year_ranges(text: str) -> tuple[str, dict]:
    keep = {}

    def sub(m):
        k = f"\x01{len(keep)}\x01"
        keep[k] = m.group(0)
        return k

    return YEARS_RANGE.sub(sub, text), keep


def _address_to_city(m: re.Match) -> str:
    """Keep coarse location (city, country) for the location flag; drop street / number / postcode."""
    parts = [p.strip() for p in m.group(0).split(":", 1)[-1].split(",") if p.strip()]
    tail = [p for p in parts[-2:] if not re.search(r"\d", p)] if len(parts) >= 2 else []
    return "Address: [ADDRESS]" + (", " + ", ".join(tail) if tail else "")


def mask(text: str, mask_names: bool = True, known_names: list[str] | None = None) -> tuple[str, dict]:
    counts: Counter = Counter()

    def rep(pattern, token, s, label=None):
        s, n = pattern.subn(token, s)
        counts[label or token] += n
        return s

    text, keep = _protect_year_ranges(text)
    text = rep(EMAIL, "[EMAIL]", text)
    text = rep(URL, "[URL]", text)
    text = rep(DOB, "[DOB]", text)
    text = rep(ADDRESS_LINE, _address_to_city, text, "[ADDRESS]")
    text = rep(STREET, "[ADDRESS]", text)
    text = rep(UK_POSTCODE, "[ADDRESS]", text)
    text = rep(US_ZIP, "[ADDRESS]", text)
    text = rep(IN_PIN, "[ADDRESS]", text)
    text = rep(PHONE, "[PHONE]", text)

    if mask_names:
        lines = text.splitlines()
        for i, ln in enumerate(lines[:3]):  # header name = first non-empty person-like line
            s = ln.strip()
            if s and NAME_LINE.match(s) and s.lower() not in SECTION_WORDS:
                # full name only: masking single tokens would eat skills ("Ruby", "Rust")
                known_names = (known_names or []) + [s]
                lines[i] = "[NAME]"
                counts["[NAME]"] += 1
                break
        text = "\n".join(lines)
        for nm in sorted(set(known_names or []), key=len, reverse=True):
            if len(nm) < 3:
                continue
            text, n = re.subn(rf"\b{re.escape(nm)}\b", "[NAME]", text)
            counts["[NAME]"] += n

    for k, v in keep.items():
        text = text.replace(k, v)
    return text, dict(counts)
