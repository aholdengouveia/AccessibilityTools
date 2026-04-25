#!/usr/bin/env python3
r"""LaTeX Accessibility Tool v{version} — make .tex files accessible for PDF and HTML output.

COMMANDS
  wizard                        Step-by-step guided mode (recommended for first-time use)

  add <file.tex>                Add accessibility features to a single file
  add-all <directory>           Add accessibility features to every .tex file in a directory
  fix <file.tex>                Fix structural issues (e.g. bookmarksetup inside hypersetup)
  fix-all <directory>           Fix structural issues in every .tex file in a directory

  restore <file.tex>            Restore a file from its .bak backup
  list-backups [path]           List all .tex.bak backup files (default: current directory)

  validate <file.tex>           Compile with pdflatex and report accessibility features
  validate-all <directory>      Validate every .tex file in a directory

  report <directory>            Generate a Markdown accessibility compliance report
  check-packages                Check whether LaTeX and required packages are installed

  check-html <file.html>        Audit an HTML file for WCAG 2.1 AA issues (requires pa11y)
  check-html-all <directory>    Audit all HTML files in a directory
  check-pdf <file.pdf>          Audit a PDF file for PDF/UA compliance (requires veraPDF)
  check-pdf-all <directory>     Audit all PDF files in a directory
  check-udl <directory>         Check UDL format pairing: every .tex has a paired .html
                                and .pdf, and each format links to the other
  check-links <file.html>       Audit HTML link text for WCAG 2.4.4 / 2.4.9 and Universal
                                Design phrasing issues — no external tools required
  check-links-all <directory>   Audit all HTML files in a directory for link text issues

FLAGS (work with most commands)
  --backup                      Save a .bak copy before modifying any file
  --dry-run                     Show what would change without writing any files
  --verbose                     Print each individual change made per file
  --plain                       Replace emoji with [OK]/[WARN]/[ERR] for screen readers
  --progress                    Show a progress bar for batch operations (requires tqdm)
  --recursive / -r              Recurse into subdirectories (check-html-all, check-pdf-all,
                                check-udl)
  --format=pdf                  Output report as PDF instead of Markdown (requires pandoc)
  --output=<path>               Custom output path for the report file
  --version / -v                Print version and exit
  --help / -h                   Show this help and exit

EXAMPLES
  First time? Use the wizard:
    python3 latex-accessibility.py wizard

  Preview what a file needs (no changes written):
    python3 latex-accessibility.py add mylab.tex --dry-run

  Make a single file accessible (with backup):
    python3 latex-accessibility.py add mylab.tex --backup
    python3 latex-accessibility.py restore mylab.tex   # undo if needed
    python3 latex-accessibility.py list-backups labs/  # see all backups

  Make a single file accessible:
    python3 latex-accessibility.py add mylab.tex

  See exactly what changed, line by line:
    python3 latex-accessibility.py add mylab.tex --verbose

  Fix a file that fails to compile:
    python3 latex-accessibility.py fix mylab.tex

  Process a whole directory (with preview first):
    python3 latex-accessibility.py add-all labs/ --dry-run
    python3 latex-accessibility.py add-all labs/ --verbose

  Check for missing captions, alt text, and color-only issues:
    python3 latex-accessibility.py add mylab.tex --dry-run

  Generate a compliance report for a directory:
    python3 latex-accessibility.py report labs/
    python3 latex-accessibility.py report labs/ --format=pdf

  Verify a file still compiles after changes:
    python3 latex-accessibility.py validate mylab.tex

  Use without emoji (for screen readers or CI scripts):
    python3 latex-accessibility.py add-all labs/ --plain

  Check generated HTML for WCAG accessibility issues:
    python3 latex-accessibility.py check-html myfile.html
    python3 latex-accessibility.py check-html-all labs/

  Check generated PDF for PDF/UA compliance:
    python3 latex-accessibility.py check-pdf myfile.pdf
    python3 latex-accessibility.py check-pdf-all labs/

  Audit HTML link text for WCAG 2.4.4/2.4.9 and Universal Design (no external tools):
    python3 latex-accessibility.py check-links myfile.html
    python3 latex-accessibility.py check-links-all site/ --recursive
    python3 latex-accessibility.py check-links-all site/ --output=link-report.md

WHAT 'add' DOES AUTOMATICALLY
  - Adds \usepackage{{bookmark}} and \usepackage{{enumitem}} if missing
  - Adds \bookmarksetup{{}} configuration for PDF navigation
  - Adds an Accessibility Notice section linking to the HTML version
  - Wraps plain URLs in \url{{}} so they are clickable in the PDF
  - Adds % Alt text: hint comments after \includegraphics lines missing one

WHAT 'add' WARNS ABOUT (requires manual fix in the source file)
  - Figures missing \caption
  - Tables missing \caption
  - \includegraphics without an alt text hint comment
  - \textcolor{{}}{{}} usage with no bold/italic/underline cue (color-only information)

For full documentation see README.md or INSTALL.md.
"""

__version__ = "1.6.0"

import sys
import re
import platform
import subprocess
import shutil
from collections import defaultdict
from datetime import datetime, date
from html.parser import HTMLParser
from pathlib import Path

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# Detect --plain / --verbose early (before any output) so they apply for the whole run
_PLAIN   = '--plain'   in sys.argv
_VERBOSE = '--verbose' in sys.argv

# Status symbols — emoji by default, plain bracketed text with --plain
SYM_OK   = "[OK]"   if _PLAIN else "✓"
SYM_SKIP = "[SKIP]" if _PLAIN else "○"
SYM_WARN = "[WARN]" if _PLAIN else "⚠️ "
SYM_ERR  = "[ERR]"  if _PLAIN else "❌"
SYM_DONE = "[DONE]" if _PLAIN else "✅"


