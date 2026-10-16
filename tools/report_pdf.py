"""Render REPORT.md to REPORT.pdf with LaTeX (Tectonic), and print the page count.

    .venv/bin/python tools/report_pdf.py

REPORT.md is the single source. It uses a small Markdown subset: one `#` title (followed by one byline paragraph), `##`
sections, paragraphs, `*` and `1.` lists, `>` call-out, pipe tables, `**bold**`, `*italic*`, `code`, and one image line
`![caption](path){w=0.9}`. The brief allows at most 6 pages.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent

PREAMBLE = r"""
\documentclass[10pt,a4paper]{article}
\usepackage[a4paper,left=17mm,right=17mm,top=15mm,bottom=16mm]{geometry}
\usepackage{fontspec}
\setmainfont{texgyreheros}[Extension=.otf,UprightFont=*-regular,BoldFont=*-bold,ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
\setmonofont{lmmono10-regular}[Extension=.otf,Scale=0.9,BoldFont=lmmonolt10-bold,ItalicFont=lmmono10-italic]
\usepackage{microtype}
\usepackage{xcolor}
\definecolor{ink}{HTML}{1F2937}
\definecolor{accent}{HTML}{3730A3}
\definecolor{muted}{HTML}{6B7280}
\usepackage{graphicx,booktabs,tabularx,array,enumitem,titlesec,fancyhdr,tcolorbox,needspace,hyperref}
\hypersetup{hidelinks,pdftitle={HYT AI Screening Agent: Report},pdfauthor={Sahil Patil}}
\color{ink}
\setlength{\parindent}{0pt}\setlength{\parskip}{4pt}
\linespread{1.04}
\setlist{nosep,leftmargin=13pt,itemsep=1.6pt,topsep=2pt}
\titleformat{\section}{\large\bfseries\color{accent}}{}{0pt}{}[{\color{black!15}\titlerule}]
\titlespacing*{\section}{0pt}{11pt}{5pt}
\renewcommand{\arraystretch}{1.18}
\pagestyle{fancy}\fancyhf{}\renewcommand{\headrulewidth}{0pt}
\fancyfoot[L]{\footnotesize\color{muted} Sahil Patil · HYT AI Screening Agent}
\fancyfoot[R]{\footnotesize\color{muted} \thepage}
\tcbuselibrary{skins}
\tcbset{colback=accent!6,colframe=accent!6,boxrule=0pt,left=7pt,right=7pt,top=5pt,bottom=5pt,
        borderline west={2.2pt}{0pt}{accent},sharp corners,before skip=5pt,after skip=5pt}
\emergencystretch=2em\frenchspacing\hyphenpenalty=2000
\begin{document}
"""

UNICODE = {"×": r"$\times$", "≥": r"$\ge$", "≤": r"$\le$", "→": r"$\rightarrow$", "−": r"$-$", "κ": r"$\kappa$",
           "…": r"\ldots{}", "⇒": r"$\Rightarrow$", "⌈": r"$\lceil$", "⌉": r"$\rceil$"}
SPECIAL = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
           "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}


def esc(t: str) -> str:
    return "".join(SPECIAL.get(c, c) for c in t)


def typo(t: str) -> str:
    t = re.sub(r'"([^"]*)"', "“\\1”", t)
    t = t.replace("'", "’")
    return "".join(UNICODE.get(c, c) for c in t)


def inline(text: str) -> str:
    """Markdown inline -> LaTeX. Code spans are protected first so their contents are never restyled."""
    codes: list[str] = []

    def keep(m):
        body = esc(m.group(1)).replace("/", "/\\allowbreak{}").replace(r"\_", r"\_\allowbreak{}")
        codes.append(r"\texttt{" + body + "}")
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", keep, text)
    text = typo(esc(text))  # typo() after esc(): UNICODE entries add backslashes and braces on purpose
    text = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", text)
    text = re.sub(r"(?<![\*\\])\*(?!\s)([^*]+?)\*(?!\*)", r"\\emph{\1}", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: codes[int(m.group(1))], text)


def table(rows: list[str]) -> str:
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows if not re.match(r"^\|[\s\-:|]+\|$", r.strip())]
    head, body = cells[0], cells[1:]
    n = len(head)
    plain = lambda c: re.sub(r"[*`]", "", c)  # noqa: E731
    spec = ["X"] + ["c" if max(len(plain(r[i])) for r in body) <= 24 else "X" for i in range(1, n)]
    out = [r"{\small\begin{tabularx}{\linewidth}{" + "".join(spec) + "}", r"\toprule",
           " & ".join(r"\textbf{" + inline(c) + "}" for c in head) + r" \\", r"\midrule"]
    out += [" & ".join(inline(c) for c in r) + r" \\" for r in body]
    out += [r"\bottomrule", r"\end{tabularx}}\par\vspace{6pt}"]
    return "\n".join(out)


def convert(md: str) -> str:
    out, lines, i = [PREAMBLE], md.splitlines(), 0
    title_done = False
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
        elif ln.startswith("# "):
            sub = ""
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and not lines[j].startswith(("#", ">", "|", "*", "!")):
                sub, i = lines[j], j
            out.append(r"{\Large\bfseries\color{accent} " + inline(ln[2:]) + r"}\par\vspace{1pt}" + "\n"
                       + (r"{\footnotesize\color{muted} " + inline(sub) + r"}\par\vspace{3pt}" if sub else ""))
            title_done = True
            i += 1
        elif ln.startswith("## "):
            out.append(r"\Needspace{7\baselineskip}" + "\n" + r"\section*{" + inline(ln[3:]) + "}")
            i += 1
        elif ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append(r"\begin{tcolorbox}\small " + inline(" ".join(buf)) + r"\end{tcolorbox}")
        elif ln.startswith("|"):
            buf = []
            while i < len(lines) and lines[i].startswith("|"):
                buf.append(lines[i])
                i += 1
            out.append(table(buf))
        elif ln.startswith("!["):
            m = re.match(r"!\[(.*)\]\((.*)\)(?:\{w=([\d.]+)\})?", ln)
            cap, path, w = m.group(1), m.group(2), m.group(3) or "0.9"
            out.append(r"\begin{center}\includegraphics[width=" + w + r"\linewidth]{" + str(ROOT / path) + "}\\\\[3pt]"
                       + r"{\footnotesize\color{muted} " + inline(cap) + r"}\end{center}")
            i += 1
        elif re.match(r"^(\*|\d+\.) ", ln):
            numbered = ln[0].isdigit()
            env = "enumerate" if numbered else "itemize"
            items: list[str] = []
            while i < len(lines) and (re.match(r"^(\*|\d+\.) ", lines[i]) or (lines[i].startswith("  ") and items)):
                if re.match(r"^(\*|\d+\.) ", lines[i]):
                    items.append(re.sub(r"^(\*|\d+\.) ", "", lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append(r"\begin{" + env + "}\n" + "\n".join(r"\item " + inline(t) for t in items) + "\n" + r"\end{" + env + "}")
        else:
            buf = []
            while i < len(lines) and lines[i].strip() and not re.match(r"^(#|>|\||!\[|\* |\d+\. )", lines[i]):
                buf.append(lines[i].strip())
                i += 1
            out.append(inline(" ".join(buf)) + "\n")
    assert title_done, "REPORT.md needs a '# ' title"
    out.append(r"\end{document}")
    return "\n".join(out)


def main() -> int:
    tex = convert((ROOT / "REPORT.md").read_text())
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "REPORT.tex"
        src.write_text(tex)
        if "--keep" in sys.argv:
            (ROOT / "docs").mkdir(exist_ok=True)
            (ROOT / "docs" / "REPORT.tex").write_text(tex)
        r = subprocess.run(["tectonic", "-X", "compile", str(src), "--outdir", d], capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-2500:], r.stderr[-2500:])
            return 1
        (ROOT / "REPORT.pdf").write_bytes((Path(d) / "REPORT.pdf").read_bytes())
        warn = [ln for ln in (r.stdout + r.stderr).splitlines() if "nrepresentable" in ln or "Overfull" in ln]
        if warn:
            print("\n".join(warn[:10]))
    with pdfplumber.open(ROOT / "REPORT.pdf") as pdf:
        n = len(pdf.pages)
    print(f"REPORT.pdf: {n} pages ({'OK' if n <= 6 else 'OVER the 6-page limit'})")
    return 0 if n <= 6 else 2


if __name__ == "__main__":
    sys.exit(main())
