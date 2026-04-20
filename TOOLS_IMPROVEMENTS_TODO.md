# Tools Improvement TODO List

Tracking improvements and enhancements for the LaTeX accessibility toolkit.

## Legend
- **Status:** ⏳ Not Started | 🔄 In Progress | ✅ Completed | ❌ Won't Fix
- **Effort:** 🟢 Low (<30 min) | 🟡 Medium (1-3 hours) | 🔴 High (>3 hours)
- **Priority:** ⭐ Quick Win | 🔥 High | 📌 Medium | 💡 Nice-to-Have

---

# 📋 TODO

## 🔥 High Priority Improvements
_Important features that significantly improve the toolkit_

_No open items._

---

## 📌 Medium Priority Improvements
_Useful features that enhance usability_

_No open items._

---

## 💡 Low Priority / Nice-to-Have
_Would be nice but not essential_

### LP3. HTML Conversion Enhancements ⏳
**Effort:** 🔴 High (4+ hours) | **Priority:** 💡 Nice-to-Have

**What it does:**
Improve tex-to-html.py with better math and figure support.

**Why it matters:**
Current HTML converter handles basic content well, but struggles with complex LaTeX.

**Areas to improve:**
- Better math conversion (MathJax rendering)
- Figure/image handling with alt text
- Code block syntax highlighting
- Citation and bibliography support

**How to test:**
Create test .tex files with complex content and verify HTML output.

---

### LP5. Extended LaTeX Environment Support ⏳
**Effort:** 🔴 High (5+ hours) | **Priority:** 💡 Nice-to-Have

**What it does:**
Handle more LaTeX environments and commands for better accessibility.

**Environments to support:**
- Figures with alt text: `\caption{text}` → add alt text hints
- Code listings: proper semantic markup
- Equations: ensure numbered for reference
- Theorems/proofs: proper semantic structure
- Bibliography: accessible citations
- Index: accessible index generation

**How to test:**
Create comprehensive test .tex with all environments, verify proper handling.

---

## 📚 Documentation Improvements
_Making the tools easier to learn and use_

### DOC4. Contributing Guide ⏳
**Effort:** 🟢 Low (30 min) | **Priority:** 💡 Nice-to-Have

**What to create:**
Add CONTRIBUTING.md with:
- How to report issues
- How to suggest improvements
- Code style guidelines
- Testing requirements
- Pull request process

---

## 🧪 Testing Infrastructure
_Ensuring the tools work correctly_

### TEST1. Automated Test Suite ⏳
**Effort:** 🔴 High (4+ hours) | **Priority:** 📌 Medium

**What to create:**
Comprehensive test suite using pytest:

**Unit tests:**
- Test each function in isolation
- Test regex patterns
- Test file detection logic

**Integration tests:**
- Test full add workflow
- Test full fix workflow
- Test batch processing

**Test files:**
- Create sample .tex files with known issues
- Verify fixes are applied correctly
- Test edge cases (empty files, malformed LaTeX, etc.)

**How to run:**
```bash
pip install pytest pytest-cov
pytest tests/
pytest --cov=latex-accessibility tests/
```

---

### TEST2. Regression Test Suite ⏳
**Effort:** 🟡 Medium (1 hour) | **Priority:** 📌 Medium

**What to create:**
Tests for bugs that have been fixed to ensure they don't come back.

**Test cases:**
- Malformed hypersetup/bookmarksetup nesting
- UTF-8 encoding issues
- Files without \maketitle
- Files without hyperref package
- Empty files
- Binary files (should fail gracefully)

---

### TEST3. Cross-Platform Testing ⏳
**Effort:** 🟡 Medium (varies) | **Priority:** 📌 Medium

**What to test:**
Verify tools work on:
- Linux (Ubuntu, Debian, Fedora)
- macOS
- Windows (with Git Bash, PowerShell, WSL)

**What to verify:**
- Python script runs
- File paths work correctly (/ vs \)
- Encoding works (UTF-8)
- LaTeX packages can be detected

---

