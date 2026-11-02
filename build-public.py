#!/usr/bin/env python3
"""Build the public, PII-free resume site from the private resume repo.

Source of truth is the private repo's generated HTML:
    ../resume/resumes/platform-architect/platform-architect.html

This script NEVER authors content. It only:
  1. strips phone + email from the contact line (keeps "Bangalore, India"),
  2. fixes the stylesheet path,
  3. writes resume.html (pure, ATS-clean) and index.html (site view with a
     download bar),
  4. renders resume.pdf from resume.html with WeasyPrint,
  5. refuses to finish if any PII survives anywhere in the outputs.

Run:
    DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib \
    ../resume/.venv/bin/python build-public.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIVATE = HERE.parent / "resume"
SRC_HTML = PRIVATE / "resumes" / "platform-architect" / "platform-architect.html"
SRC_MASTER = PRIVATE / "src" / "master.md"
PDF = HERE / "resume.pdf"

# Shape-based PII checks — the literal values are never written down here,
# because this file is published. They are read from the private master.md.
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
PHONE_CANDIDATE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")


def find_phone(text: str) -> list[str]:
    """Digit-dense candidates only — '2004 - 2008' is a date, not a phone."""
    return [m.group() for m in PHONE_CANDIDATE_RE.finditer(text) if sum(c.isdigit() for c in m.group()) >= 10]

PUBLIC_CONTACT = "Bangalore, India"

CSS_LINK_OLD = '<link rel="stylesheet" href="../../styles/resume.css">'
CSS_LINK_NEW = '<link rel="stylesheet" href="styles/resume.css">'

# Breathing room around the resume: wider PDF margins, and a gutter on the web
# page, which otherwise runs to the browser edge. Print-only and screen-only, so
# neither changes the extracted text.
PUBLIC_CSS = """<style>
  @page { margin: 20mm 22mm 18mm 22mm; }
  body { font-size: 9.25pt; line-height: 1.36; }
  @media screen {
    :root { --gutter: max(24px, calc((100vw - 210mm) / 2)); }
    body { padding: 32px var(--gutter) 48px; overflow-x: clip; }
    .site-bar { margin: -32px calc(-1 * var(--gutter)) 28px; }
  }
</style>
"""

BAR = """<div class="site-bar">
  <span>Simranjeet Singh &mdash; Resume</span>
  <a class="dl" href="resume.pdf" download>Download PDF</a>
</div>
"""

BAR_CSS = """<style>
  body { margin: 0; }
  .site-bar {
    display: flex; align-items: center; justify-content: space-between;
    gap: 1rem; padding: 0.6rem 1.25rem;
    background: #10141c; color: #e8eaf0;
    font-family: Inter, system-ui, -apple-system, sans-serif; font-size: 14px;
  }
  .site-bar .dl {
    color: #10141c; background: #e8eaf0; text-decoration: none;
    padding: 0.35rem 0.8rem; border-radius: 999px; font-weight: 600;
  }
  .site-bar .dl:hover { background: #fff; }
  @media print { .site-bar { display: none; } }
</style>
"""


def scrub(html: str) -> str:
    html = re.sub(
        r'<p class="contact">.*?</p>',
        f'<p class="contact">{PUBLIC_CONTACT}</p>',
        html,
        count=1,
        flags=re.S,
    )
    if CSS_LINK_OLD not in html:
        sys.exit(f"stylesheet link not found in {SRC_HTML} — template changed?")
    html = html.replace(CSS_LINK_OLD, CSS_LINK_NEW)
    return html.replace("</head>", PUBLIC_CSS + "</head>", 1)


def private_pii() -> list[str]:
    """Pull the phone number and email out of the private contact header."""
    if not SRC_MASTER.exists():
        sys.exit(f"missing private source: {SRC_MASTER}")
    header = SRC_MASTER.read_text(encoding="utf-8").splitlines()
    contact = header[1] if len(header) > 1 else header[0]
    out = []
    out += EMAIL_RE.findall(contact)
    out += find_phone(contact)
    return out


def check_no_pii(*texts: str) -> None:
    literals = private_pii()
    if not literals:
        sys.exit("ABORT: could not read the private contact header; refusing to publish")
    for label, text in zip(("html", "index", "pdf"), texts):
        for needle in literals + ["mailto:"]:
            if needle.lower() in text.lower():
                sys.exit(f"ABORT: PII {needle!r} found in {label} output")
        hit = EMAIL_RE.search(text) or (find_phone(text) or [None])[0]
        if hit:
            sys.exit(f"ABORT: {label} output still looks like it contains contact PII: {hit!r}")


def main() -> None:
    if not SRC_HTML.exists():
        sys.exit(f"missing source html: {SRC_HTML}\nrun ../resume/scripts/build.sh platform-architect")

    pure = scrub(SRC_HTML.read_text(encoding="utf-8"))

    # Pure resume page — this is what the PDF is rendered from. No site chrome,
    # so the ATS text extraction is identical to the private build.
    (HERE / "resume.html").write_text(pure, encoding="utf-8")

    # Site view — same resume plus a download bar (never rendered to PDF).
    site = pure.replace("</head>", BAR_CSS + "</head>", 1).replace(
        '<header class="resume-header">', BAR + '<header class="resume-header">', 1
    )
    (HERE / "index.html").write_text(site, encoding="utf-8")

    from weasyprint import HTML

    HTML(string=pure, base_url=str(HERE) + "/").write_pdf(str(PDF))

    # Same extractor the private repo's ats-check.py uses.
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(str(PDF))
    pdf_text = "\n".join(pdf[i].get_textpage().get_text_range() for i in range(len(pdf)))
    check_no_pii(pure, site, pdf_text)

    first = [ln for ln in pdf_text.splitlines() if ln.strip()]
    print("ok  resume.pdf pages:", len(pdf))
    print("ok  extracts as:", first[0][:60] if first else "<empty>")
    print("ok  no phone/email in html, index, or pdf")


if __name__ == "__main__":
    main()
