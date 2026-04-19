# LaTeX Accessibility Toolkit

Tools to make LaTeX documents accessible and convert them to clean, accessible HTML.

---

## Table of Contents

- [Quick Start](#quick-start)
- [What to Run When](#what-to-run-when)
  - [Accessible PDF](#accessible-pdf-latex-accessibilitypy--pdflatex)
  - [Accessible HTML](#accessible-html-tex-to-htmlpy)
  - [Both PDF and HTML at once](#both-pdf-and-html-at-once-update-tex-outputssh)
- [Full Workflow: New Lab File](#full-workflow-new-lab-file)
- [What `add` Does Automatically](#what-add-does-automatically)
- [What `add` Warns About](#what-add-warns-about-requires-manual-fix)
- [Examples](#examples)
  - [Before and After](#before-and-after-making-a-latex-file-accessible)
  - [Dry Run Output](#dry-run-output)
  - [Verbose Output](#verbose-output)
  - [Fixing a Broken Structure](#fixing-a-broken-structure)
  - [HTML Table Conversion](#html-conversion-latex-table--accessible-html-table)
  - [HTML Document Structure](#html-conversion-document-structure)
- [HTML Conversion Details](#html-conversion-details)
- [Troubleshooting](#troubleshooting)
- [Requirements](#requirements)
- [Files](#files)

---

## Quick Start

**Never used this before? Start here.**

### Step 1 — Install requirements

```bash
# LaTeX (for PDF generation)
sudo apt-get install texlive-latex-base texlive-fonts-recommended

# Python 3 is usually already installed — check with:
python3 --version
```

See [INSTALL.md](INSTALL.md) for macOS, Windows, and optional tools.

### Step 2 — Make a single file accessible

```bash
python3 latex-accessibility.py add myfile.tex
```

That's it. The tool adds the missing packages, PDF bookmark configuration, accessibility notice, and URL formatting automatically.

Not sure what it will change? Preview first with no files written:

```bash
python3 latex-accessibility.py add myfile.tex --dry-run
```

### Step 3 — Convert to HTML

```bash
python3 tex-to-html.py myfile.tex
```

### Prefer a guided experience?

Run the wizard — it asks you everything and shows a preview before making any changes:

```bash
python3 latex-accessibility.py wizard
```

### Processing a whole directory?

```bash
# Preview first
python3 latex-accessibility.py add-all labs/ --dry-run

# Apply to all files
python3 latex-accessibility.py add-all labs/

# Get a written compliance report
python3 latex-accessibility.py report labs/
```

---

## What to Run When

### Accessible PDF (`latex-accessibility.py` → `pdflatex`)

Adds accessibility features to the `.tex` source, which `pdflatex` then compiles into an accessible PDF with working bookmarks, navigation, and proper structure.

| Situation | Command |
|-----------|---------|
| Preview what a file needs, no changes written | `python3 latex-accessibility.py add myfile.tex --dry-run` |
| Make a single file accessible | `python3 latex-accessibility.py add myfile.tex` |
| See exactly what changed, line by line | `python3 latex-accessibility.py add myfile.tex --verbose` |
| Fix a file that fails to compile | `python3 latex-accessibility.py fix myfile.tex` |
| Process every `.tex` file in a directory | `python3 latex-accessibility.py add-all labs/` |
| Preview batch changes without writing | `python3 latex-accessibility.py add-all labs/ --dry-run` |
| Generate an accessibility compliance report | `python3 latex-accessibility.py report labs/` |
| Verify a file compiles correctly | `python3 latex-accessibility.py validate myfile.tex` |
| Step-by-step guided wizard (asks you everything) | `python3 latex-accessibility.py wizard` |

**Flags that work with any command:**

| Flag | What it does |
|------|--------------|
| `--dry-run` | Show what would change — never writes to disk |
| `--verbose` | Print each change made, line by line |
| `--plain` | Replace emoji with `[OK]` / `[WARN]` / `[ERR]` for screen readers or scripts |
| `--progress` | Progress bar for batch operations (requires `pip install tqdm`) |
| `--help` / `-h` | Show full help with examples |
| `--version` / `-v` | Print version and exit |

### Accessible HTML (`tex-to-html.py`)

Converts `.tex` files directly to semantic, screen-reader-friendly HTML without going through `pdflatex`.

| Situation | Command |
|-----------|---------|
| Convert one file to HTML only | `python3 tex-to-html.py myfile.tex` |
| Convert all `.tex` files in a directory | `cd labs/ && make` |
| Watch for changes and auto-convert | `make watch` |
| Remove generated HTML files | `make clean` |

### Both PDF and HTML at once (`update-tex-outputs.sh`)

Interactive script that runs `latex-accessibility.py`, then `pdflatex`, then `tex-to-html.py` in one go:

```bash
./update-tex-outputs.sh
```

---

## Full Workflow: New Lab File

**Option A — guided (recommended for first-time use):**
```bash
python3 latex-accessibility.py wizard
```
The wizard asks you everything step by step and shows a preview before making any changes.

**Option B — command line:**
```bash
# 1. Preview what needs to change
python3 latex-accessibility.py add mylab.tex --dry-run

# 2. Apply accessibility features
python3 latex-accessibility.py add mylab.tex

# 3. Fill in any % Alt text: comments the tool added (open the file and edit)

# 4. Verify the file still compiles
python3 latex-accessibility.py validate mylab.tex

# 5. Convert to accessible HTML
python3 tex-to-html.py mylab.tex

# 6. Check the whole directory for compliance
python3 latex-accessibility.py report labs/
```

---

## What `add` Does Automatically

- Adds `\usepackage{bookmark}` and `\usepackage{enumitem}` if missing
- Adds `\bookmarksetup{numbered, open,}` for PDF navigation
- Adds an Accessibility Notice section linking to the HTML version
- Wraps plain URLs in `\url{}` so they are clickable in PDFs
- Adds `% Alt text: [Add description here for accessibility]` after any `\includegraphics` that is missing one

## What `add` Warns About (requires manual fix)

| Warning | What to do |
|---------|-----------|
| `Figure on line N has no \caption` | Add `\caption{Description}` inside the `figure` environment |
| `Table on line N has no \caption` | Add `\caption{Description}` inside the `table` environment |
| `\includegraphics` missing alt text hint | Fill in the `% Alt text:` comment with a real description |
| `Color-only text on line N` | Add `\textbf{}` or `\textit{}` so meaning isn't conveyed by color alone |

---

## Examples

### Before and After: Making a LaTeX File Accessible

**Before** — a plain file missing accessibility features:
```latex
\documentclass{article}
\usepackage{hyperref}

\hypersetup{
    colorlinks=false,
    pdftitle={My Lab}
}

\begin{document}
\maketitle

Check out https://example.com for more info.

\end{document}
```

**After** running `python3 latex-accessibility.py add myfile.tex`:
```latex
\documentclass{article}
\usepackage{hyperref}
\usepackage{bookmark}      % ← Added: PDF navigation
\usepackage{enumitem}      % ← Added: Better list spacing

\hypersetup{
    colorlinks=false,
    pdftitle={My Lab}
}

% Configure PDF bookmarks for navigation
\bookmarksetup{            % ← Added: bookmark configuration
    numbered,
    open,
}

% Configure list spacing for better accessibility
\setlist{nosep}

\begin{document}
\maketitle

\section*{Accessibility Notice}        % ← Added: notice section
This document is also available in HTML format at:
\url{https://yoursite.com/labs/myfile.html}
...

Check out \url{https://example.com} for more info.   % ← Fixed: URL wrapped

\end{document}
```

---

### Dry Run Output

Preview exactly what would change before touching any files:

```bash
python3 latex-accessibility.py add myfile.tex --dry-run
```
```
[DRY RUN] myfile.tex — 3 change(s) would be made:
  + add package(s): bookmark, enumitem
  + wrap plain URLs in \url{}
  + add accessibility notice section
```

On a file that is already compliant:
```
[DRY RUN] myfile.tex — no changes needed (already compliant)
```

---

### Verbose Output

See each individual change as it is applied:

```bash
python3 latex-accessibility.py add myfile.tex --verbose
```
```
  - Added package: bookmark
  - Added package: enumitem
  - Added accessibility notice section
  - Added alt text hint to 2 \includegraphics instance(s)
  ⚠️  Figure on line 12 has no \caption — add a description for accessibility
✓ Added accessibility features to myfile.tex
```

---

### Fixing a Broken Structure

If `\bookmarksetup` ended up inside `\hypersetup`, the file will fail to compile:

```latex
% Broken — \bookmarksetup wrongly nested inside \hypersetup:
\hypersetup{
    colorlinks=false,
    pdftitle={My Lab},
\bookmarksetup{
    numbered,
    open,
}
    pdfauthor={Author},
}
```

```bash
python3 latex-accessibility.py fix myfile.tex
# ✓ Fixed structure in myfile.tex
```

```latex
% Fixed — correctly separated:
\hypersetup{
    colorlinks=false,
    pdftitle={My Lab},
    pdfauthor={Author},
}

\bookmarksetup{
    numbered,
    open,
}
```

---

### HTML Conversion: LaTeX Table → Accessible HTML Table

**LaTeX source:**
```latex
\begin{table}[h]
\centering
\caption{Star Wars vs Star Trek: The Important Questions}
\begin{tabular}{|l|c|c|}
\hline
\textbf{Feature} & \textbf{Star Wars} & \textbf{Star Trek} \\
\hline
Earl Grey Tea, Hot & No & Yes (Picard approves) \\
The Force          & Yes & Only if Spock raises an eyebrow \\
Lightsabers        & Yes & Negative, Captain \\
Transporters       & No & Energize! \\
Warp Speed         & Hyperspace & Yes, make it so \\
\hline
\end{tabular}
\end{table}
```

**Generated HTML:**
```html
<div class="table-container">
  <table>
    <caption id="star-wars-vs-star-trek">Star Wars vs Star Trek: The Important Questions</caption>
    <thead>
      <tr>
        <th scope="col">Feature</th>
        <th scope="col">Star Wars</th>
        <th scope="col">Star Trek</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>Earl Grey Tea, Hot</td><td>No</td><td>Yes (Picard approves)</td></tr>
      <tr><td>The Force</td><td>Yes</td><td>Only if Spock raises an eyebrow</td></tr>
      <tr><td>Lightsabers</td><td>Yes</td><td>Negative, Captain</td></tr>
      <tr><td>Transporters</td><td>No</td><td>Energize!</td></tr>
      <tr><td>Warp Speed</td><td>Hyperspace</td><td>Yes, make it so</td></tr>
    </tbody>
  </table>
</div>
```

---

### HTML Conversion: Document Structure

**Generated HTML structure:**
```html
<!DOCTYPE html>
<html lang="en-US">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Lab Title</title>
    <link href="../../css/accessible-lab.css" rel="stylesheet" type="text/css">
</head>
<body>
    <header>
        <h1>Lab Title</h1>
    </header>
    <main>
        <section aria-labelledby="objectives">
            <h2 id="objectives">Objectives</h2>
            ...
        </section>
    </main>
</body>
</html>
```

---

## HTML Conversion Details

`tex-to-html.py` supports three backends — it auto-detects the best available one:

| Backend | Speed | Requires |
|---------|-------|----------|
| `custom` | Fast | Python 3 only (always available, default) |
| `pandoc` | Robust | `pandoc` installed |
| `htlatex` | Full LaTeX | TeX4ht installed |

Force a specific backend with `--backend=pandoc` etc.

**The generated HTML includes:**
- Semantic HTML5 (`<header>`, `<main>`, `<section>`)
- ARIA labels for screen readers
- Proper heading hierarchy
- Accessible tables (`<thead>`, `<tbody>`, `<th scope="col">`)
- Responsive design and dark mode via `accessible-lab.css`
- Handles `\input{}` / `\include{}` (recursively expands included files)

---

## Troubleshooting

### "TeX capacity exceeded" compilation error

**Symptom:** `pdflatex` fails with output like:
```
! TeX capacity exceeded, sorry [input stack size=5000].
```

**Cause:** `\bookmarksetup` ended up nested inside `\hypersetup` — usually from a previous run of the tool on an already-modified file.

**Fix:**
```bash
python3 latex-accessibility.py fix myfile.tex
# ✓ Fixed structure in myfile.tex
```

---

### "LaTeX Error: File `bookmark.sty' not found" (or similar package error)

**Symptom:**
```
! LaTeX Error: File `bookmark.sty' not found.
```

**Cause:** The required LaTeX package isn't installed on your system.

**Fix:** Install the full recommended LaTeX package set:
```bash
# Ubuntu / Debian
sudo apt-get install texlive-latex-recommended texlive-latex-extra

# Then verify the tool can see the packages
python3 latex-accessibility.py check-packages
```

---

### "Permission denied" when writing a file

**Symptom:**
```
❌ Error: Permission denied writing to myfile.tex
```

**Cause:** The file is read-only, or owned by another user.

**Fix:** Check and correct the file permissions:
```bash
# Check who owns the file and its permissions
ls -l myfile.tex

# Make it writable by you
chmod u+w myfile.tex

# Then re-run
python3 latex-accessibility.py add myfile.tex
```

---

### "File is not valid UTF-8 text"

**Symptom:**
```
❌ Error: File myfile.tex is not valid UTF-8 text
   Suggestion: Check if this is a binary file or has encoding issues
```

**Cause:** The `.tex` file was saved with a different character encoding (common with older Windows editors that default to Latin-1 or Windows-1252).

**Fix:** Convert the file to UTF-8:
```bash
# Check the current encoding
file myfile.tex

# Convert from latin-1 to UTF-8
iconv -f latin-1 -t utf-8 myfile.tex -o myfile_utf8.tex

# Verify it looks correct, then replace the original
mv myfile_utf8.tex myfile.tex
```

---

### PDF looks wrong after running `add`

**Symptom:** The tool reports success but the generated PDF still lacks bookmarks or shows the old content.

**Cause:** The `.tex` source was updated but `pdflatex` hasn't been re-run to regenerate the PDF.

**Fix:** Recompile — the `validate` command does this and checks for errors:
```bash
python3 latex-accessibility.py validate myfile.tex
```

Or compile directly:
```bash
pdflatex myfile.tex
```

---

### File shows "already compliant" but you expected changes

**Symptom:**
```
○ myfile.tex already has accessibility features
```

**Cause:** The tool detected that all features it adds are already present in the source file.

**Fix:** Use `--dry-run` to see exactly what the tool checks:
```bash
python3 latex-accessibility.py add myfile.tex --dry-run
```

If you want to see the full feature status including warnings (missing captions, alt text, etc.), generate a report:
```bash
python3 latex-accessibility.py report .
```

---

### `--progress` flag shows a warning about tqdm

**Symptom:**
```
⚠️  tqdm not installed — falling back to verbose output.
   To install: pip install tqdm
```

**Fix:**
```bash
pip install tqdm
```

The tool works fine without it — `--progress` just falls back to standard per-file output.

---

## Requirements

| Tool | Required for | Install |
|------|-------------|---------|
| Python 3 | Everything | Usually pre-installed |
| pdflatex | PDF generation, `validate` | `sudo apt-get install texlive-latex-base` |
| pandoc | `--backend=pandoc` | `sudo apt-get install pandoc` |
| entr | `make watch` | `sudo apt-get install entr` |
| tqdm | `--progress` flag | `pip install tqdm` |

See [INSTALL.md](INSTALL.md) for full setup instructions.

---

## Files

| File | Purpose |
|------|---------|
| `latex-accessibility.py` | Main tool — add, fix, check, and report on LaTeX accessibility |
| `tex-to-html.py` | Convert `.tex` files to accessible HTML |
| `accessible-lab.css` | Stylesheet for the generated HTML |
| `update-tex-outputs.sh` | Interactive script — generate PDF and HTML for one file |
| `Makefile` | Batch HTML conversion via `make` |
| `watch-tex.sh` | Auto-convert on file changes |
| `add-lab-links.py` | Add lab navigation links to topic HTML pages |
| `INSTALL.md` | Installation and setup instructions |