## 🎯 Performance Improvements
_Making the tools faster_

### PERF1. Cache Compiled Regex Patterns ⏳
**Effort:** 🟢 Low (15 min) | **Priority:** 💡 Nice-to-Have

**What to do:**
Pre-compile regex patterns at module level instead of in functions.

**Why:**
Faster when processing many files.

---

### PERF2. Parallel Processing for Batch Operations ⏳
**Effort:** 🟡 Medium (1-2 hours) | **Priority:** 💡 Nice-to-Have

**What to do:**
Use multiprocessing to process multiple .tex files simultaneously.

**Why:**
Much faster for large directories (50+ files).

**How:**
Use `multiprocessing.Pool` to process files in parallel.

---

# ✅ COMPLETED

## latex-accessibility.py

### HP2. Backup/Restore Functionality ✅ DONE
Added `--backup` flag to `add`, `fix`, `add-all`, and `fix-all`. Creates `file.tex.bak` before writing. Added `restore <file.tex>` command and `list-backups [path]` command.

### MP4. Template System for Notices ✅ DONE
Created `sample-accessible-template.tex` — a fully commented, ready-to-compile LaTeX template demonstrating every accessibility feature the tool adds or checks for (packages, hypersetup, bookmarksetup, links, figures with alt text, tables with captions, color usage). Users copy it as a starting point.

---

## Universal Design

### UDL1. UDL Format Pairing and Cross-Linking Check ✅ DONE
Added `check-udl <directory>` command. For every standalone `.tex` file, verifies a paired `.html` and `.pdf` exist, the `.tex` accessibility notice links to the HTML version, and the HTML links back to the PDF. Supports `--recursive` and `--output=`. Fragment files (no `\documentclass`) and Jekyll `_site` directories are automatically skipped. Documents the UDL principle of multiple means of representation in README.

---

## Output Accessibility Checking

### OAC1. HTML Accessibility Report (`pa11y`) ✅ DONE
Added `check-html <file.html>` and `check-html-all <directory>` commands. Uses pa11y to audit generated HTML for WCAG 2.1 AA compliance. Reports violations by severity, saves optional Markdown report with `--output=`. Detects missing pa11y and prints installation instructions.

### OAC2. PDF Accessibility Report (`veraPDF`) ✅ DONE
Added `check-pdf <file.pdf>` and `check-pdf-all <directory>` commands. Uses veraPDF to audit generated PDFs for PDF/UA compliance. Parses XML output, reports failures by clause, saves optional Markdown report with `--output=`. Detects missing veraPDF and prints installation instructions.

### OAC3. Combined Source + Output Accessibility Report ✅ DONE
`check-html` and `check-pdf` commands each save individual Markdown reports. Both integrate into the full workflow alongside the existing `report` command for source compliance.

---

## latex-accessibility.py

### QW4. Add --help Text with Examples ✅ DONE
Replaced module docstring with structured help: COMMANDS table, FLAGS table, EXAMPLES section, and summaries of what `add` does automatically vs warns about. Running with no arguments now shows help instead of an error. `-h` added as alias for `--help`.

### QW5. Add Troubleshooting Section to README ✅ DONE
Added Troubleshooting section to README.md covering: "TeX capacity exceeded", missing LaTeX packages, permission denied, UTF-8 encoding issues, PDF not updated after changes, file already compliant, and tqdm not installed. Each entry includes the exact error symptom, cause, and fix with example commands.

### LP2. Interactive Mode / Wizard ✅ DONE
Added `wizard` command (also accepts `interactive`). No extra libraries needed — uses built-in `input()`.
Steps: file vs directory → path → HTML URL → dry-run preview → confirm → apply → optional report.
Ctrl-C cancels cleanly at any step.

### ACC1. Better Error Messages for Screen Reader Users ✅ DONE
Audited every emoji use in `latex-accessibility.py` and added explicit text status words where the emoji was the only indicator of meaning.