def check_package_installed(package_name):
    """Check if a LaTeX package is installed using kpsewhich"""
    try:
        # kpsewhich is a standard tool that comes with TeX distributions
        # It searches for files in the TeX directory structure
        result = subprocess.run(
            ['kpsewhich', f'{package_name}.sty'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except FileNotFoundError:
        # kpsewhich not found - LaTeX probably not installed
        return None
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None


def detect_os():
    """Detect the operating system"""
    system = platform.system().lower()
    if system == 'linux':
        # Try to detect Linux distribution
        try:
            with open('/etc/os-release', 'r') as f:
                os_info = f.read().lower()
                if 'ubuntu' in os_info or 'debian' in os_info:
                    return 'debian'
                elif 'fedora' in os_info or 'rhel' in os_info or 'centos' in os_info:
                    return 'fedora'
                else:
                    return 'linux'
        except:
            return 'linux'
    elif system == 'darwin':
        return 'mac'
    elif system == 'windows':
        return 'windows'
    else:
        return 'unknown'


def get_installation_command(os_type):
    """Get OS-specific installation commands for LaTeX packages"""
    commands = {
        'debian': {
            'full': 'sudo apt-get install texlive-latex-extra texlive-fonts-recommended',
            'description': 'Ubuntu/Debian'
        },
        'fedora': {
            'full': 'sudo dnf install texlive-scheme-medium',
            'description': 'Fedora/RHEL/CentOS'
        },
        'mac': {
            'full': 'brew install --cask mactex',
            'alt': 'Or download from: https://www.tug.org/mactex/',
            'description': 'macOS'
        },
        'windows': {
            'full': 'Download and install MiKTeX from: https://miktex.org/download',
            'alt': 'Or install TeX Live from: https://www.tug.org/texlive/windows.html',
            'description': 'Windows'
        },
        'linux': {
            'full': 'Install texlive-latex-extra using your package manager',
            'description': 'Linux'
        }
    }
    return commands.get(os_type, commands['linux'])


def check_latex_packages():
    """Check if required LaTeX packages are installed and provide installation instructions"""
    required_packages = ['hyperref', 'bookmark', 'enumitem']
    optional_packages = ['accessibility']

    print("Checking LaTeX installation and packages...\n")

    # Check if kpsewhich exists (indicates LaTeX is installed)
    try:
        subprocess.run(['kpsewhich', '--version'], capture_output=True, timeout=5)
        latex_installed = True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        latex_installed = False

    if not latex_installed:
        print(f"{SYM_ERR} LaTeX does not appear to be installed (kpsewhich not found)")
        print("\nLaTeX is required to generate PDFs from .tex files.")
        os_type = detect_os()
        install_info = get_installation_command(os_type)
        print(f"\nTo install LaTeX on {install_info['description']}:")
        print(f"  {install_info['full']}")
        if 'alt' in install_info:
            print(f"  {install_info['alt']}")
        return False

    print(f"{SYM_OK} LaTeX is installed (kpsewhich found)\n")

    # Check required packages
    missing_packages = []
    installed_packages = []

    print("Required packages:")
    for package in required_packages:
        status = check_package_installed(package)
        if status:
            print(f"  {SYM_OK} {package} — installed")
            installed_packages.append(package)
        else:
            print(f"  {SYM_ERR} {package} — missing")
            missing_packages.append(package)

    # Check optional packages
    print("\nOptional packages:")
    for package in optional_packages:
        status = check_package_installed(package)
        if status:
            print(f"  {SYM_OK} {package} — installed")
            installed_packages.append(package)
        else:
            print(f"  {SYM_SKIP} {package} — not installed (optional)")

    # Provide installation instructions if packages are missing
    if missing_packages:
        print(f"\n{SYM_ERR} Missing {len(missing_packages)} required package(s): {', '.join(missing_packages)}")
        print("\nThese packages are needed for the accessibility features to work.")

        os_type = detect_os()
        install_info = get_installation_command(os_type)

        print(f"\nTo install missing packages on {install_info['description']}:")
        print(f"  {install_info['full']}")
        if 'alt' in install_info:
            print(f"  {install_info['alt']}")

        print("\nAfter installation, run this command again to verify.")
        return False
    else:
        print(f"\n{SYM_DONE} All required packages are installed!")
        print("\nYou're ready to use the LaTeX accessibility tools.")
        return True


def add_accessibility_packages(content):
    """Add accessibility-related packages if missing"""
    modified = False

    # Check for and add hyperxmp package (must come before hyperref for XMP metadata)
    if r'\usepackage{hyperxmp}' not in content:
        pattern = r'(\\usepackage(?:\[.*?\])?\{hyperref\})'
        if re.search(pattern, content):
            content = re.sub(pattern, r'\\usepackage{hyperxmp}\n\1', content)
            modified = True

    # Check for and add bookmark package
    if r'\usepackage{bookmark}' not in content:
        # Find hyperref package and add bookmark after it
        pattern = r'(\\usepackage(?:\[.*?\])?\{hyperref\})'
        if re.search(pattern, content):
            content = re.sub(pattern, r'\1\n\\usepackage{bookmark}', content)
            modified = True

    # Check for and add enumitem package
    if r'\usepackage{enumitem}' not in content:
        # Add after bookmark or hyperref
        if r'\usepackage{bookmark}' in content:
            pattern = r'(\\usepackage\{bookmark\})'
            content = re.sub(pattern, r'\1\n\\usepackage{enumitem}', content)
            modified = True
        elif r'\usepackage{hyperref}' in content:
            pattern = r'(\\usepackage(?:\[.*?\])?\{hyperref\})'
            content = re.sub(pattern, r'\1\n\\usepackage{enumitem}', content)
            modified = True

    return content, modified


def add_pdfdisplaydoctitle(content):
    """Add pdfdisplaydoctitle=true and pdfuapart=1 to \\hypersetup if missing.

    pdfdisplaydoctitle: makes PDF viewers show the document title in the title
    bar instead of the filename — required for PDF/UA clause 7.1.

    pdfuapart=1: tells hyperxmp to stamp the XMP metadata stream with the
    PDF/UA-1 conformance declaration — required for PDF/UA clause 5.
    """
    modified = False
    additions = []

    if 'pdfdisplaydoctitle' not in content:
        additions.append('pdfdisplaydoctitle=true')
    if 'pdfuapart' not in content:
        additions.append('pdfuapart=1')

    if not additions:
        return content, False

    pattern = r'(\\hypersetup\{)'
    if re.search(pattern, content):
        insert = '\n    ' + ',\n    '.join(additions) + ','
        content = re.sub(pattern, r'\1' + insert, content)
        modified = True

    return content, modified


def add_bookmark_configuration(content):
    """Add bookmarksetup and setlist configuration after hypersetup"""
    modified = False

    # Check if already has bookmarksetup
    if r'\bookmarksetup{' in content:
        return content, False

    # Find the end of hypersetup block
    pattern = r'(\\hypersetup\{[^}]*\})'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        bookmark_config = r'''

% Configure PDF bookmarks for navigation
\bookmarksetup{
    numbered,
    open,
}

% Configure list spacing for better accessibility
\setlist{nosep}
'''
        insert_pos = match.end()
        content = content[:insert_pos] + bookmark_config + content[insert_pos:]
        modified = True

    return content, modified


def add_accessibility_notice(content, html_url):
    """Add accessibility notice section after \maketitle"""
    modified = False

    # Check if notice already exists
    if 'Accessibility Notice' in content:
        return content, False

    # Find \maketitle and add notice after it
    pattern = r'(\\maketitle\s*\n)'

    if re.search(pattern, content):
        notice = f'''
\\section*{{Accessibility Notice}}
This document is also available in HTML format at:

\\url{{{html_url}}}

The HTML version provides enhanced accessibility features including keyboard navigation, screen reader support, responsive design, dark mode support, and high contrast options.

'''
        content = re.sub(pattern, lambda m: m.group(1) + '\n' + notice, content)
        modified = True

    return content, modified


def fix_hypersetup_structure(content):
    """Fix hypersetup block that has bookmarksetup incorrectly inside it"""

    # Pattern to find malformed hypersetup blocks where bookmarksetup is inside
    pattern = r'\\hypersetup\{(.*?)\n\n(% Configure PDF bookmarks for navigation.*?\\setlist\{nosep\})\s*\n\s*\n(,\s*\n.*?)\}'

    match = re.search(pattern, content, re.DOTALL)
    if match:
        hypersetup_params_before = match.group(1)  # colorlinks, pdfborder, etc.
        bookmark_section = match.group(2)  # The bookmarksetup and setlist blocks
        hypersetup_params_after = match.group(3)  # Comma + pdftitle, etc.

        # Remove the leading comma from params_after
        hypersetup_params_after = hypersetup_params_after.lstrip(',\n ')

        # Reconstruct hypersetup properly
        fixed_hypersetup = '\\hypersetup{\n' + hypersetup_params_before

        # Add comma if needed between before and after params
        if hypersetup_params_before.strip() and hypersetup_params_after.strip():
            if not hypersetup_params_before.rstrip().endswith(','):
                fixed_hypersetup += ','
            fixed_hypersetup += '\n    ' + hypersetup_params_after
        else:
            fixed_hypersetup += '\n    ' + hypersetup_params_after

        fixed_hypersetup += '\n}'

        # Reconstruct the full content with bookmark section after hypersetup
        new_content = content[:match.start()] + fixed_hypersetup + '\n\n' + bookmark_section + '\n' + content[match.end():]
        return new_content, True

    return content, False


def fix_plain_urls(content):
    r"""Wrap plain http(s) URLs in \url{} commands"""
    lines = content.split('\n')
    fixed_lines = []
    modified = False

    for line in lines:
        # Skip lines that already have \url or \href
        if '\\url' in line or '\\href' in line:
            fixed_lines.append(line)
            continue

        # Find standalone URLs (not already wrapped)
        url_pattern = r'(?<!\\url\{)(?<!\\href\{)(https?://[^\s\)]+)'
        if re.search(url_pattern, line):
            # Wrap URL in \url{}
            new_line = re.sub(url_pattern, r'\\url{\1}', line)
            if new_line != line:
                fixed_lines.append(new_line)
                modified = True
                continue

        fixed_lines.append(line)

    return '\n'.join(fixed_lines), modified


def add_alt_text_hints(content):
    r"""Add % Alt text: hint comments after \includegraphics lines that lack one.

    Only inserts a hint when the very next non-blank line is not already an
    alt text comment.  Returns (new_content, modified, count).
    """
    lines = content.split('\n')
    result = []
    modified = False
    count = 0

    for i, line in enumerate(lines):
        result.append(line)
        # Skip comment lines
        if line.lstrip().startswith('%'):
            continue
        if re.search(r'\\includegraphics', line):
            # Check whether the next non-empty line is already an alt text comment
            already_has_hint = '% Alt text:' in line
            if not already_has_hint:
                for j in range(i + 1, min(i + 4, len(lines))):
                    stripped = lines[j].strip()
                    if stripped:
                        if stripped.startswith('% Alt text:'):
                            already_has_hint = True
                        break
            if not already_has_hint:
                result.append('% Alt text: [Add description here for accessibility]')
                modified = True
                count += 1

    return '\n'.join(result), modified, count


def check_figure_captions(content):
    r"""Find \begin{figure} environments that are missing a \caption.

    Returns a list of 1-based line numbers where caption-less figures begin.
    Handles both figure and figure* environments.
    """
    missing = []
    lines = content.split('\n')
    in_figure = False
    figure_line = None
    has_caption = False

    for i, line in enumerate(lines, 1):
        if re.search(r'\\begin\{figure', line):
            in_figure = True
            figure_line = i
            has_caption = False
        elif re.search(r'\\end\{figure', line):
            if in_figure and not has_caption:
                missing.append(figure_line)
            in_figure = False
            figure_line = None
            has_caption = False
        elif in_figure and re.search(r'\\caption', line):
            has_caption = True

    return missing


def check_color_only_text(content):
    r"""Find \textcolor{}{} where the text has no additional non-color formatting cue.

    Color-only information is inaccessible to users with color vision deficiency.
    Checks for \textbf, \textit, \emph, \underline, \textsc, \textsf, \texttt as cues.

    Returns a list of (line_num, color, snippet) tuples for potentially inaccessible usage.
    """
    issues = []
    lines = content.split('\n')
    color_pattern = re.compile(r'\\textcolor\{([^}]+)\}\{([^}]*)\}')
    cue_pattern = re.compile(r'\\(?:textbf|textit|emph|underline|textsc|textsf|texttt)')

    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith('%'):
            continue
        for m in color_pattern.finditer(line):
            color = m.group(1)
            text = m.group(2)
            if not cue_pattern.search(text):
                snippet = m.group(0)
                if len(snippet) > 60:
                    snippet = snippet[:57] + '...'
                issues.append((i, color, snippet))

    return issues


def check_table_captions(content):
    r"""Find \begin{table} environments that are missing a \caption.

    Returns a list of 1-based line numbers where caption-less tables begin.
    Handles both table and table* environments.
    """
    missing = []
    lines = content.split('\n')
    in_table = False
    table_line = None
    has_caption = False

    for i, line in enumerate(lines, 1):
        if re.search(r'\\begin\{table', line):
            in_table = True
            table_line = i
            has_caption = False
        elif re.search(r'\\end\{table', line):
            if in_table and not has_caption:
                missing.append(table_line)
            in_table = False
            table_line = None
            has_caption = False
        elif in_table and re.search(r'\\caption', line):
            has_caption = True

    return missing


def add_all_features(tex_file, html_url=None, dry_run=False, verbose=False, backup=False):
    """Add all accessibility features to a .tex file.

    When dry_run=True the file is never written; instead a summary of what
    would change is printed.  When verbose=True, a detail line is printed for
    each change made.  Return values are the same as the normal path:
    True = would/did modify, False = already compliant, None = error.
    """
    try:
        with open(tex_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
    except UnicodeDecodeError:
        print(f"{SYM_ERR} Error: File {tex_file} is not valid UTF-8 text")
        print("   Suggestion: Check if this is a binary file or has encoding issues")
        return None
    except Exception as e:
        print(f"{SYM_ERR} Error reading {tex_file}: {e}")
        return None

    # Auto-generate HTML URL if not provided
    if not html_url:
        file_path = Path(tex_file)
        parts = file_path.parts
        if len(parts) >= 2:
            section = parts[-2]
            parent  = parts[-3] if len(parts) >= 3 else "unknown"
            filename = file_path.stem
            # CUSTOMIZE THIS: Change "example.com" to your domain
            html_url = f"https://example.com/{parent}/{section}/{filename}.html"

    # Run all transformations in memory (always — dry-run or not)
    content = original_content
    content, pkg_modified      = add_accessibility_packages(content)
    content, doctitle_modified = add_pdfdisplaydoctitle(content)
    content, url_modified      = fix_plain_urls(content)
    content, bookmark_modified = add_bookmark_configuration(content)
    if html_url:
        content, notice_modified = add_accessibility_notice(content, html_url)
    else:
        notice_modified = False
    content, alt_modified, alt_count = add_alt_text_hints(content)

    modified = pkg_modified or doctitle_modified or url_modified or bookmark_modified or notice_modified or alt_modified

    # Advisory checks — never block or modify, run on original_content for accurate line numbers
    caption_issues = check_figure_captions(original_content)
    table_caption_issues = check_table_captions(original_content)
    color_issues = check_color_only_text(original_content)

    if dry_run:
        if modified:
            changes = []
            if pkg_modified:
                pkgs = []
                if '\\usepackage{hyperxmp}' not in original_content:
                    pkgs.append('hyperxmp')
                if '\\usepackage{bookmark}' not in original_content:
                    pkgs.append('bookmark')
                if '\\usepackage{enumitem}' not in original_content:
                    pkgs.append('enumitem')
                if pkgs:
                    changes.append(f'add package(s): {", ".join(pkgs)}')
            if doctitle_modified:
                changes.append('add pdfdisplaydoctitle=true and pdfuapart=1 to \\hypersetup')
            if url_modified:
                changes.append('wrap plain URLs in \\url{}')
            if bookmark_modified:
                changes.append('add \\bookmarksetup{} configuration')
            if notice_modified:
                changes.append('add accessibility notice section')
            if alt_modified:
                changes.append(f'add alt text hint comment to {alt_count} \\includegraphics instance(s)')
            print(f"[DRY RUN] {Path(tex_file).name} — {len(changes)} change(s) would be made:")
            for change in changes:
                print(f"  + {change}")
        else:
            print(f"[DRY RUN] {Path(tex_file).name} — no changes needed (already compliant)")
        for line_num in caption_issues:
            print(f"  {SYM_WARN} Figure on line {line_num} has no \\caption — add a description for accessibility")
        for line_num in table_caption_issues:
            print(f"  {SYM_WARN} Table on line {line_num} has no \\caption — add a description for accessibility")
        for line_num, color, snippet in color_issues:
            print(f"  {SYM_WARN} Color-only text on line {line_num} (\\textcolor{{{color}}}{{...}}) — add \\textbf, \\textit, or other cue for colorblind accessibility")
        return True if modified else False

    # Write changes to disk
    if modified:
        if backup:
            _backup_file(tex_file)
        try:
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(content)
            if verbose:
                if pkg_modified:
                    pkgs = []
                    if '\\usepackage{hyperxmp}' not in original_content:
                        pkgs.append('hyperxmp')
                    if '\\usepackage{bookmark}' not in original_content:
                        pkgs.append('bookmark')
                    if '\\usepackage{enumitem}' not in original_content:
                        pkgs.append('enumitem')
                    for pkg in pkgs:
                        print(f"  - Added package: {pkg}")
                if doctitle_modified:
                    print(f"  - Added pdfdisplaydoctitle=true and pdfuapart=1 to \\hypersetup")
                if url_modified:
                    print(f"  - Wrapped plain URLs in \\url{{}}")
                if bookmark_modified:
                    print(f"  - Added \\bookmarksetup{{}} configuration")
                if notice_modified:
                    print(f"  - Added accessibility notice section")
                if alt_modified:
                    print(f"  - Added alt text hint to {alt_count} \\includegraphics instance(s)")
            for line_num in caption_issues:
                print(f"  {SYM_WARN} Figure on line {line_num} has no \\caption — add a description for accessibility")
            for line_num in table_caption_issues:
                print(f"  {SYM_WARN} Table on line {line_num} has no \\caption — add a description for accessibility")
            for line_num, color, snippet in color_issues:
                print(f"  {SYM_WARN} Color-only text on line {line_num} (\\textcolor{{{color}}}{{...}}) — add \\textbf, \\textit, or other cue for colorblind accessibility")
            return True
        except PermissionError:
            print(f"{SYM_ERR} Error: Permission denied writing to {tex_file}")
            print("   Suggestion: Check file permissions or run with appropriate privileges")
            return None
        except Exception as e:
            print(f"{SYM_ERR} Error writing to {tex_file}: {e}")
            return None

    for line_num in caption_issues:
        print(f"  {SYM_WARN} Figure on line {line_num} has no \\caption — add a description for accessibility")
    for line_num in table_caption_issues:
        print(f"  {SYM_WARN} Table on line {line_num} has no \\caption — add a description for accessibility")
    for line_num, color, snippet in color_issues:
        print(f"  {SYM_WARN} Color-only text on line {line_num} (\\textcolor{{{color}}}{{...}}) — add \\textbf, \\textit, or other cue for colorblind accessibility")
    return False


def _backup_file(tex_path):
    """Copy tex_path to tex_path.bak. Returns backup Path or None on failure."""
    src = Path(tex_path)
    bak = src.with_suffix(src.suffix + '.bak')
    try:
        shutil.copy2(str(src), str(bak))
        print(f"  {SYM_OK} Backup created: {bak.name}")
        return bak
    except Exception as e:
        print(f"{SYM_ERR} Could not create backup for {src.name}: {e}")
        return None


def restore_file(tex_file):
    """Restore a .tex file from its .bak backup.

    Returns True on success, False if backup not found, None on error.
    """
    src = Path(tex_file)
    bak = src.with_suffix(src.suffix + '.bak')
    if not bak.exists():
        print(f"{SYM_ERR} No backup found: {bak}")
        print(f"   Run 'add --backup' or 'fix --backup' to create a backup first.")
        return False
    try:
        shutil.copy2(str(bak), str(src))
        print(f"{SYM_OK} Restored {src.name} from {bak.name}")
        return True
    except Exception as e:
        print(f"{SYM_ERR} Error restoring {src.name}: {e}")
        return None


def list_backups(path):
    """List all .tex.bak files under path (file or directory).

    Returns list of Path objects found.
    """
    p = Path(path)
    if p.is_file():
        candidates = [p.with_suffix(p.suffix + '.bak')]
    else:
        candidates = sorted(p.rglob('*.tex.bak'))

    found = [c for c in candidates if c.exists()]
    if not found:
        print(f"No .tex.bak backup files found in {path}")
        return []

    print(f"Found {len(found)} backup file(s):")
    from datetime import datetime as _dt
    import os as _os
    for bak in found:
        mtime = _dt.fromtimestamp(bak.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
        size  = bak.stat().st_size
        print(f"  {bak}  ({size} bytes, {mtime})")
    return found


def fix_structure(tex_file, dry_run=False, backup=False):
    """Fix structural issues in a .tex file.

    When dry_run=True the file is never written; instead a summary of what
    would change is printed.
    """
    try:
        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"{SYM_ERR} Error reading {tex_file}: {e}")
        return None

    content, modified = fix_hypersetup_structure(content)

    if dry_run:
        if modified:
            print(f"[DRY RUN] {Path(tex_file).name} — would fix hypersetup/bookmarksetup structure")
        else:
            print(f"[DRY RUN] {Path(tex_file).name} — no structural issues found")
        return True if modified else False

    if modified:
        if backup:
            _backup_file(tex_file)
        try:
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"{SYM_ERR} Error writing to {tex_file}: {e}")
            return None

    return False


def validate_file(tex_file):
    """
    Validate that a .tex file compiles correctly with pdflatex.

    Runs pdflatex in nonstopmode, parses the log for errors, reports
    results, checks for accessibility features, then cleans up aux files.

    Returns:
        True  - compiled successfully
        False - compilation failed
        None  - pdflatex not available
    """
    tex_path = Path(tex_file)

    # Check pdflatex is available
    if not subprocess.run(['which', 'pdflatex'], capture_output=True).returncode == 0:
        print(f"{SYM_ERR} pdflatex not found — cannot validate")
        print(f"   Install LaTeX to enable validation")
        return None

    print(f"Compiling {tex_path.name}...")

    try:
        result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', str(tex_path.name)],
            cwd=tex_path.parent,
            capture_output=True,
            text=True,
            timeout=120
        )
        success = result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"{SYM_ERR} pdflatex timed out (>120 seconds)")
        return False
    except Exception as e:
        print(f"{SYM_ERR} Error running pdflatex: {e}")
        return False

    # Parse the .log file for errors and warnings before cleaning up
    log_file = tex_path.with_suffix('.log')
    errors = []
    warnings = []

    if log_file.exists():
        try:
            with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                log_lines = f.readlines()

            i = 0
            while i < len(log_lines):
                line = log_lines[i]
                # Errors start with "!"
                if line.startswith('!'):
                    error_msg = line[1:].strip()
                    line_num = None
                    # The line number follows on a "l.N" line nearby
                    for j in range(i + 1, min(i + 6, len(log_lines))):
                        line_match = re.match(r'l\.(\d+)', log_lines[j])
                        if line_match:
                            line_num = line_match.group(1)
                            break
                    errors.append((error_msg, line_num))
                # Overfull/underfull hbox warnings
                elif line.startswith('Overfull') or line.startswith('Underfull'):
                    warnings.append(line.strip())
                i += 1
        except Exception:
            pass  # Log parse failure is non-fatal

    # Report compilation result
    pdf_file = tex_path.with_suffix('.pdf')

    if success and pdf_file.exists():
        print(f"{SYM_OK} Compiled successfully — {pdf_file.name} generated")

        # Check for accessibility features in the source
        try:
            with open(tex_file, 'r', encoding='utf-8') as f:
                content = f.read()
            has_hyperref = bool(re.search(r'\\usepackage.*\{hyperref\}', content))
            has_bookmark = '\\usepackage{bookmark}' in content
            has_enumitem = '\\usepackage{enumitem}' in content
            has_bookmarksetup = '\\bookmarksetup{' in content

            features = []
            missing = []
            if has_hyperref:
                features.append('hyperref')
            else:
                missing.append('hyperref')
            if has_bookmark:
                features.append('bookmark')
            else:
                missing.append('bookmark')
            if has_enumitem:
                features.append('enumitem')
            if has_bookmarksetup:
                features.append('bookmarksetup')

            if features:
                print(f"{SYM_OK} Accessibility packages: {', '.join(features)}")
            if missing:
                print(f"{SYM_WARN} Missing accessibility packages: {', '.join(missing)}")
                print(f"   Run: python3 latex-accessibility.py add {tex_file}")
        except Exception:
            pass  # Accessibility check failure is non-fatal

        if warnings:
            print(f"{SYM_WARN} {len(warnings)} layout warning(s) (overfull/underfull boxes)")

    else:
        print(f"{SYM_ERR} Compilation failed")
        if errors:
            print(f"\n  Errors:")
            for msg, line_num in errors:
                location = f"line {line_num}: " if line_num else ""
                print(f"  {SYM_ERR} Error: {location}{msg}")
        else:
            # No errors parsed but still failed — show raw pdflatex stderr
            if result.stderr.strip():
                print(f"\n  Output:\n  {result.stderr.strip()[:400]}")

        # Remove any incomplete PDF left behind
        if pdf_file.exists():
            pdf_file.unlink()

    # Clean up auxiliary files (keep the PDF on success)
    for ext in ['.aux', '.log', '.out', '.toc', '.fls', '.fdb_latexmk', '.synctex.gz']:
        aux = tex_path.with_suffix(ext)
        if aux.exists():
            aux.unlink()

    return success


