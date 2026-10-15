"""Render REPORT.md to REPORT.pdf (A4) via headless Chrome, and print the page count.

    .venv/bin/python tools/report_pdf.py

The brief allows at most 6 pages.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown
import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
CHROME = next((p for p in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                           shutil.which("google-chrome") or "", shutil.which("chromium") or ""] if p and Path(p).exists()), None)

CSS = """
@page { size: A4; margin: 14mm 14mm 14mm 14mm; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 10.4pt; line-height: 1.38; color: #111; }
h1 { font-size: 16pt; margin: 0 0 4pt; } h2 { font-size: 12.5pt; margin: 9pt 0 3pt; border-bottom: 1px solid #ccc; }
h3 { font-size: 10pt; margin: 6pt 0 2pt; } p, li { margin: 2pt 0; } ul, ol { padding-left: 15pt; margin: 2pt 0; }
table { border-collapse: collapse; margin: 4pt 0; font-size: 9pt; width: 100%; }
th, td { border: 1px solid #bbb; padding: 1.5pt 4pt; text-align: left; vertical-align: top; }
th { background: #f2f2f2; } code { font-family: Menlo, monospace; font-size: 8pt; background: #f4f4f4; padding: 0 2px; }
pre { font-size: 6.4pt; background: #f6f6f6; padding: 4pt; white-space: pre; overflow: hidden; margin: 3pt 0; }
blockquote { margin: 3pt 0; padding: 2pt 8pt; border-left: 3px solid #999; background: #fafafa; }
"""


def main() -> int:
    if not CHROME:
        print("Chrome/Chromium not found"); return 1
    body = markdown.markdown((ROOT / "REPORT.md").read_text(), extensions=["tables", "fenced_code", "sane_lists"])
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "report.html"
        src.write_text(html)
        out = ROOT / "REPORT.pdf"
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", src.as_uri()], check=True, capture_output=True)
    with pdfplumber.open(out) as pdf:
        n = len(pdf.pages)
    print(f"REPORT.pdf: {n} pages ({'OK' if n <= 6 else 'OVER the 6-page limit'})")
    return 0 if n <= 6 else 2


if __name__ == "__main__":
    sys.exit(main())
