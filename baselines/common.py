"""Shared I/O for baselines: same input (masked resume text + JD text) and output (score per pair)."""
from __future__ import annotations

import re

TOK = re.compile(r"[a-z0-9+#.]+")
STOP = set("""a an and are as at be by for from has have in is it of on or our that the their this to we with you your
will can who what which into about all any its they them more most other such than then there these those""".split())


def tokens(t: str) -> list[str]:
    return [w.strip(".") for w in TOK.findall(t.lower()) if len(w.strip(".")) > 1 and w not in STOP]


def resume_body(text: str) -> str:
    """Drop the masked contact header so baselines compare content only."""
    return "\n".join(ln for ln in text.splitlines() if not re.match(r"^(\[NAME\]|Address:|Email:|Phone:)", ln))
