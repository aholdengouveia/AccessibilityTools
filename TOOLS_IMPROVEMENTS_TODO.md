# Tools Improvement TODO List

Tracking improvements and enhancements for the LaTeX accessibility toolkit.

## Legend
- **Status:** ⏳ Not Started | 🔄 In Progress | ✅ Completed | ❌ Won't Fix
- **Effort:** 🟢 Low (<30 min) | 🟡 Medium (1-3 hours) | 🔴 High (>3 hours)
- **Priority:** ⭐ Quick Win | 🔥 High | 📌 Medium | 💡 Nice-to-Have

---

# 📋 TODO

## ⭐ Quick Wins (Easy, High Impact)
_These can be done quickly and provide immediate value_

### QW4. Add --help Text with Examples ⏳
**Effort:** 🟢 Low (15 min) | **Impact:** Better discoverability

Enhance `--help` output to include common examples for each command.

**How to test:**
```bash
python3 latex-accessibility.py --help
# Should show usage, commands, and examples
```

---

### QW5. Add Troubleshooting Section to README ⏳
**Effort:** 🟢 Low (20 min) | **Impact:** Reduces support questions

Add common issues and solutions:
- "TeX capacity exceeded" error
- "Package not found" errors
- Permission denied errors
- UTF-8 encoding issues

**How to test:** Review section for completeness and clarity.

---

### QW6. Color-Coded Output ⏳
**Effort:** 🟢 Low (30 min) | **Impact:** Easier to scan output

Add color to terminal output:
- ✅ Green for success
- ❌ Red for errors
- ⚠️  Yellow for warnings
- ℹ️  Blue for info

Use colorama library with fallback for Windows compatibility.

**How to test:** Run on Linux/Mac/Windows, verify colors display correctly or fall back gracefully.

---

## 🔥 High Priority Improvements
_Important features that significantly improve the toolkit_

### HP2. Backup/Restore Functionality ⏳
**Effort:** 🟡 Medium (1-2 hours) | **Priority:** 🔥 High

**What it does:**
Automatically create backups before modifying files, with ability to restore if something goes wrong.

**Why it matters:**
Users are nervous about tools modifying their .tex files. Backups provide peace of mind.

**How to implement:**
1. Add `--backup` flag (or make it default?)
2. Copy file to `.bak` before making changes
3. Add `restore` command to revert changes
4. Maybe keep a log of what was backed up when

**How to test:**
```bash
# Modify with backup
python3 latex-accessibility.py add --backup myfile.tex
# Should create myfile.tex.bak

# Restore if needed
python3 latex-accessibility.py restore myfile.tex
# Restores from myfile.tex.bak

# List all backups
python3 latex-accessibility.py list-backups
```

---

---

## 📌 Medium Priority Improvements
_Useful features that enhance usability_

### MP3. Configuration File Support ⏳
**Effort:** 🟡 Medium (2 hours) | **Priority:** 📌 Medium

**What it does:**
Let users customize settings via config file instead of command-line flags.

**Why it matters:**
Easier to maintain consistent settings across a project.

**How to implement:**
1. Support `.latex-accessibility.yaml` or `.latex-accessibility.ini`
2. Look for config in current directory, then home directory
3. Allow customizing:
   - HTML URL pattern
   - Which packages to add
   - Custom accessibility notice text
   - Default backup behavior

**Example config:**
```yaml
# .latex-accessibility.yaml
html_url_pattern: "https://mysite.edu/{parent}/{section}/{filename}.html"
packages:
  - bookmark
  - enumitem
  - accessibility
backup_by_default: true
custom_notice: |
  This document is available in accessible formats at {html_url}
```

**How to test:**
Create config file, run tool, verify settings are used.

---

### MP4. Template System for Notices ⏳
**Effort:** 🟢 Low (45 min) | **Priority:** 📌 Medium

**What it does:**
Let users customize the accessibility notice with templates.

**Why it matters:**
Different institutions may have different wording requirements.

**How to implement:**
1. Create `templates/` directory with default template
2. Support variables: `{html_url}`, `{title}`, `{date}`, `{author}`
3. Look for custom template in project directory
4. Fall back to default if not found

