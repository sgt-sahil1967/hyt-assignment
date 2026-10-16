"""Build REPORT.pdf from report/main.tex (the ACM SIGGRAPH-style template) with Tectonic, and print the page count.

    .venv/bin/python tools/report_pdf.py     # or: make report

report/main.tex is the source of the report; report/styles/ holds the template's class files (unchanged).
The brief allows at most 6 pages.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "report" / "main.tex"


def main() -> int:
    if not shutil.which("tectonic"):
        print("tectonic not found (brew install tectonic)")
        return 1
    with tempfile.TemporaryDirectory() as d:
        r = subprocess.run(["tectonic", "-X", "compile", str(SRC), "--outdir", d], capture_output=True, text=True, cwd=SRC.parent)
        if r.returncode:
            print((r.stdout + r.stderr)[-3000:])
            return 1
        shutil.copy(Path(d) / "main.pdf", ROOT / "REPORT.pdf")
    with pdfplumber.open(ROOT / "REPORT.pdf") as pdf:
        n = len(pdf.pages)
    print(f"REPORT.pdf: {n} pages ({'OK' if n <= 6 else 'OVER the 6-page limit'})")
    return 0 if n <= 6 else 2


if __name__ == "__main__":
    sys.exit(main())