def check_file_accessibility(tex_file):
    """
    Inspect a .tex file for accessibility features without modifying it.

    Returns a dict with per-feature booleans, a list of issues, and a
    'readable' flag set to False if the file could not be opened.
    """
    result = {
        'file': Path(tex_file).name,
        'path': str(tex_file),
        'has_hyperref': False,
        'has_bookmark': False,
        'has_enumitem': False,
        'has_bookmarksetup': False,
        'has_notice': False,
        'has_accessibility_pkg': False,
        'figures_without_caption': [],   # LAT2: line numbers
        'tables_without_caption': [],    # LAT3: line numbers
        'color_only_text': [],           # LAT4: (line_num, color, snippet) tuples
        'graphics_without_hint': 0,      # LAT1: count
        'issues': [],
        'readable': True,
    }

    try:
        with open(tex_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        result['readable'] = False
        result['issues'].append(f"Could not read file: {e}")
        return result

    result['has_hyperref'] = bool(re.search(r'\\usepackage.*\{hyperref\}', content))
    result['has_bookmark'] = '\\usepackage{bookmark}' in content
    result['has_enumitem'] = '\\usepackage{enumitem}' in content
    result['has_bookmarksetup'] = '\\bookmarksetup{' in content
    result['has_notice'] = 'Accessibility Notice' in content
    result['has_accessibility_pkg'] = '\\usepackage{accessibility}' in content

    # LAT1: count \includegraphics without an alt text hint comment
    _, _, graphics_without_hint = add_alt_text_hints(content)
    result['graphics_without_hint'] = graphics_without_hint

    # LAT2: figure environments missing \caption
    result['figures_without_caption'] = check_figure_captions(content)

    # LAT3: table environments missing \caption
    result['tables_without_caption'] = check_table_captions(content)

    # LAT4: color-only text without additional formatting cue
    result['color_only_text'] = check_color_only_text(content)

    if not result['has_hyperref']:
        result['issues'].append('Missing `\\usepackage{hyperref}`')
    if not result['has_bookmark']:
        result['issues'].append('Missing `\\usepackage{bookmark}`')
    if not result['has_enumitem']:
        result['issues'].append('Missing `\\usepackage{enumitem}`')
    if not result['has_bookmarksetup']:
        result['issues'].append('Missing `\\bookmarksetup{}` configuration')
    if not result['has_notice']:
        result['issues'].append('Missing accessibility notice section')

    return result


def _compliance_level(file_result):
    """Return 'compliant', 'partial', or 'non-compliant' for a file result dict."""
    required = ['has_hyperref', 'has_bookmark', 'has_enumitem', 'has_bookmarksetup', 'has_notice']
    met = sum(1 for key in required if file_result.get(key))
    if met == len(required):
        return 'compliant'
    elif met >= 3:
        return 'partial'
    else:
        return 'non-compliant'


def _find_pa11y():
    """Return the pa11y executable path, or None if not found."""
    for candidate in ['pa11y', 'npx pa11y']:
        result = subprocess.run(
            ['which', candidate.split()[0]], capture_output=True
        )
        if result.returncode == 0:
            return candidate
    return None


def _find_verapdf():
    """Return the verapdf executable path, or None if not found."""
    result = subprocess.run(['which', 'verapdf'], capture_output=True)
    if result.returncode == 0:
        return 'verapdf'
    return None


def _find_chrome():
    """Return the path to a Chrome/Chromium executable, or None if not found."""
    import os
    # 1. Honour explicit env var
    env_path = os.environ.get('PUPPETEER_EXECUTABLE_PATH')
    if env_path and Path(env_path).exists():
        return env_path
    # 2. Try common binary names on PATH
    for name in ('google-chrome', 'google-chrome-stable', 'chromium-browser', 'chromium'):
        found = shutil.which(name)
        if found:
            return found
    # 3. Common fixed locations on Linux/macOS
    for fixed in ('/usr/bin/google-chrome', '/usr/bin/chromium-browser',
                  '/snap/bin/chromium', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'):
        if Path(fixed).exists():
            return fixed
    return None


def check_html_accessibility(html_file, report_file=None, standard='WCAG2AA'):
    """
    Run a WCAG accessibility audit on an HTML file using pa11y.

    standard: pa11y --standard value, e.g. 'WCAG2AA' or 'WCAG2AAA'.

    Returns a dict with keys: file, tool, standard, critical, serious, moderate, minor,
    issues (list of dicts), tool_missing (bool), error (str or None).
    Writes a Markdown report to report_file if provided.
    """
    html_path = Path(html_file)
    result = {
        'file': html_path.name,
        'path': str(html_path),
        'tool': 'pa11y',
        'standard': standard,
        'critical': 0, 'serious': 0, 'moderate': 0, 'minor': 0,
        'issues': [],
        'tool_missing': False,
        'error': None,
    }

    pa11y = _find_pa11y()
    if not pa11y:
        result['tool_missing'] = True
        result['error'] = 'pa11y not found'
        print(f"{SYM_ERR} pa11y is not installed — cannot check HTML accessibility")
        print(f"   Install with: npm install -g pa11y")
        print(f"   (requires Node.js — https://nodejs.org)")
        return result

    if not html_path.exists():
        result['error'] = f"File not found: {html_file}"
        print(f"{SYM_ERR} File not found: {html_file}")
        return result

    standard_label = 'WCAG 2.1 AAA' if standard == 'WCAG2AAA' else 'WCAG 2.1 AA'
    print(f"Checking {html_path.name} for {standard_label} compliance (pa11y)...")

    chrome = _find_chrome()
    import os
    env = os.environ.copy()
    if chrome:
        env['PUPPETEER_EXECUTABLE_PATH'] = chrome

    try:
        proc = subprocess.run(
            [pa11y, '--reporter', 'json', '--standard', standard, str(html_path)],
            capture_output=True, text=True, timeout=60, env=env
        )
        import json
        raw = proc.stdout.strip()
        if not raw:
            raw = '[]'
        issues = json.loads(raw)
    except subprocess.TimeoutExpired:
        result['error'] = 'pa11y timed out'
        print(f"{SYM_ERR} pa11y timed out after 60 seconds")
        return result
    except Exception as e:
        result['error'] = str(e)
        print(f"{SYM_ERR} Error running pa11y: {e}")
        return result

    severity_map = {'error': 'critical', 'warning': 'moderate', 'notice': 'minor'}
    for issue in issues:
        severity = severity_map.get(issue.get('type', ''), 'minor')
        result[severity] += 1
        result['issues'].append({
            'severity': severity,
            'message': issue.get('message', ''),
            'selector': issue.get('selector', ''),
            'context': issue.get('context', ''),
        })

    total = len(issues)
    if result['critical'] == 0 and result['serious'] == 0:
        print(f"  {SYM_OK} No critical or serious issues ({total} total)")
    else:
        if result['critical']:
            print(f"  {SYM_ERR} {result['critical']} critical issue(s)")
        if result['serious']:
            print(f"  {SYM_WARN} {result['serious']} serious issue(s)")
        if result['moderate']:
            print(f"  {SYM_WARN} {result['moderate']} moderate issue(s)")
        if result['minor']:
            print(f"  {SYM_SKIP} {result['minor']} minor issue(s)")

    for issue in result['issues']:
        sev = issue['severity'].upper()
        print(f"    [{sev}] {issue['message']}")
        if issue.get('selector'):
            print(f"           Selector: {issue['selector']}")

    if report_file:
        _write_html_report(result, report_file)

    return result


def _write_html_report(result, report_file):
    """Write an HTML accessibility check result to a Markdown file."""
    standard = result.get('standard', 'WCAG2AA')
    standard_label = 'WCAG 2.1 AAA' if standard == 'WCAG2AAA' else 'WCAG 2.1 AA'
    lines = [
        f"# HTML Accessibility Report: {result['file']}",
        '',
        f"**Tool:** pa11y ({standard_label})  ",
        f"**File:** `{result['path']}`  ",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        '',
        '## Summary',
        '',
        f"| Severity | Count |",
        f"|----------|-------|",
        f"| Critical | {result['critical']} |",
        f"| Serious  | {result['serious']} |",
        f"| Moderate | {result['moderate']} |",
        f"| Minor    | {result['minor']} |",
        '',
    ]
    if result['issues']:
        lines += ['## Issues', '']
        for issue in result['issues']:
            lines.append(f"**[{issue['severity'].upper()}]** {issue['message']}")
            if issue.get('selector'):
                lines.append(f"- Selector: `{issue['selector']}`")
            if issue.get('context'):
                lines.append(f"- Context: `{issue['context'][:120]}`")
            lines.append('')
    else:
        lines += ['## Issues', '', '✅ No issues found.', '']

    Path(report_file).write_text('\n'.join(lines), encoding='utf-8')
    print(f"  {SYM_DONE} Report saved: {report_file}")


def check_udl_directory(directory, recursive=False, report_file=None):
    """Check a directory for Universal Design for Learning (UDL) compliance.

    For each .tex source file, verifies:
      1. A paired .html file exists (multiple means of representation)
      2. A paired .pdf file exists
      3. The .tex accessibility notice links to the .html version
      4. The .html file links back to the .pdf version
      5. The linked filenames are consistent (no broken cross-references)

    Returns a dict with keys: total, passed, issues (list of dicts).
    """
    directory = Path(directory)
    glob_fn = directory.rglob if recursive else directory.glob

    all_tex = sorted(t for t in glob_fn('*.tex') if '_site' not in t.parts)
    # Skip fragment files — standalone labs always have \documentclass,
    # section fragments (\input'd into a parent) do not.
    tex_files = []
    skipped_fragments = []
    for t in all_tex:
        try:
            head = t.read_text(encoding='utf-8', errors='ignore')[:500]
            if '\\documentclass' in head:
                tex_files.append(t)
            else:
                skipped_fragments.append(t.name)
        except Exception:
            skipped_fragments.append(t.name)

    if not tex_files:
        print(f"No standalone .tex files found (skipped {len(skipped_fragments)} fragment(s))")
        return {'total': 0, 'passed': 0, 'issues': []}

    if skipped_fragments:
        print(f"  (skipping {len(skipped_fragments)} fragment file(s) without \\documentclass)\n")

    results = []

    for tex_path in tex_files:
        stem = tex_path.stem
        html_path = tex_path.with_suffix('.html')
        pdf_path  = tex_path.with_suffix('.pdf')
        file_issues = []

        # 1. Paired HTML exists
        if not html_path.exists():
            file_issues.append({
                'check': 'paired-html',
                'severity': 'error',
                'message': f"No HTML version found — expected {html_path.name}",
            })

        # 2. Paired PDF exists
        if not pdf_path.exists():
            file_issues.append({
                'check': 'paired-pdf',
                'severity': 'error',
                'message': f"No PDF version found — expected {pdf_path.name}",
            })

        # 3. .tex accessibility notice links to the .html
        try:
            tex_content = tex_path.read_text(encoding='utf-8')
            # Look for any URL containing the stem and .html in the body
            body = tex_content.split('\\begin{document}', 1)[-1] if '\\begin{document}' in tex_content else tex_content
            html_link_in_tex = bool(re.search(
                re.escape(stem) + r'\.html', body
            ))
            if not html_link_in_tex:
                file_issues.append({
                    'check': 'tex-links-html',
                    'severity': 'warning',
                    'message': f"Accessibility notice in {tex_path.name} does not appear to link to {stem}.html",
                })
        except Exception:
            pass

        # 4 & 5. .html links back to .pdf with correct filename
        if html_path.exists():
            try:
                html_content = html_path.read_text(encoding='utf-8')
                # Check for a link whose href is exactly the pdf filename
                pdf_link_pattern = re.compile(
                    r'href=["\']' + re.escape(pdf_path.name) + r'["\']', re.IGNORECASE
                )
                if not pdf_link_pattern.search(html_content):
                    # Also accept full-path references
                    if pdf_path.name not in html_content:
                        file_issues.append({
                            'check': 'html-links-pdf',
                            'severity': 'warning',
                            'message': f"{html_path.name} does not link back to {pdf_path.name}",
                        })
            except Exception:
                pass

        results.append({
            'file': stem,
            'tex': str(tex_path),
            'issues': file_issues,
        })

    total  = len(results)
    passed = sum(1 for r in results if not r['issues'])
    all_issues = [
        dict(file=r['file'], **issue)
        for r in results for issue in r['issues']
    ]

    # Print results
    for r in results:
        if r['issues']:
            print(f"  {SYM_WARN} {r['file']}")
            for issue in r['issues']:
                sym = SYM_ERR if issue['severity'] == 'error' else SYM_WARN
                print(f"    {sym} [{issue['check']}] {issue['message']}")
        else:
            print(f"  {SYM_OK} {r['file']} — HTML + PDF paired and cross-linked")

    print()
    print('─' * 50)
    errors   = sum(1 for i in all_issues if i['severity'] == 'error')
    warnings = sum(1 for i in all_issues if i['severity'] == 'warning')
    print(f"{SYM_DONE} Checked {total} .tex file(s): {passed} fully compliant")
    if errors:
        print(f"  {SYM_ERR} {errors} error(s) — missing paired format file(s)")
    if warnings:
        print(f"  {SYM_WARN} {warnings} warning(s) — cross-linking gaps")

    if report_file:
        lines = [
            '# UDL Format & Cross-Linking Report',
            '',
            f'**Directory:** `{directory}`  ',
            f'**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}  ',
            f'**Scope:** {"recursive" if recursive else "single directory"}',
            '',
            '## Summary',
            '',
            f'| Check | Count |',
            f'|-------|-------|',
            f'| .tex files checked | {total} |',
            f'| Fully compliant | {passed} |',
            f'| Errors (missing files) | {errors} |',
            f'| Warnings (linking gaps) | {warnings} |',
            '',
            '## Results',
            '',
        ]
        for r in results:
            if r['issues']:
                lines.append(f"### ❌ {r['file']}")
                for issue in r['issues']:
                    marker = '🔴' if issue['severity'] == 'error' else '🟡'
                    lines.append(f"- {marker} **{issue['check']}**: {issue['message']}")
            else:
                lines.append(f"### ✅ {r['file']}")
                lines.append("- Paired HTML and PDF present")
                lines.append("- PDF links to HTML, HTML links to PDF")
            lines.append('')
        Path(report_file).write_text('\n'.join(lines), encoding='utf-8')
        print(f"  {SYM_DONE} Report saved: {report_file}")

    return {'total': total, 'passed': passed, 'issues': all_issues}


def check_pdf_accessibility(pdf_file, report_file=None):
    """
    Run a PDF/UA accessibility audit on a PDF file using veraPDF.

    Returns a dict with keys: file, tool, passed, failed, warnings,
    failures (list of dicts), tool_missing (bool), error (str or None).
    Writes a Markdown report to report_file if provided.
    """
    pdf_path = Path(pdf_file)
    result = {
        'file': pdf_path.name,
        'path': str(pdf_path),
        'tool': 'veraPDF',
        'passed': 0, 'failed': 0, 'warnings': 0,
        'failures': [],
        'tool_missing': False,
        'error': None,
    }

    verapdf = _find_verapdf()
    if not verapdf:
        result['tool_missing'] = True
        result['error'] = 'veraPDF not found'
        print(f"{SYM_ERR} veraPDF is not installed — cannot check PDF accessibility")
        print(f"   Download from: https://github.com/veraPDF/veraPDF-apps/releases/latest")
        print(f"   (requires Java — install with: sudo apt-get install default-jre)")
        return result

    if not pdf_path.exists():
        result['error'] = f"File not found: {pdf_file}"
        print(f"{SYM_ERR} File not found: {pdf_file}")
        return result

    print(f"Checking {pdf_path.name} for PDF/UA compliance (veraPDF)...")

    try:
        proc = subprocess.run(
            [verapdf, '--flavour', 'ua1', '--format', 'xml', str(pdf_path)],
            capture_output=True, text=True, timeout=120
        )
        xml_output = proc.stdout
    except subprocess.TimeoutExpired:
        result['error'] = 'veraPDF timed out'
        print(f"{SYM_ERR} veraPDF timed out after 120 seconds")
        return result
    except Exception as e:
        result['error'] = str(e)
        print(f"{SYM_ERR} Error running veraPDF: {e}")
        return result

    # Parse XML output
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_output)

        # Summary counts are on the <details> element inside <validationReport>
        details = root.find('.//validationReport/details')
        if details is not None:
            result['passed'] = int(details.get('passedRules', 0))
            result['failed'] = int(details.get('failedRules', 0))

        # Collect individual failed rules; description is a child element
        for rule in root.iter('rule'):
            if rule.get('status') == 'failed':
                desc_el = rule.find('description')
                description = desc_el.text.strip() if desc_el is not None and desc_el.text else ''
                result['failures'].append({
                    'clause': rule.get('clause', ''),
                    'test_number': rule.get('testNumber', ''),
                    'description': description,
                    'count': int(rule.get('failedChecks', 1)),
                })
    except Exception as e:
        result['error'] = f"Could not parse veraPDF output: {e}"
        print(f"{SYM_ERR} Could not parse veraPDF output: {e}")
        return result

    if result['failed'] == 0:
        print(f"  {SYM_OK} PDF/UA compliant — {result['passed']} rule(s) passed")
    else:
        print(f"  {SYM_ERR} {result['failed']} failure(s), {result['passed']} passed")
        for f in result['failures']:
            clause = f"clause {f['clause']}" if f['clause'] else ''
            print(f"    {SYM_ERR} {clause}: {f['description']} ({f['count']} instance(s))")

    if report_file:
        _write_pdf_report(result, report_file)

    return result


def _write_pdf_report(result, report_file):
    """Write a PDF accessibility check result to a Markdown file."""
    lines = [
        f"# PDF Accessibility Report: {result['file']}",
        '',
        f"**Tool:** veraPDF (PDF/UA-1)  ",
        f"**File:** `{result['path']}`  ",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        '',
        '## Summary',
        '',
        f"| Result | Count |",
        f"|--------|-------|",
        f"| Passed | {result['passed']} |",
        f"| Failed | {result['failed']} |",
        '',
    ]
    if result['failures']:
        lines += ['## Failures', '']
        for f in result['failures']:
            clause = f"Clause {f['clause']}" if f['clause'] else 'Unknown clause'
            lines.append(f"**{clause}:** {f['description']} — {f['count']} instance(s)")
            lines.append('')
    else:
        lines += ['## Failures', '', '✅ No failures — PDF/UA compliant.', '']

    Path(report_file).write_text('\n'.join(lines), encoding='utf-8')
    print(f"  {SYM_DONE} Report saved: {report_file}")


# ---------------------------------------------------------------------------
# HTML link text checker — WCAG 2.4.4, 2.4.9, and Universal Design
#
# Checks every <a> element's accessible name against known vague-text patterns
# and other link quality rules.  No external tools required — Python 3 only.
#
# WCAG 2.4.4  Link Purpose (In Context)  — Level A   → errors
# WCAG 2.4.9  Link Purpose (Link Only)   — Level AAA → warnings
# Universal Design: equitable and flexible navigation for all users
# ---------------------------------------------------------------------------

# Exact link text matches (after normalisation) that are always vague.
_LINK_VAGUE_EXACT = {
    'click here', 'here', 'read more', 'more', 'link', 'this link',
    'this', 'view details', 'details', 'learn more', 'click',
    'see more', 'see here', 'get more', 'view more', 'go here', 'info', 'go',
}

# Short prefixes where the complete phrase is still too vague (≤3 words).
_LINK_VAGUE_STARTS = ('click ', 'read ')

_LINK_URL_RE = re.compile(r'^https?://', re.IGNORECASE)


def _link_normalise(text):
    """Lowercase, collapse whitespace, strip trailing punctuation for comparison."""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text.rstrip(' .,;:!?»')


class _LinkParser(HTMLParser):
    """Extract every <a> element: href, aria-label, text content, line number,
    and whether the link is nested inside a heading element."""

    _HEADING_TAGS = {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}

    def __init__(self):
        super().__init__()
        self.links = []
        self._current = None
        self._link_depth = 0
        self._heading_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        line, _ = self.getpos()
        if tag in self._HEADING_TAGS:
            self._heading_depth += 1
        if tag == 'a':
            self._link_depth += 1
            if self._link_depth == 1:
                self._current = {
                    'href':       attrs_dict.get('href', ''),
                    'aria_label': attrs_dict.get('aria-label', '').strip(),
                    'text_parts': [],
                    'line':       line,
                    'in_heading': self._heading_depth > 0,
                }
        # Images inside links: alt text counts as the accessible name.
        if tag == 'img' and self._current is not None:
            alt = attrs_dict.get('alt', '').strip()
            if alt:
                self._current['text_parts'].append(alt)

    def handle_endtag(self, tag):
        if tag in self._HEADING_TAGS:
            self._heading_depth = max(0, self._heading_depth - 1)
        if tag == 'a':
            if self._link_depth == 1 and self._current is not None:
                raw = ''.join(self._current['text_parts'])
                self._current['text'] = ' '.join(raw.split())
                del self._current['text_parts']
                self.links.append(self._current)
                self._current = None
            self._link_depth = max(0, self._link_depth - 1)

    def handle_data(self, data):
        if self._current is not None and self._link_depth == 1:
            self._current['text_parts'].append(data)


def _run_link_checks(links):
    """Run all link text checks against a parsed link list.
    Returns a list of (kind, code, criterion, message) tuples where
    kind is 'error' or 'warn'."""
    issues = []

    # Build text → set-of-hrefs map for duplicate detection.
    text_to_hrefs = defaultdict(set)
    for lnk in links:
        effective = lnk['aria_label'] or lnk['text']
        norm = _link_normalise(effective)
        if norm:
            text_to_hrefs[norm].add(lnk['href'])

    seen_duplicate = set()

    for lnk in links:
        href       = lnk['href']
        raw_text   = lnk['text']
        aria_label = lnk['aria_label']
        effective  = aria_label or raw_text
        norm       = _link_normalise(effective)
        line       = lnk['line']

        # 1. Empty link — WCAG 2.4.4 Level A
        if not raw_text.strip() and not aria_label:
            issues.append(('error', 'EMPTY_LINK', 'WCAG 2.4.4 (Level A)',
                f'Line {line}: link has no text and no aria-label — '
                'assistive technology will announce only the URL or nothing.'))
            continue

        # 2. Vague text — WCAG 2.4.4 Level A / 2.4.9 Level AAA
        is_vague = (
            norm in _LINK_VAGUE_EXACT
            or (any(norm.startswith(p) for p in _LINK_VAGUE_STARTS)
                and len(norm.split()) <= 3)
        )
        if is_vague:
            issues.append(('error', 'VAGUE_TEXT',
                'WCAG 2.4.4 (Level A) / 2.4.9 (Level AAA)',
                f'Line {line}: link text "{raw_text.strip()}" does not describe '
                'the destination — screen reader users navigating by link list '
                'will not know where this goes.'))

        # 3. Raw URL as visible text — Universal Design
        if _LINK_URL_RE.match(raw_text.strip()) and not aria_label:
            issues.append(('warn', 'URL_AS_TEXT', 'Universal Design',
                f'Line {line}: link text is a raw URL. Consider a descriptive '
                'label or add an aria-label.'))

        # 4. href="#" placeholder — WCAG 2.4.4 / Universal Design
        if href == '#':
            issues.append(('warn', 'PLACEHOLDER_HREF',
                'WCAG 2.4.4 (Level A) / Universal Design',
                f'Line {line}: link "{raw_text.strip()}" uses href="#" and goes '
                'nowhere — keyboard and screen reader users get no useful feedback.'))

        # 5. Duplicate text → different destinations — WCAG 2.4.9 Level AAA
        if norm and norm not in seen_duplicate:
            hrefs = text_to_hrefs[norm]
            if len(hrefs) > 1:
                seen_duplicate.add(norm)
                issues.append(('warn', 'DUPLICATE_TEXT', 'WCAG 2.4.9 (Level AAA)',
                    f'Line {line}: link text "{raw_text.strip()}" is used for '
                    f'{len(hrefs)} different destinations — users navigating by '
                    'link list cannot distinguish them.'))

        # 6. Link inside heading — Universal Design (advisory)
        if lnk['in_heading']:
            issues.append(('warn', 'LINK_IN_HEADING',
                'Universal Design (advisory)',
                f'Line {line}: link "{raw_text.strip()}" is nested inside a heading '
                '— screen readers expose headings and links as separate lists.'))

    return issues


def check_html_link_text(html_file, verbose=False, report_file=None):
    """Audit a single HTML file for WCAG 2.4.4 / 2.4.9 link text issues.

    No external tools required.  Returns a dict with keys:
      errors (int), warnings (int), issues (list of tuples), link_count (int),
      error (str or None).
    Writes a Markdown report to report_file if provided.
    """
    html_path = Path(html_file)
    result = {
        'file': html_path.name,
        'path': str(html_path),
        'errors': 0, 'warnings': 0,
        'issues': [],
        'link_count': 0,
        'error': None,
    }

    if not html_path.exists():
        result['error'] = f'File not found: {html_file}'
        print(f'{SYM_ERR} File not found: {html_file}')
        return result

    try:
        content = html_path.read_text(encoding='utf-8', errors='replace')
    except OSError as exc:
        result['error'] = str(exc)
        print(f'{SYM_ERR} Could not read {html_file}: {exc}')
        return result

    parser = _LinkParser()
    parser.feed(content)
    links = parser.links
    result['link_count'] = len(links)

    raw_issues = _run_link_checks(links)
    result['issues'] = raw_issues
    result['errors']   = sum(1 for k, *_ in raw_issues if k == 'error')
    result['warnings'] = sum(1 for k, *_ in raw_issues if k == 'warn')

    if not raw_issues:
        print(f'{SYM_OK} {html_path.name} — {len(links)} link(s), no issues')
    else:
        parts = []
        if result['errors']:
            parts.append(f"{result['errors']} error(s)")
        if result['warnings']:
            parts.append(f"{result['warnings']} warning(s)")
        lead = SYM_ERR if result['errors'] else SYM_WARN
        print(f'{lead} {html_path.name} — {", ".join(parts)}')
        for kind, code, criterion, message in raw_issues:
            sym = SYM_ERR if kind == 'error' else SYM_WARN
            print(f'  {sym} [{code}] {message}')
            print(f'      Criterion: {criterion}')
            if verbose:
                idx = raw_issues.index((kind, code, criterion, message))
                # find the matching link for context
                for lnk in links:
                    lnk_line = str(lnk['line'])
                    if lnk_line in message.split(':')[0]:
                        print(f'      href: {lnk["href"] or "(empty)"}')
                        if lnk['text']:
                            print(f'      visible text: {lnk["text"]!r}')
                        if lnk['aria_label']:
                            print(f'      aria-label: {lnk["aria_label"]!r}')
                        break

    if report_file:
        _write_link_report([result], report_file)

    return result


def check_html_link_text_all(directory, recursive=False, verbose=False, report_file=None):
    """Audit all HTML files in a directory for WCAG 2.4.4 / 2.4.9 link text issues.

    Returns (passed_count, failed_count, total_errors, total_warnings).
    """
    directory = Path(directory)
    if recursive:
        html_files = sorted(
            f for f in directory.rglob('*.html')
            if '_site' not in f.parts and not any(p.startswith('.') for p in f.parts)
        )
    else:
        html_files = sorted(directory.glob('*.html'))

    if not html_files:
        scope = 'recursively in' if recursive else 'in'
        print(f'No .html files found {scope} {directory}')
        return 0, 0, 0, 0

    scope = 'recursively in' if recursive else 'in'
    print(f'Checking link text in {len(html_files)} HTML file(s) {scope} {directory}')
    print(f'Standard: WCAG 2.4.4 (Level A), 2.4.9 (Level AAA), Universal Design\n')

    all_results = []
    passed = failed = total_errors = total_warnings = 0

    for i, html_file in enumerate(html_files, 1):
        print(f'[{i}/{len(html_files)}] ', end='', flush=True)
        r = check_html_link_text(str(html_file), verbose=verbose)
        all_results.append(r)
        if r['errors'] or r['warnings']:
            failed += 1
        else:
            passed += 1
        total_errors   += r['errors']
        total_warnings += r['warnings']

    print()
    print('─' * 50)
    print(f'{SYM_DONE} Checked {len(html_files)} file(s): {passed} passed, {failed} with issues')
    if total_errors:
        print(f'  {SYM_ERR} {total_errors} error(s) — WCAG 2.4.4 Level A violation(s)')
    if total_warnings:
        print(f'  {SYM_WARN} {total_warnings} warning(s) — WCAG 2.4.9 AAA / Universal Design')

    if report_file:
        _write_link_report(all_results, report_file)

    return passed, failed, total_errors, total_warnings


def _write_link_report(results, report_file):
    """Write a Markdown link accessibility report for one or more HTML files."""
    today        = date.today().isoformat()
    total_links  = sum(r['link_count'] for r in results)
    total_errors = sum(r['errors']   for r in results)
    total_warns  = sum(r['warnings'] for r in results)
    files_ok     = sum(1 for r in results if not r['errors'] and not r['warnings'])

    lines = [
        '# Link Accessibility Report',
        '',
        f'**Generated:** {today}  ',
        '**Standard:** WCAG 2.1 — 2.4.4 Link Purpose (Level A), '
        '2.4.9 Link Purpose (Level AAA) — and Universal Design principles  ',
        f'**Files checked:** {len(results)}  ',
        f'**Total links:** {total_links}  ',
        f'**Files passing:** {files_ok} / {len(results)}',
        '',
        '---',
        '',
        '## Summary',
        '',
        '| Metric | Count |',
        '|--------|-------|',
        f'| Files checked | {len(results)} |',
        f'| Files with no issues | {files_ok} |',
        f'| Files with issues | {len(results) - files_ok} |',
        f'| Errors — WCAG 2.4.4 Level A (must fix) | {total_errors} |',
        f'| Warnings — WCAG 2.4.9 AAA / Universal Design (recommended) | {total_warns} |',
        f'| Total links checked | {total_links} |',
        '',
        '---',
        '',
        '## Issues by File',
        '',
    ]

    for r in results:
        errors = [(k, c, cr, m) for k, c, cr, m in r['issues'] if k == 'error']
        warns  = [(k, c, cr, m) for k, c, cr, m in r['issues'] if k == 'warn']
        lines.append(f'### {r["path"]}')
        lines.append('')
        if not r['issues']:
            lines.append(f'{r["link_count"]} link(s) checked — no issues found.')
            lines.append('')
            continue
        lines.append(
            f'{r["link_count"]} link(s) checked — '
            f'{len(errors)} error(s), {len(warns)} warning(s)'
        )
        lines.append('')
        if errors:
            lines.append('**Errors — WCAG Level A (must fix):**')
            lines.append('')
            for _, code, criterion, message in errors:
                lines.append(f'- **[{code}]** {message}')
                lines.append(f'  - Criterion: {criterion}')
            lines.append('')
        if warns:
            lines.append('**Warnings — WCAG Level AAA / Universal Design (recommended):**')
            lines.append('')
            for _, code, criterion, message in warns:
                lines.append(f'- **[{code}]** {message}')
                lines.append(f'  - Criterion: {criterion}')
            lines.append('')

    lines += [
        '---',
        '',
        '## Issue Reference',
        '',
        '| Code | Severity | Criterion | Description |',
        '|------|----------|-----------|-------------|',
        '| `EMPTY_LINK` | Error | WCAG 2.4.4 (A) | No text and no aria-label |',
        '| `VAGUE_TEXT` | Error | WCAG 2.4.4 (A) / 2.4.9 (AAA) | Generic text: '
        "'click here', 'here', 'read more', 'view details', etc. |",
        '| `URL_AS_TEXT` | Warning | Universal Design | Visible text is a raw URL |',
        "| `PLACEHOLDER_HREF` | Warning | WCAG 2.4.4 (A) / UD | href=\"#\" goes nowhere |",
        '| `DUPLICATE_TEXT` | Warning | WCAG 2.4.9 (AAA) | Same text, different destinations |',
        '| `LINK_IN_HEADING` | Warning | Universal Design | Link nested inside a heading |',
        '',
        '---',
        '',
        '## Why Link Text Matters',
        '',
        'Screen reader users and keyboard navigators frequently pull up a list of all '
        'links on a page to scan for what they need. When link text says "click here" '
        'or "here", every entry in that list is identical — the user cannot tell where '
        'any link goes without reading surrounding context.',
        '',
        '**Universal Design** goes further: descriptive link text benefits every user, '
        'including sighted users scanning a page and users with cognitive disabilities.',
        '',
        '**WCAG references:**',
        '- [2.4.4 Link Purpose (In Context) — Level A]'
        '(https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html)',
        '- [2.4.9 Link Purpose (Link Only) — Level AAA]'
        '(https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-link-only.html)',
        '',
        f'*Generated by latex-accessibility.py v{__version__}*',
    ]

    try:
        Path(report_file).write_text('\n'.join(lines), encoding='utf-8')
        print(f'  {SYM_DONE} Report saved: {report_file}')
    except OSError as exc:
        print(f'{SYM_ERR} Could not write report: {exc}')


def generate_report(directory, output_file=None, output_format='markdown'):
    """
    Generate a Markdown (default) or PDF accessibility compliance report
    for all .tex files in a directory.

    PDF output requires pandoc to be installed.
    """
    directory = Path(directory)
    tex_files = sorted(directory.glob('*.tex'))

    if not tex_files:
        print(f"No .tex files found in {directory}")
        return

    # Analyse every file
    print(f"Analysing {len(tex_files)} file(s) in {directory}...")
    results = [check_file_accessibility(f) for f in tex_files]

    compliant     = [r for r in results if _compliance_level(r) == 'compliant']
    partial       = [r for r in results if _compliance_level(r) == 'partial']
    non_compliant = [r for r in results if _compliance_level(r) == 'non-compliant']

    now = datetime.now().strftime('%Y-%m-%d %H:%M')

    # ── Build Markdown ────────────────────────────────────────────────────────
    lines = []
    lines += [
        '# Accessibility Compliance Report',
        '',
        f'**Directory:** `{directory}`  ',
        f'**Generated:** {now}  ',
        f'**Files checked:** {len(results)}',
        '',
        '---',
        '',
        '## Summary',
        '',
        '| Status | Count |',
        '|--------|-------|',
        f'| ✅ Compliant | {len(compliant)} |',
        f'| ⚠️ Partial | {len(partial)} |',
        f'| ❌ Non-compliant | {len(non_compliant)} |',
        f'| **Total** | **{len(results)}** |',
        '',
        '---',
        '',
        '## File Details',
        '',
    ]

    icon_map = {'compliant': '✅', 'partial': '⚠️', 'non-compliant': '❌'}
    features = [
        ('has_hyperref',      '`hyperref` package'),
        ('has_bookmark',      '`bookmark` package'),
        ('has_enumitem',      '`enumitem` package'),
        ('has_bookmarksetup', '`\\bookmarksetup{}` configuration'),
        ('has_notice',        'Accessibility notice'),
    ]

    for r in results:
        level = _compliance_level(r)
        icon  = icon_map[level]
        lines.append(f'### {icon} {r["file"]}')
        lines.append('')

        if not r['readable']:
            lines.append('**Error:** Could not read file.')
            for issue in r['issues']:
                lines.append(f'- {issue}')
            lines.append('')
            continue

        lines += ['| Feature | Status |', '|---------|--------|']
        for key, label in features:
            status = '✅ Yes' if r[key] else '❌ Missing'
            lines.append(f'| {label} | {status} |')
        if r['has_accessibility_pkg']:
            lines.append('| `accessibility` package (optional) | ✅ Yes |')

        # LAT1: alt text hints
        gwh = r.get('graphics_without_hint', 0)
        if gwh == 0:
            lines.append('| `\\includegraphics` alt text hints | ✅ All present |')
        else:
            lines.append(f'| `\\includegraphics` alt text hints | ⚠️ {gwh} instance(s) missing hint |')

        # LAT2: figure captions
        fwc = r.get('figures_without_caption', [])
        if not fwc:
            lines.append('| Figure `\\caption` | ✅ All present |')
        else:
            locations = ', '.join(f'line {n}' for n in fwc)
            lines.append(f'| Figure `\\caption` | ⚠️ Missing on {locations} |')

        # LAT3: table captions
        twc = r.get('tables_without_caption', [])
        if not twc:
            lines.append('| Table `\\caption` | ✅ All present |')
        else:
            locations = ', '.join(f'line {n}' for n in twc)
            lines.append(f'| Table `\\caption` | ⚠️ Missing on {locations} |')

        # LAT4: color-only text
        cot = r.get('color_only_text', [])
        if not cot:
            lines.append('| Color-only text | ✅ None detected |')
        else:
            locations = ', '.join(f'line {ln}' for ln, _, _ in cot)
            lines.append(f'| Color-only text | ⚠️ {len(cot)} instance(s) on {locations} |')

        lines.append('')

        if r['issues']:
            lines += [
                '**To fix, run:**',
                '```bash',
                f'python3 latex-accessibility.py add {r["file"]}',
                '```',
                '',
            ]

    # ── Action Items ─────────────────────────────────────────────────────────
    if non_compliant or partial:
        lines += ['---', '', '## Action Items', '']

        if non_compliant:
            lines.append('### Files needing full accessibility features')
            lines.append('')
            for r in non_compliant:
                lines.append(f'- [ ] `{r["file"]}`')
            lines.append('')

        if partial:
            lines.append('### Files needing partial fixes')
            lines.append('')
            for r in partial:
                lines.append(f'- [ ] `{r["file"]}`')
            lines.append('')

        lines += [
            '**To fix all at once:**',
            '```bash',
            f'python3 latex-accessibility.py add-all {directory}',
            '```',
            '',
        ]

    markdown_content = '\n'.join(lines)

    # ── Determine output paths ────────────────────────────────────────────────
    if output_format == 'pdf':
        if output_file:
            base = Path(output_file).with_suffix('')
        else:
            base = directory / 'accessibility_report'

        md_path  = base.with_suffix('.md')
        pdf_path = base.with_suffix('.pdf')

        # Write markdown
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        # Convert to PDF via pandoc
        if subprocess.run(['which', 'pandoc'], capture_output=True).returncode == 0:
            try:
                subprocess.run(
                    ['pandoc', str(md_path), '-o', str(pdf_path),
                     '--pdf-engine=pdflatex',
                     '-V', 'geometry:margin=1in',
                     '-V', 'fontsize=11pt'],
                    check=True, capture_output=True
                )
                md_path.unlink()
                print(f"{SYM_DONE} Report generated: {pdf_path}")
            except subprocess.CalledProcessError:
                print(f"{SYM_WARN} pandoc failed to produce PDF — report saved as Markdown instead:")
                print(f"   {md_path}")
        else:
            print(f"{SYM_WARN} pandoc not found — report saved as Markdown instead.")
            print("   To install pandoc: sudo apt-get install pandoc")
            print(f"   {md_path}")
    else:
        # Markdown output
        if output_file:
            output_path = Path(output_file)
            if not output_path.suffix:
                output_path = output_path.with_suffix('.md')
        else:
            output_path = directory / 'accessibility_report.md'

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"{SYM_DONE} Report generated: {output_path}")

    # Terminal summary
    print(f"\nSummary: {len(compliant)}/{len(results)} files fully compliant")
    if non_compliant:
        print(f"  {SYM_ERR} {len(non_compliant)} file(s) need full accessibility features")
    if partial:
        print(f"  {SYM_WARN} {len(partial)} file(s) need partial fixes")
    if not non_compliant and not partial:
        print("  All files meet accessibility requirements.")


