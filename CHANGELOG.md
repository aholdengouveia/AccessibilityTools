# Changelog

All notable changes to the LaTeX accessibility toolkit are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).  
Both tools use [Semantic Versioning](https://semver.org/): MAJOR.MINOR.PATCH.

---

## latex-accessibility.py

### [1.5.0] — 2026-04-20

#### Added
- `--backup` flag for `add`, `fix`, `add-all`, and `fix-all` — creates a `file.tex.bak` copy before writing any changes. Backup is only created when changes are actually made (skipped files produce no backup).
- `restore <file.tex>` command — copies `file.tex.bak` back over `file.tex`. Prints a clear error if no backup exists.
- `list-backups [path]` command — lists all `*.tex.bak` files under a file or directory, showing size and modification timestamp. Defaults to the current directory if no path given.
- `check-html` and `check-html-all` now auto-detect the Chrome/Chromium binary via `PUPPETEER_EXECUTABLE_PATH`, common binary names on `$PATH`, and known fixed locations — no manual configuration needed.
- `--standard=` flag for `check-html` and `check-html-all` — supports `WCAG2AA` (default) and `WCAG2AAA` for stricter contrast and other AAA requirements.

---

### [1.4.0] — 2026-04-20

#### Added
- `check-udl <directory>` — Universal Design for Learning format audit. For every standalone `.tex` file in a directory, verifies that a paired `.html` and `.pdf` exist (multiple means of representation), that the `.tex` accessibility notice links to the HTML version, and that the generated HTML links back to the PDF. Supports `--recursive` / `-r` to walk subdirectories and `--output=<path>` to save a Markdown report. Exit code 0 = all compliant, 1 = gaps found.
- Fragment files without `\documentclass` (CV sections, `\input`-only files) are automatically skipped — not reported as failures.
- Jekyll `_site` build directories are excluded from recursive searches in `check-udl`, `check-html-all`, and `check-pdf-all`.
- `--recursive` / `-r` flag added to `check-html-all` and `check-pdf-all` to recurse into subdirectories.
- `pdfdisplaydoctitle=true` and `pdfuapart=1` now added automatically by the `add` command, addressing PDF/UA clause 7.1 (DisplayDocTitle) and clause 5 (PDF/UA conformance declaration). Requires the `hyperxmp` package, which is also added automatically.
- `hyperxmp` package added automatically by `add` — inserts an XMP metadata stream into the PDF, addressing PDF/UA clause 7.1 (missing Metadata stream).

---

### [1.3.0] — 2026-04-19

#### Added
- `check-html <file.html>` — audits a generated HTML file for WCAG 2.1 AA issues using pa11y. Reports violations grouped by severity (critical, serious, moderate, minor). Supports `--output=<path>` to save a Markdown report.
- `check-html-all <directory>` — batch version of `check-html` for all `.html` files in a directory, with per-file progress and a summary.
- `check-pdf <file.pdf>` — audits a generated PDF file for PDF/UA compliance using veraPDF. Parses XML output and reports failures by clause. Supports `--output=<path>` to save a Markdown report.
- `check-pdf-all <directory>` — batch version of `check-pdf` for all `.pdf` files in a directory.
- Both checkers detect missing tools and print clear installation instructions rather than crashing. Exit code 0 = pass, 1 = issues found or tool missing.

---

### [1.2.0] — 2026-04-19

#### Added
- `--help` / `-h` flag — structured help output with a COMMANDS table, FLAGS table, EXAMPLES section, and summaries of what `add` does automatically vs. warns about. Version number is interpolated into the help text automatically. Running with no arguments now shows help instead of an error.

- `wizard` command (also accepts `interactive`) — step-by-step guided mode that asks for file/directory, HTML URL, shows a dry-run preview, and confirms before applying. No extra libraries required. Ctrl-C cancels cleanly at any step. Offers to generate a compliance report at the end (directory mode).
- `--verbose` flag for `add` and `add-all` — prints a detail line for each individual change made per file (packages added, notice added, URLs wrapped, alt text hints added). Compatible with `--plain`.
- `--plain` flag — replaces all emoji status symbols with bracketed text equivalents (`[OK]`, `[SKIP]`, `[WARN]`, `[ERR]`, `[DONE]`) for screen reader users and scripting. Detected before any output so the whole run is consistent.
- LAT1: `add_alt_text_hints()` — automatically inserts `% Alt text: [Add description here for accessibility]` after any `\includegraphics` line that does not already have one. Reports count in dry-run and verbose output.
- LAT2: `check_figure_captions()` — detects `\begin{figure}` environments missing `\caption` and warns with the accurate source-file line number. Advisory only — never modifies files.
- LAT3: `check_table_captions()` — detects `\begin{table}` environments missing `\caption` and warns with the accurate source-file line number. Handles `table*`. Advisory only.
- LAT4: `check_color_only_text()` — detects `\textcolor{}{}` usage where the text has no secondary formatting cue (`\textbf`, `\textit`, `\emph`, `\underline`, `\textsc`, `\textsf`, `\texttt`). Advisory only.
- LAT1–4 results included in `check_file_accessibility()` result dict and rendered in `generate_report()` Markdown output.
- ACC1: All emoji in terminal output audited — added explicit text status words where emoji was the sole indicator of meaning (package install/missing lines, parsed LaTeX error prefix).

#### Fixed
- `add_accessibility_notice()`: `re.sub` replacement string crash when the accessibility notice contains LaTeX backslash commands (e.g. `\section*`, `\url`). Fixed by using a lambda replacement instead of a string, preventing Python from misinterpreting `\s` as a regex escape sequence.
- Advisory checks (`check_figure_captions`, `check_table_captions`, `check_color_only_text`) now run against `original_content` so reported line numbers match the source file, not the post-transformation content.

---

### [1.1.0] — 2026-04-18

#### Added
- `report` command — generates a Markdown accessibility compliance report for a directory, with a summary table, per-file feature checklists, and an action-items section with checkboxes for files that need work.
  - `--format=pdf` converts the report via pandoc (falls back to Markdown with a clear message if pandoc is missing).
  - `--output=<path>` specifies a custom output file path.
- `--dry-run` flag for `add`, `fix`, `add-all`, and `fix-all` — runs all transformations in memory and prints what would change without writing any files.
- `validate` command — compiles a .tex file with `pdflatex -interaction=nonstopmode`, parses the log for errors, reports accessibility feature detection, and cleans up auxiliary files.
- `validate-all` command — runs `validate` across every .tex file in a directory with `[N/total]` per-file progress and a pass/fail/skip summary; exits with code 1 if any file fails.
- `--progress` flag for `add-all` and `fix-all` — enables a compact tqdm progress bar with automatic fallback to verbose output when tqdm is not installed.
- Batch summary statistics for `add-all` and `fix-all`: Modified / Skipped / Errors counts at the end of every run.
- `check-packages` command — detects whether LaTeX is installed, checks for required packages (hyperref, bookmark, enumitem) and optional packages (accessibility), and provides OS-specific installation instructions.

#### Changed
- Error return value in `add_all_features()` and `fix_structure()` is now `None` for errors and `False` for already-compliant, allowing callers to distinguish the two cases in summary counts.
- Hardcoded personal domain replaced with `example.com` placeholder with a clear `# CUSTOMIZE THIS` comment.
- Version flag added: `--version` / `-v`.

---

### [1.0.0] — initial release

- `add` command: adds `bookmark` and `enumitem` packages, `\bookmarksetup{}` configuration, accessibility notice, and `\url{}` wrapping for plain URLs.
- `fix` command: repairs malformed `\hypersetup`/`\bookmarksetup` nesting that causes "TeX capacity exceeded" compilation errors.
- `add-all` / `fix-all` commands: batch versions of `add` and `fix` for a directory of .tex files.

---

## tex-to-html.py

### [1.2.2] — 2026-04-18

#### Changed
- Website and GitHub sections in generated HTML are now commented out (`<!-- ... -->`) instead of showing placeholder values when no URL is found in the source file.

---

### [1.2.1] — 2026-04-18

#### Fixed
- `longtable` environments that span multiple blank-line-separated paragraphs no longer get split apart by the block-splitting preprocessor. Table environments are now extracted into placeholders before splitting and restored afterward.
- Caption lines in longtable output no longer appear as spurious table rows.
- Duplicate header rows from longtable's `\endfirsthead`/`\endhead` sections are deduplicated.

---

### [1.2.0] — 2026-04-18

#### Added
- Full HTML table conversion for `tabular` and `table` LaTeX environments.
  - Proper `<thead>`, `<tbody>`, `<th scope="col">`, `<td>` structure.
  - `\caption{}` support with accessible `<caption>` elements.
  - Header row detection via `\textbf{}`.
  - Responsive `.table-container` wrapper with horizontal scrolling on mobile.
- `longtable` environment support, including `\endfirsthead`, `\endhead`, `\endfoot`, `\endlastfoot` commands.
- Table styles added to `accessible-lab.css`: alternating row colors, hover highlight, dark mode equivalents.

---

### [1.1.0] — 2026-04-18

#### Added
- `\input{}` and `\include{}` expansion: the converter now recursively reads included files before conversion.
  - Handles nested includes (files that include other files).
  - Resolves paths relative to the including file.
  - Detects and warns about circular dependencies.
  - Works with all three backends (custom, pandoc, htlatex).

---

### [1.0.0] — initial release

- Unified converter supporting three backends: custom Python parser (default), pandoc, and htlatex.
- Auto-detects the best available backend; backend can be forced with `--backend=<name>`.
- Generates clean, semantic HTML5 with `<header>`, `<main>`, `<section>` structure.
- ARIA labels (`aria-labelledby`) on each section.
- Links to `accessible-lab.css` for consistent styling.
- Converts lists, figures, and basic inline formatting.
- `--version` flag.

---

## accessible-lab.css

### [1.1.0] — 2026-04-18

#### Added
- Full table styles: `.table-container`, `table`, `caption`, `th`, `td`, `thead th`, alternating `tbody` row colors, hover highlight.
- Dark mode equivalents for all table styles inside `@media (prefers-color-scheme: dark)`.

---

### [1.0.0] — initial release

- Base typography, link styles with WCAG AAA contrast ratios.
- External link indicator (↗) via CSS `::after`.
- Focus-visible keyboard navigation indicators.
- Skip navigation link (`.skip-link`).
- Breadcrumb navigation styles.
- Table of contents (`.toc`) styles.
- Code and monospace block styles.
- Dark mode support (`prefers-color-scheme: dark`).
- High contrast mode support (`prefers-contrast: high`).
- Reduced motion support (`prefers-reduced-motion: reduce`).
- Print styles.
- Mobile responsive breakpoint at 600px.
