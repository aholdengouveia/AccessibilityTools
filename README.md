# TEX to HTML Conversion Tools

Convert .tex files to clean, accessible HTML.

## Quick Start

### Interactive Converter (PDF + HTML)

The easiest way to convert a single .tex file to both PDF and HTML:

```bash
cd tools
./update-tex-outputs.sh
```

The script will:
- ✓ Prompt you for the .tex file path
- ✓ Validate the file exists
- ✓ Generate both PDF (via pdflatex) and HTML (via tex-to-html.py)
- ✓ Show clear success/failure messages
- ✓ Clean up auxiliary files (.aux, .log, etc.)

### Convert a Single File to HTML Only

```bash
cd IntroData/labs
python3 ../../tools/tex-to-html.py usesandabusesofdata.tex
```

Or specify a backend explicitly:

```bash
python3 ../../tools/tex-to-html.py --backend=pandoc usesandabusesofdata.tex
python3 ../../tools/tex-to-html.py --backend=htlatex usesandabusesofdata.tex
```

### Convert All Files in a Directory

```bash
cd IntroData/labs
make
```

## The Unified HTML Converter

The `tex-to-html.py` script is a unified converter that supports multiple backends:

**Backends:**
- **custom** - Fast Python parser (always available, default)
- **pandoc** - Robust LaTeX parsing (requires pandoc)
- **htlatex** - Complex document support (requires TeX4ht)

The converter auto-detects the best available backend, or you can specify one explicitly with `--backend=<name>`.

**Features:**
- ✓ Clean, semantic HTML5
- ✓ Proper `<header>`, `<main>`, `<section>` structure
- ✓ ARIA labels (`aria-labelledby`) for accessibility
- ✓ Responsive design (viewport meta tag)
- ✓ Links to accessible-lab.css in tools folder
- ✓ Converts lists, figures, and **tables** automatically
- ✓ **Accessible table support** with proper `<thead>`, `<tbody>`, `<th scope="col">`, and `<td>` elements
- ✓ No complex LaTeX-generated classes
- ✓ Automatic post-processing for clean output
- ✓ Supports `\input{}` and `\include{}` commands (recursively expands included files)

**Example Output:**
```html
<!DOCTYPE html>
<html lang="en-US">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Lab Title</title>
    <link href="../../tools/accessible-lab.css" rel="stylesheet" type="text/css">
</head>
<body>
    <header>
        <h1>Lab Title</h1>
        ...
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

## Usage from Makefile

Each labs directory has a Makefile. Just run:

```bash
cd IntroData/labs
make              # Convert all .tex files
make watch        # Auto-convert on changes (requires entr)
make clean        # Remove generated HTML
```

## Table Support

The converter automatically converts LaTeX tables to accessible HTML tables:

```latex
\begin{table}[h]
\centering
\caption{Student Grades}
\begin{tabular}{|l|c|r|}
\hline
\textbf{Name} & \textbf{Score} & \textbf{Grade} \\
\hline
Alice & 95 & A \\
Bob & 87 & B+ \\
Charlie & 92 & A- \\
\hline
\end{tabular}
\end{table}
```

**Converts to:**
```html
<div class="table-container">
  <table>
    <caption id="student-grades">Student Grades</caption>
    <thead>
      <tr>
        <th scope="col">Name</th>
        <th scope="col">Score</th>
        <th scope="col">Grade</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>Alice</td><td>95</td><td>A</td></tr>
      <tr><td>Bob</td><td>87</td><td>B+</td></tr>
      <tr><td>Charlie</td><td>92</td><td>A-</td></tr>
    </tbody>
  </table>
</div>
```

**Features:**
- ✓ Proper semantic HTML with `<thead>`, `<tbody>`, `<th>`, `<td>`
- ✓ Accessibility attributes (`scope="col"` on headers)
- ✓ Responsive design with horizontal scrolling on mobile
- ✓ Caption support with `\caption{}`
- ✓ Header row detection using `\textbf{}`
- ✓ **Supports `longtable` environment** for multi-page tables
- ✓ Automatically handles longtable-specific commands (`\endfirsthead`, `\endhead`, `\endfoot`, `\endlastfoot`)
- ✓ Styled with alternating row colors and hover effects
- ✓ Dark mode support

## Working with Multi-File Documents

The converter automatically handles LaTeX documents that use `\input{}` or `\include{}` to split content across multiple files:

```latex
% main.tex
\documentclass{article}
\begin{document}
\input{chapter1}
\input{chapter2}
\end{document}
```

**Features:**
- ✓ Automatically expands all `\input{}` and `\include{}` commands
- ✓ Handles nested inputs (files that include other files)
- ✓ Resolves relative paths correctly
- ✓ Works with all backends (custom, pandoc, htlatex)
- ✓ Detects and warns about missing or circular includes
- ✓ Supports both `.tex` extension and without (LaTeX convention)

## Files

- `update-tex-outputs.sh` - **Interactive script to generate both PDF and HTML** (recommended for single files)
- `tex-to-html.py` - **Unified HTML converter with multiple backends** (custom/pandoc/htlatex)
- `Makefile` - Simple make interface for batch conversion
- `watch-tex.sh` - Watch script for auto-conversion

## Requirements

### For HTML conversion only:
- Python 3 (usually pre-installed)
- Optional: `entr` for watch mode (`sudo apt-get install entr`)

### For PDF + HTML conversion (update-tex-outputs.sh):
- Python 3
- pdflatex (install with: `sudo apt-get install texlive-latex-base`)

No pandoc required!

## Test Results

Successfully converts:
- ✓ usesandabusesofdata.tex → Clean, accessible HTML
- ✓ bigdata.tex
- ✓ datasecurity.tex
- ✓ datavisualizations.tex
- ✓ finalproject.tex
- ✓ labtemplate.tex
- And more...

## Accessibility Features

The generated HTML includes:
- Semantic HTML5 elements
- ARIA labels for screen readers  
- Proper heading hierarchy (h1 → h2 → h3)
- Alt text for images (from \alt{} in .tex)
- Clean, readable structure
- Mobile-responsive viewport settings

Perfect for students using screen readers or other assistive technologies!