def process_directory(directory, command, use_progress=False, dry_run=False, backup=False):
    """Process all .tex files in a directory"""
    directory = Path(directory)
    tex_files = sorted(directory.glob('*.tex'))

    if not tex_files:
        print(f"No .tex files found in {directory}")
        return

    total = len(tex_files)
    modified_count = 0
    skipped_count = 0
    error_count = 0

    def process_file(tex_file):
        """Run the appropriate command on one file, return result."""
        if command == 'add-all':
            return add_all_features(tex_file, dry_run=dry_run, verbose=_VERBOSE, backup=backup)
        elif command == 'fix-all':
            return fix_structure(tex_file, dry_run=dry_run, backup=backup)

    def label_result(result, tex_file):
        """Update counters and return a short status string."""
        nonlocal modified_count, skipped_count, error_count
        if result is True:
            modified_count += 1
            return f"{SYM_OK} modified"
        elif result is None:
            error_count += 1
            return f"{SYM_ERR} error"
        else:
            skipped_count += 1
            return f"{SYM_SKIP} already compliant"

    if use_progress:
        if not HAS_TQDM:
            print(f"{SYM_WARN} tqdm not installed — falling back to verbose output.")
            print("   To install: pip install tqdm\n")
            use_progress = False

    dry_run_tag = " [DRY RUN]" if dry_run else ""

    if use_progress:
        # Compact progress bar mode
        print(f"Processing {total} file(s) in {directory}{dry_run_tag}")
        with tqdm(tex_files, unit="file", dynamic_ncols=True) as bar:
            for tex_file in bar:
                bar.set_description(tex_file.name[:40])
                result = process_file(tex_file)
                status = label_result(result, tex_file)
                # Errors still get a visible message above the bar
                if result is None:
                    tqdm.write(f"  {SYM_ERR} Error processing {tex_file.name}")
                bar.set_postfix_str(status)
    else:
        # Verbose per-file mode (default)
        print(f"Processing {total} file(s) in {directory}{dry_run_tag}\n")
        for i, tex_file in enumerate(tex_files, 1):
            print(f"[{i}/{total}] {tex_file.name}")
            result = process_file(tex_file)
            status = label_result(result, tex_file)
            # In dry-run the per-file detail is already printed inside
            # add_all_features / fix_structure, so just show the status tag
            print(f"  {status}")

    action_word = "Would modify" if dry_run else "Modified"
    print(f"\n{'─' * 40}")
    if dry_run:
        print(f"[DRY RUN] {total} file(s) analysed — no files written")
    else:
        print(f"{SYM_OK} Processed {total} file(s)")
    print(f"  {action_word}: {modified_count}")
    print(f"  Skipped:   {skipped_count} (already compliant)")
    print(f"  Errors:    {error_count}")


