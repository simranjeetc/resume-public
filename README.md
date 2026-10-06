# Resume — Simranjeet Singh

Public, **phone- and email-free** resume. Live at
**https://simranjeetc.github.io/resume-public/** (`index.html` = resume + PDF
download; `resume.html` = clean page; `resume.pdf` = the file to send).

## Where the content comes from

Nothing here is authored. The single content source is the **private**
`simranjeetc/resume` repo. This repo holds rendered artifacts only:

| File | Role |
| --- | --- |
| `index.html` | resume + a download bar (site view) |
| `resume.html` | pure resume page, no chrome — the PDF is rendered from this |
| `resume.pdf` | what recruiters download / ATS parses |
| `styles/` | `resume.css` + bundled Inter (OFL) |
| `build-public.py` | regenerates the three files above |

## Rebuild

```bash
# 1. rebuild in the private repo first (source of truth)
cd ../resume && ./scripts/build.sh platform-architect

# 2. regenerate the scrubbed public artifacts
cd ../resume-public
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib ../resume/.venv/bin/python build-public.py

# 3. commit + push (Pages redeploys automatically)
```

`build-public.py` strips the phone number and email from the contact line
(keeping `Bangalore, India`), re-renders the PDF through the same
HTML+WeasyPrint+Cassius path as the private build, and **aborts if the phone
number or email survives anywhere in the HTML or the extracted PDF text**.

Layout, CSS and ATS guarantees (`styles/resume.css`) are copied unchanged from
the private repo — do not edit them here; edit them in `../resume/styles/` and
re-copy.