**Template example:**
```latex
\section*{Accessibility}
Accessible version: \url{{html_url}}
Last updated: {date}
```

**How to test:**
Create custom template, run tool, verify custom text is used.

---

## 💡 Low Priority / Nice-to-Have
_Would be nice but not essential_

### LP1. Git Integration ⏳
**Effort:** 🟢 Low (30 min) | **Priority:** 💡 Nice-to-Have

**What it does:**
Automatically commit changes with descriptive message.

**Why it matters:**
Saves time for users who want changes tracked in git.

**How to implement:**
1. Add `--commit` flag
2. Check if directory is a git repo
3. Create commit with message listing modified files
4. Warn if there are uncommitted changes first

**How to test:**
```bash
python3 latex-accessibility.py add-all --commit labs/

# Creates git commit:
# "Add accessibility features to 14 lab files
#
# Modified: shellbasics.tex, shellcond.tex, ..."
```

---

### LP2. Interactive Mode / Wizard ⏳
**Effort:** 🟡 Medium (2 hours) | **Priority:** 💡 Nice-to-Have

**What it does:**
Step-by-step wizard for users who prefer interactive prompts.

**Why it matters:**
Some users prefer guided experience over command-line flags.

**How to implement:**
1. Add `interactive` command
2. Prompt for: file/directory, HTML URL, which features to add
3. Show preview of changes
4. Confirm before applying
5. Use arrow keys for navigation (library: `questionary` or `inquirer`)

**How to test:**
```bash
python3 latex-accessibility.py interactive

# Wizard prompts:
# 1. Select file or directory: [browse]
# 2. HTML URL pattern: [input]
# 3. Features to add: [✓] Packages [✓] Bookmarks [✓] Notice
# 4. Preview changes? [Yes/No]
# 5. Apply changes? [Yes/No]
```

---

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

### DOC1. Quick Start Video Tutorial ⏳
**Effort:** 🔴 High (3+ hours) | **Priority:** 💡 Nice-to-Have

**What to create:**
Short (5-10 min) video showing:
1. Installation and setup
2. Making a single file accessible
3. Batch processing a directory
4. Viewing results

**Where to host:**
YouTube or similar, link from README

---

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

## ♿ Accessibility of the Tools Themselves
_Making the tools accessible to all users_

### ACC1. Better Error Messages for Screen Reader Users ⏳
**Effort:** 🟢 Low (30 min) | **Priority:** 📌 Medium

**What to improve:**
Current messages use emojis (✓, ❌, ○) which may not read well on screen readers.

**How to fix:**
Add text equivalents:
- `✓` → `[SUCCESS]` or `✓ Success:`
- `❌` → `[ERROR]` or `❌ Error:`
- `○` → `[SKIP]` or `○ Skipped:`
- `⚠️` → `[WARNING]` or `⚠️ Warning:`

**How to test:**
Test with screen reader (NVDA, JAWS, VoiceOver) or just ensure text is always present.

---

### ACC2. Verbose Mode for Detailed Output ⏳
**Effort:** 🟢 Low (20 min) | **Priority:** 💡 Nice-to-Have

**What to add:**
Add `--verbose` flag for users who need more detailed output.

**Normal mode:**
```
✓ Added accessibility features to myfile.tex
```

**Verbose mode:**
```
✓ Added accessibility features to myfile.tex
  - Added package: bookmark
  - Added package: enumitem
  - Added bookmarksetup configuration
  - Added accessibility notice
  - Wrapped 3 plain URLs
```

---

### ACC3. Plain Text Output Mode ⏳
**Effort:** 🟢 Low (15 min) | **Priority:** 💡 Nice-to-Have

**What to add:**
Add `--plain` flag to disable all colors and emojis for accessibility or scripting.

**How to implement:**
Set flag that disables colorama colors and replaces emojis with text.

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
# Install pytest
pip install pytest pytest-cov

# Run tests
pytest tests/

# With coverage report
pytest --cov=latex-accessibility tests/