### ACC2. Verbose Mode for Detailed Output ✅ DONE
Added `--verbose` flag. Lists each change made per file immediately before the summary line.
Works with `add` and `add-all`. Compatible with `--plain` for fully text-based output.

### ACC3. Plain Text Output Mode ✅ DONE
Added `--plain` flag that replaces all emoji status symbols with bracketed text equivalents (`[OK]`, `[SKIP]`, `[WARN]`, `[ERR]`, `[DONE]`). Detected from `sys.argv` before any output so the whole run is consistent.

### LAT1. Better \includegraphics Handling ✅ DONE
Automatically inserts `% Alt text: [Add description here for accessibility]` after any `\includegraphics` line missing one. Count reported in dry-run and verbose output.

### LAT2. Detect Missing Alt Text in Figures ✅ DONE
Detects `\begin{figure}` environments missing `\caption` and warns with accurate source-file line numbers. Advisory only — never modifies files.

### LAT3. Table Accessibility Checks ✅ DONE
Detects `\begin{table}` environments missing `\caption` and warns with accurate source-file line numbers. Handles `table*`. Advisory only.

### LAT4. Detect Color-Only Information ✅ DONE
Detects `\textcolor{}{}` usage where the text has no secondary formatting cue (`\textbf`, `\textit`, `\emph`, `\underline`, `\textsc`, `\textsf`, `\texttt`). Advisory only.

### QW1. Add Version Number to Scripts ✅ DONE
Added `__version__` and `--version` / `-v` flag.

### QW3 + HP3. Batch Processing with Progress and Summary Statistics ✅ DONE
`add-all` and `fix-all` now show per-file progress with `[N/total]` counters and a summary footer. `--progress` flag enables a compact tqdm progress bar with graceful fallback.

### MP1. Dry Run Mode ✅ DONE
Added `--dry-run` flag to `add`, `fix`, `add-all`, and `fix-all`. Runs all transformations in memory, prints what would change, never writes files.

### MP2. Validation and Verification ✅ DONE
Added `validate` and `validate-all` commands. Compiles with `pdflatex -interaction=nonstopmode`, parses the log for errors, checks accessibility features, cleans up auxiliary files.

### LP4. Accessibility Compliance Report ✅ DONE
Added `report` command. Generates a Markdown report with summary table, per-file feature checklists, and action items with checkboxes. Supports `--output=<path>` and `--format=pdf`.

### HP1. LaTeX Package Detection and Installation ✅ DONE
Added `check-packages` command. Detects LaTeX installation, checks required and optional packages, provides OS-specific installation instructions.

---

## tex-to-html.py

### Table Support ✅ DONE
Full HTML table conversion for `tabular`, `table`, and `longtable` environments with proper `<thead>`, `<tbody>`, `<th scope="col">` structure, caption support, and responsive design.

### \input{} and \include{} File Support ✅ DONE
Converter now expands `\input{}` and `\include{}` commands recursively before conversion. Handles nested inputs, circular dependency detection, and all three backends.

### Comment Out Missing Website/GitHub Links ✅ DONE
When no website or GitHub link is found in the .tex file, those HTML sections are commented out instead of showing placeholder values.

### Version Numbers ✅ DONE
Added `__version__` and `--version` flag to tex-to-html.py (v1.2.2).

---

## Documentation

### DOC2. FAQ Section ✅ DONE
Added FAQ section covering: `add` vs `fix`, "already compliant" message, `--dry-run`, `report` command, customising the HTML URL, "TeX capacity exceeded", Windows compatibility.

### DOC3. Expand Examples Section ✅ DONE
Added before/after examples, dry-run preview output, malformed structure fix, compliance report output, and complete end-to-end workflow to documentation.

### DOC5. Changelog ✅ DONE
Created `CHANGELOG.md` in Keep-a-Changelog format covering all three tools.

### QW2. Add Example Section to README ✅ DONE
Added before/after example showing key changes with visual annotations.

---

## General

### Tools Made Generic ✅ DONE
Removed all hardcoded personal information: generic author defaults, `example.com` domain, directory arguments instead of hardcoded paths.