def _wizard_prompt(question, default=None, choices=None):
    """Print a prompt and return stripped input. Ctrl-C exits cleanly."""
    if choices:
        options = '/'.join(
            c.upper() if c == default else c
            for c in choices
        )
        question = f"{question} [{options}]"
    elif default is not None:
        question = f"{question} [{default}]"
    question += ": "
    try:
        answer = input(question).strip()
    except (KeyboardInterrupt, EOFError):
        print("\nWizard cancelled.")
        sys.exit(0)
    if not answer and default is not None:
        return default
    return answer


def run_wizard():
    """Interactive step-by-step wizard for making LaTeX files accessible."""
    divider = "─" * 50

    print(divider)
    print("  LaTeX Accessibility Wizard")
    print(divider)
    print("Answer each question — press Enter to accept the default shown in [ ].")
    print("Press Ctrl-C at any time to cancel.\n")

    # ── Step 1: file or directory ────────────────────────────────────────────
    print("Step 1: What do you want to process?")
    mode = _wizard_prompt("  (f) a single file, or (d) a whole directory", default='f', choices=['f', 'd'])
    mode = mode.lower()

    if mode == 'f':
        path_label = "Path to .tex file"
    else:
        path_label = "Path to directory containing .tex files"

    print()
    print(f"Step 2: {path_label}")
    while True:
        target = _wizard_prompt("  Path", default='.')
        target_path = Path(target)
        if mode == 'f':
            if not target_path.exists():
                print(f"  {SYM_ERR} File not found: {target}")
            elif not str(target).endswith('.tex'):
                print(f"  {SYM_WARN} That doesn't look like a .tex file — continue anyway?")
                confirm = _wizard_prompt("  ", default='n', choices=['y', 'n'])
                if confirm.lower() == 'y':
                    break
            else:
                break
        else:
            if not target_path.exists() or not target_path.is_dir():
                print(f"  {SYM_ERR} Directory not found: {target}")
            else:
                tex_files = sorted(target_path.glob('*.tex'))
                if not tex_files:
                    print(f"  {SYM_WARN} No .tex files found in {target}")
                else:
                    print(f"  Found {len(tex_files)} .tex file(s)")
                    break

    # ── Step 3: HTML URL ─────────────────────────────────────────────────────
    print()
    print("Step 3: HTML URL for the accessibility notice")
    print("  This is the web address where the accessible HTML version will live.")
    print("  Leave blank to auto-generate from the file path.")
    html_url = _wizard_prompt("  HTML URL", default='')
    if not html_url:
        html_url = None
        print(f"  {SYM_SKIP} URL will be auto-generated")

    # ── Step 4: preview ──────────────────────────────────────────────────────
    print()
    print("Step 4: Preview changes before applying?")
    show_preview = _wizard_prompt("  Show dry-run preview", default='y', choices=['y', 'n'])

    if show_preview.lower() == 'y':
        print()
        print(divider)
        print("  Preview (no files will be written)")
        print(divider)
        if mode == 'f':
            add_all_features(target, html_url=html_url, dry_run=True)
        else:
            for tex_file in sorted(Path(target).glob('*.tex')):
                add_all_features(str(tex_file), html_url=html_url, dry_run=True)
        print(divider)

    # ── Step 5: confirm and apply ────────────────────────────────────────────
    print()
    apply = _wizard_prompt("Apply changes?", default='y', choices=['y', 'n'])

    if apply.lower() != 'y':
        print("No changes made.")
        sys.exit(0)

    print()
    print(divider)
    print("  Applying changes")
    print(divider)

    if mode == 'f':
        result = add_all_features(target, html_url=html_url, verbose=_VERBOSE)
        if result is True:
            print(f"{SYM_OK} Added accessibility features to {target}")
        elif result is False:
            print(f"{SYM_SKIP} {target} already has accessibility features")
        else:
            print(f"{SYM_ERR} Could not process {target}")
    else:
        tex_files = sorted(Path(target).glob('*.tex'))
        modified = skipped = errors = 0
        for tex_file in tex_files:
            result = add_all_features(str(tex_file), html_url=html_url, verbose=_VERBOSE)
            if result is True:
                print(f"  {SYM_OK} {tex_file.name}")
                modified += 1
            elif result is False:
                print(f"  {SYM_SKIP} {tex_file.name} (already compliant)")
                skipped += 1
            else:
                print(f"  {SYM_ERR} {tex_file.name} (error)")
                errors += 1
        print(divider)
        print(f"{SYM_DONE} Processed {len(tex_files)} file(s)")
        print(f"  Modified: {modified}")
        print(f"  Skipped:  {skipped} (already compliant)")
        if errors:
            print(f"  Errors:   {errors}")

    # ── Step 6: generate report ──────────────────────────────────────────────
    if mode == 'd':
        print()
        want_report = _wizard_prompt("Generate an accessibility compliance report?", default='y', choices=['y', 'n'])
        if want_report.lower() == 'y':
            generate_report(target)