# Should aim for >80% code coverage
```

---

### TEST2. Regression Test Suite ⏳
**Effort:** 🟡 Medium (1 hour) | **Priority:** 📌 Medium

**What to create:**
Tests for bugs that have been fixed to ensure they don't come back.

**Test cases:**
- Malformed hypersetup/bookmarksetup nesting (the big bug we fixed)
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
- Colors work or fallback gracefully

---

## 🔧 Additional LaTeX Features
_Specific LaTeX commands and environments to handle better_

### LAT1. Better \includegraphics Handling ⏳
**Effort:** 🟡 Medium (1-2 hours) | **Priority:** 💡 Nice-to-Have

**What to detect:**
Find `\includegraphics{image.png}` and suggest adding descriptions.

**What to suggest:**
```latex
% Before:
\includegraphics{diagram.png}

% After (suggestion):
\includegraphics{diagram.png}
% Alt text: [Add description here for accessibility]
```

---

### LAT2. Detect Missing Alt Text in Figures ⏳
**Effort:** 🟡 Medium (1 hour) | **Priority:** 💡 Nice-to-Have

**What to check:**
Ensure figures have \caption for accessibility.

**What to report:**
```
⚠️ Warning: Figure on line 42 has no \caption
  Suggestion: Add \caption{Description of figure}
```

---

### LAT3. Table Accessibility Checks ⏳
**Effort:** 🟡 Medium (1-2 hours) | **Priority:** 💡 Nice-to-Have

**What to check:**
- Tables should have \caption
- Consider suggesting header row markup
- Warn about complex tables that may not be accessible

---

### LAT4. Detect Color-Only Information ⏳
**Effort:** 🟡 Medium (1-2 hours) | **Priority:** 💡 Nice-to-Have

**What to detect:**
Use of `\textcolor` without additional cues (bold, italic, markers).

**What to suggest:**
```latex
% Potentially inaccessible:
\textcolor{red}{Important text}

% Better:
\textcolor{red}{\textbf{Important text}} % Also bold
```

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

## tex-to-html.py improvements

### Table Support ✅
Added full HTML table conversion for `tabular`, `table`, and `longtable` environments.
- Proper `<thead>`, `<tbody>`, `<th scope="col">`, `<td>` structure
- Caption support via `\caption{}`
- Header row detection using `\textbf{}`
- `longtable` support including `\endfirsthead`, `\endhead`, `\endfoot`, `\endlastfoot`
- Responsive design with horizontal scrolling, dark mode, alternating row colors
- Table environments protected from block-splitting during preprocessing

### \input{} and \include{} File Support ✅
Converter now expands `\input{}` and `\include{}` commands recursively before conversion.
- Handles nested inputs (files that include other files)
- Resolves paths relative to the including file
- Detects and warns about circular dependencies
- Works with all three backends (custom, pandoc, htlatex)

### Comment Out Missing Website/GitHub Links ✅
When no website or GitHub link is found in the .tex file, those HTML sections are now commented out instead of showing placeholder values.
- With links: renders active `<a>` tags
- Without links: outputs `<!-- ... -->` comments with placeholder text

### Version Numbers ✅ (v1.2.2)
Added `__version__` and `--version` flag to tex-to-html.py.

---

## latex-accessibility.py improvements

### QW1. Add Version Number to Scripts ✅
Added `__version__ = "1.0.0"` and `--version` / `-v` flag support.

**Output:**
```bash
python3 latex-accessibility.py --version
# LaTeX Accessibility Tool v1.0.0
```

### QW3 + HP3. Batch Processing with Progress and Summary Statistics ✅
`add-all` and `fix-all` now show per-file progress with `[N/total]` counters and a summary at the end. An optional `--progress` flag enables a compact tqdm progress bar with graceful fallback when tqdm isn't installed.

**Default verbose output:**
```
Processing 14 file(s) in IntroLinux/labs

[1/14] shellbasics.tex
  ✓ modified
[2/14] shellcond.tex
  ○ already compliant
...
────────────────────────────────────────
✓ Processed 14 file(s)
  Modified:  1
  Skipped:   13 (already compliant)
  Errors:    0
```

**With `--progress` flag (requires `pip install tqdm`):**
```
Processing 14 file(s) in IntroLinux/labs
100%|████████████████| 14/14 [00:01<00:00, 12.3file/s, ○ already compliant]
────────────────────────────────────────
✓ Processed 14 file(s)
  ...