def main():
    def show_help():
        print(__doc__.format(version=__version__))

    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)

    command = sys.argv[1]

    # Handle --version and --help flags
    if command in ['--version', '-v']:
        print(f"LaTeX Accessibility Tool v{__version__}")
        sys.exit(0)

    if command in ['--help', '-h']:
        show_help()
        sys.exit(0)

    if command in ['add', 'fix']:
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing file argument")
            print(f"\nUsage: {sys.argv[0]} {command} <file.tex>")
            print(f"\nExample: {sys.argv[0]} {command} mylab.tex")
            sys.exit(1)

        tex_file = sys.argv[2]

        if not Path(tex_file).exists():
            print(f"{SYM_ERR} Error: File not found: {tex_file}")
            print(f"\nSuggestions:")
            print(f"  • Check the file path is correct")
            print(f"  • Make sure you're in the right directory")
            print(f"  • Use 'ls' to see available .tex files")

            # Suggest similar files
            directory = Path(tex_file).parent if Path(tex_file).parent.exists() else Path('.')
            tex_files = list(directory.glob('*.tex'))
            if tex_files:
                print(f"\n  Available .tex files in {directory}:")
                for f in sorted(tex_files)[:5]:
                    print(f"    • {f.name}")
                if len(tex_files) > 5:
                    print(f"    ... and {len(tex_files) - 5} more")
            sys.exit(1)

        if not str(tex_file).endswith('.tex'):
            print(f"{SYM_WARN} Warning: {tex_file} doesn't have .tex extension")
            print(f"   This tool is designed for LaTeX files (.tex)")
            response = input("Continue anyway? (y/n): ")
            if response.lower() != 'y':
                sys.exit(0)

        dry_run = '--dry-run' in sys.argv
        do_backup = '--backup' in sys.argv

        if command == 'add':
            result = add_all_features(tex_file, dry_run=dry_run, verbose=_VERBOSE, backup=do_backup)
            if not dry_run:
                if result is True:
                    print(f"{SYM_OK} Added accessibility features to {tex_file}")
                elif result is False:
                    print(f"{SYM_SKIP} {tex_file} already has accessibility features")
        elif command == 'fix':
            result = fix_structure(tex_file, dry_run=dry_run, backup=do_backup)
            if not dry_run:
                if result is True:
                    print(f"{SYM_OK} Fixed structure in {tex_file}")
                elif result is False:
                    print(f"{SYM_SKIP} {tex_file} structure OK")

    elif command in ['add-all', 'fix-all']:
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing directory argument")
            print(f"\nUsage: {sys.argv[0]} {command} <directory>")
            print(f"\nExample: {sys.argv[0]} {command} IntroLinux/labs")
            sys.exit(1)

        directory = sys.argv[2]

        if not Path(directory).exists():
            print(f"{SYM_ERR} Error: Directory not found: {directory}")
            print(f"\nSuggestions:")
            print(f"  • Check the directory path is correct")
            print(f"  • Use 'ls' to see available directories")
            sys.exit(1)

        if not Path(directory).is_dir():
            print(f"{SYM_ERR} Error: {directory} is not a directory")
            print(f"   Use '{command.replace('-all', '')}' for single files")
            sys.exit(1)

        use_progress = '--progress' in sys.argv
        dry_run      = '--dry-run'  in sys.argv
        do_backup    = '--backup'   in sys.argv
        process_directory(directory, command, use_progress=use_progress, dry_run=dry_run, backup=do_backup)

    elif command == 'restore':
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing file argument")
            print(f"\nUsage: {sys.argv[0]} restore <file.tex>")
            sys.exit(1)
        tex_file = sys.argv[2]
        result = restore_file(tex_file)
        sys.exit(0 if result is True else 1)

    elif command == 'list-backups':
        path = sys.argv[2] if len(sys.argv) >= 3 else '.'
        found = list_backups(path)
        sys.exit(0 if found else 1)

    elif command == 'validate':
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing file argument")
            print(f"\nUsage: {sys.argv[0]} validate <file.tex>")
            sys.exit(1)

        tex_file = sys.argv[2]

        if not Path(tex_file).exists():
            print(f"{SYM_ERR} Error: File not found: {tex_file}")
            sys.exit(1)

        result = validate_file(tex_file)
        sys.exit(0 if result else 1)

    elif command == 'validate-all':
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing directory argument")
            print(f"\nUsage: {sys.argv[0]} validate-all <directory>")
            sys.exit(1)

        directory = Path(sys.argv[2])

        if not directory.exists() or not directory.is_dir():
            print(f"{SYM_ERR} Error: Directory not found: {sys.argv[2]}")
            sys.exit(1)

        tex_files = sorted(directory.glob('*.tex'))
        if not tex_files:
            print(f"No .tex files found in {directory}")
            sys.exit(0)

        total = len(tex_files)
        passed = 0
        failed = 0
        unavailable = 0

        print(f"Validating {total} file(s) in {directory}\n")
        for i, tex_file in enumerate(tex_files, 1):
            print(f"[{i}/{total}] ", end='', flush=True)
            result = validate_file(tex_file)
            if result is True:
                passed += 1
            elif result is False:
                failed += 1
            else:
                unavailable += 1
            print()

        print(f"{'─' * 40}")
        print(f"{SYM_OK} Validated {total} file(s)")
        print(f"  Passed:  {passed}")
        print(f"  Failed:  {failed}")
        if unavailable:
            print(f"  Skipped: {unavailable} (pdflatex not available)")
        sys.exit(0 if failed == 0 else 1)

    elif command == 'report':
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing directory argument")
            print(f"\nUsage: {sys.argv[0]} report <directory> [--output=file] [--format=markdown|pdf]")
            sys.exit(1)

        directory = sys.argv[2]

        if not Path(directory).exists() or not Path(directory).is_dir():
            print(f"{SYM_ERR} Error: Directory not found: {directory}")
            sys.exit(1)

        output_file   = None
        output_format = 'markdown'

        for arg in sys.argv[3:]:
            if arg.startswith('--output='):
                output_file = arg.split('=', 1)[1]
            elif arg.startswith('--format='):
                output_format = arg.split('=', 1)[1]
                if output_format not in ('markdown', 'pdf'):
                    print(f"{SYM_ERR} Error: Unknown format '{output_format}'")
                    print(f"   Valid formats: markdown, pdf")
                    sys.exit(1)

        generate_report(directory, output_file, output_format)

    elif command == 'check-packages':
        # Check LaTeX package installation
        success = check_latex_packages()
        sys.exit(0 if success else 1)

    elif command in ('wizard', 'interactive'):
        run_wizard()

    elif command == 'check-udl':
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing directory argument")
            print(f"\nUsage: {sys.argv[0]} check-udl <directory> [--recursive] [--output=report.md]")
            sys.exit(1)
        directory = Path(sys.argv[2])
        if not directory.exists() or not directory.is_dir():
            print(f"{SYM_ERR} Error: Directory not found: {sys.argv[2]}")
            sys.exit(1)
        recursive = '--recursive' in sys.argv or '-r' in sys.argv
        output_arg = next((a for a in sys.argv[3:] if a.startswith('--output=')), None)
        report_file = output_arg.split('=', 1)[1] if output_arg else None
        scope = 'recursively in' if recursive else 'in'
        print(f"Checking UDL format pairing and cross-linking {scope} {directory}\n")
        result = check_udl_directory(directory, recursive=recursive, report_file=report_file)
        sys.exit(0 if result['passed'] == result['total'] else 1)

    elif command == 'check-html':
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing file argument")
            print(f"\nUsage: {sys.argv[0]} check-html <file.html>")
            sys.exit(1)
        html_file = sys.argv[2]
        output_arg = next((a for a in sys.argv[3:] if a.startswith('--output=')), None)
        standard_arg = next((a for a in sys.argv[3:] if a.startswith('--standard=')), None)
        standard = standard_arg.split('=', 1)[1] if standard_arg else 'WCAG2AA'
        report_file = output_arg.split('=', 1)[1] if output_arg else None
        result = check_html_accessibility(html_file, report_file=report_file, standard=standard)
        sys.exit(0 if not result.get('error') and result['critical'] == 0 and result['serious'] == 0 else 1)

    elif command == 'check-html-all':
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing directory argument")
            print(f"\nUsage: {sys.argv[0]} check-html-all <directory>")
            sys.exit(1)
        directory = Path(sys.argv[2])
        if not directory.exists() or not directory.is_dir():
            print(f"{SYM_ERR} Error: Directory not found: {sys.argv[2]}")
            sys.exit(1)
        recursive = '--recursive' in sys.argv or '-r' in sys.argv
        standard_arg = next((a for a in sys.argv[3:] if a.startswith('--standard=')), None)
        standard = standard_arg.split('=', 1)[1] if standard_arg else 'WCAG2AA'
        html_files = sorted(directory.rglob('*.html') if recursive else directory.glob('*.html'))
        if not html_files:
            scope = 'recursively in' if recursive else 'in'
            print(f"No .html files found {scope} {directory}")
            sys.exit(0)
        scope = 'recursively in' if recursive else 'in'
        standard_label = 'WCAG 2.1 AAA' if standard == 'WCAG2AAA' else 'WCAG 2.1 AA'
        print(f"Checking {len(html_files)} HTML file(s) {scope} {directory} [{standard_label}]\n")
        passed = failed = skipped = 0
        for i, html_file in enumerate(html_files, 1):
            print(f"[{i}/{len(html_files)}] ", end='', flush=True)
            r = check_html_accessibility(str(html_file), standard=standard)
            if r.get('tool_missing'):
                sys.exit(1)
            if r.get('error'):
                skipped += 1
            elif r['critical'] == 0 and r['serious'] == 0:
                passed += 1
            else:
                failed += 1
            print()
        print('─' * 50)
        print(f"{SYM_DONE} Checked {len(html_files)} file(s)")
        print(f"  Passed:  {passed}")
        print(f"  Issues:  {failed}")
        if skipped:
            print(f"  Skipped: {skipped}")
        sys.exit(0 if failed == 0 else 1)

    elif command == 'check-pdf':
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing file argument")
            print(f"\nUsage: {sys.argv[0]} check-pdf <file.pdf>")
            sys.exit(1)
        pdf_file = sys.argv[2]
        output_arg = next((a for a in sys.argv[3:] if a.startswith('--output=')), None)
        report_file = output_arg.split('=', 1)[1] if output_arg else None
        result = check_pdf_accessibility(pdf_file, report_file=report_file)
        sys.exit(0 if not result.get('error') and result['failed'] == 0 else 1)

    elif command == 'check-pdf-all':
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing directory argument")
            print(f"\nUsage: {sys.argv[0]} check-pdf-all <directory>")
            sys.exit(1)
        directory = Path(sys.argv[2])
        if not directory.exists() or not directory.is_dir():
            print(f"{SYM_ERR} Error: Directory not found: {sys.argv[2]}")
            sys.exit(1)
        recursive = '--recursive' in sys.argv or '-r' in sys.argv
        pdf_files = sorted(directory.rglob('*.pdf') if recursive else directory.glob('*.pdf'))
        if not pdf_files:
            scope = 'recursively in' if recursive else 'in'
            print(f"No .pdf files found {scope} {directory}")
            sys.exit(0)
        scope = 'recursively in' if recursive else 'in'
        print(f"Checking {len(pdf_files)} PDF file(s) {scope} {directory}\n")
        passed = failed = skipped = 0
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"[{i}/{len(pdf_files)}] ", end='', flush=True)
            r = check_pdf_accessibility(str(pdf_file))
            if r.get('tool_missing'):
                sys.exit(1)
            if r.get('error'):
                skipped += 1
            elif r['failed'] == 0:
                passed += 1
            else:
                failed += 1
            print()
        print('─' * 50)
        print(f"{SYM_DONE} Checked {len(pdf_files)} file(s)")
        print(f"  Passed:  {passed}")
        print(f"  Issues:  {failed}")
        if skipped:
            print(f"  Skipped: {skipped}")
        sys.exit(0 if failed == 0 else 1)

    elif command == 'check-links':
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing file argument")
            print(f"\nUsage: {sys.argv[0]} check-links <file.html> [--output=report.md]")
            sys.exit(1)
        html_file = sys.argv[2]
        output_arg  = next((a for a in sys.argv[3:] if a.startswith('--output=')), None)
        report_file = output_arg.split('=', 1)[1] if output_arg else None
        result = check_html_link_text(html_file, verbose=_VERBOSE, report_file=report_file)
        sys.exit(0 if not result.get('error') and result['errors'] == 0 else 1)

    elif command == 'check-links-all':
        if len(sys.argv) < 3:
            print(f"{SYM_ERR} Error: Missing directory argument")
            print(f"\nUsage: {sys.argv[0]} check-links-all <directory> [--recursive] [--output=report.md]")
            sys.exit(1)
        directory = Path(sys.argv[2])
        if not directory.exists() or not directory.is_dir():
            print(f"{SYM_ERR} Error: Directory not found: {sys.argv[2]}")
            sys.exit(1)
        recursive   = '--recursive' in sys.argv or '-r' in sys.argv
        output_arg  = next((a for a in sys.argv[3:] if a.startswith('--output=')), None)
        report_file = output_arg.split('=', 1)[1] if output_arg else None
        _, failed, total_errors, _ = check_html_link_text_all(
            directory, recursive=recursive, verbose=_VERBOSE, report_file=report_file
        )
        sys.exit(0 if total_errors == 0 else 1)

    else:
        print(f"{SYM_ERR} Error: Unknown command: {command}")
        print(f"\nValid commands: add, fix, add-all, fix-all, validate, validate-all,")
        print(f"  report, check-packages, wizard,")
        print(f"  check-html, check-html-all, check-pdf, check-pdf-all, check-udl,")
        print(f"  check-links, check-links-all")
        print(f"\nAdd --dry-run to add/fix/add-all/fix-all to preview changes without writing files.")
        print(f"\nFor help, run: {sys.argv[0]} --help")
        sys.exit(1)


if __name__ == '__main__':
    main()