```

**Without tqdm installed, `--progress` falls back gracefully:**
```
⚠️  tqdm not installed — falling back to verbose output.
   To install: pip install tqdm
```

Errors now return `None` (vs `False` for already-compliant) so they're counted separately.

### MP1. Dry Run Mode ✅
Added `--dry-run` flag to `add`, `fix`, `add-all`, and `fix-all` commands.
- Runs all transformations in memory but never writes to disk
- Per-file output lists exactly what would change (which packages, URL wrapping, bookmarksetup, notice)
- Batch summary footer changes from "Processed" to "[DRY RUN] analysed — no files written"
- `Would modify:` counter replaces `Modified:` in the summary

---

### LP4. Accessibility Compliance Report ✅
Added `report` command that analyses all .tex files in a directory and writes a Markdown report.
- Per-file feature checklist: hyperref, bookmark, enumitem, bookmarksetup, accessibility notice
- Summary table (compliant / partial / non-compliant counts)
- Action items section with `- [ ]` checkboxes for files that need fixes
- `--output=<path>` to customise the output file location
- `--format=pdf` converts via pandoc (falls back to Markdown with a clear message if pandoc is missing)
- Default output: `<directory>/accessibility_report.md`

---

### MP2. Validation and Verification ✅
Added `validate` and `validate-all` commands that compile .tex files with pdflatex and report results.
- Runs `pdflatex -interaction=nonstopmode` in the file's directory
- Parses the `.log` file for `!` error lines and `l.N` line numbers
- Checks for accessibility features (hyperref, bookmark, enumitem, bookmarksetup)
- Cleans up auxiliary files (.aux, .log, .out, .toc, .fls, .fdb_latexmk, .synctex.gz)
- `validate-all` shows per-file `[N/total]` progress and summary; exits with code 1 if any file fails
- Returns `None` if pdflatex is not installed (skips gracefully)

---

### HP1. LaTeX Package Detection and Installation ✅
Added `check-packages` command that:
- Detects if LaTeX is installed (checks for kpsewhich)
- Checks for required packages (hyperref, bookmark, enumitem)
- Checks for optional packages (accessibility)
- Detects OS (Ubuntu/Debian, Fedora/RHEL, Mac, Windows, generic Linux)
- Provides OS-specific installation instructions
- Returns exit code 0 for success, 1 for missing packages

---

## General improvements

### DOC2. FAQ Section ✅
Added "Frequently Asked Questions" section to ACCESSIBILITY_README.md covering:
- `add` vs `fix` — when to use each
- "Already compliant" message but PDF still lacks bookmarks — PDF must be regenerated separately
- `--dry-run` — how to preview changes without writing files
- `report` command — how to check a whole directory at once
- Customising the HTML URL pattern
- "TeX capacity exceeded" error — use `fix`
- Windows compatibility

### DOC3. Expand Examples Section ✅
Added "More Examples" section to ACCESSIBILITY_README.md with:
- Dry-run preview (before/after output for compliant and non-compliant files)
- Malformed structure fix — broken vs corrected `\hypersetup`/`\bookmarksetup` layout
- Compliance report — example output and PDF variant
- Complete end-to-end workflow: `--dry-run` → `add` → `validate` → `tex-to-html.py` → `report`

### DOC5. Changelog ✅
Created `CHANGELOG.md` covering all three tools in Keep-a-Changelog format:
- `latex-accessibility.py` v1.0.0 and v1.1.0
- `tex-to-html.py` v1.0.0 through v1.2.2
- `accessible-lab.css` v1.0.0 and v1.1.0

### QW2. Add Example Section to README ✅
Added concise before/after example to ACCESSIBILITY_README.md showing key changes (packages, bookmarks, URL wrapping) with visual annotations.

### Tools Made Generic ✅
Removed all hardcoded personal information from tools:
- tex-to-html.py: generic author defaults, commented-out website/GitHub
- latex-accessibility.py: generic `example.com` domain instead of personal domain
- add-lab-links.py: accepts directory as argument instead of hardcoded path
