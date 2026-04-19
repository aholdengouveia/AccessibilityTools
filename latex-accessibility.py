#!/usr/bin/env python3
r"""LaTeX Accessibility Tool v{version} — make .tex files accessible for PDF and HTML output.

COMMANDS
  wizard                        Step-by-step guided mode (recommended for first-time use)

  add <file.tex>                Add accessibility features to a single file
  add-all <directory>           Add accessibility features to every .tex file in a directory
  fix <file.tex>                Fix structural issues (e.g. bookmarksetup inside hypersetup)
  fix-all <directory>           Fix structural issues in every .tex file in a directory

  validate <file.tex>           Compile with pdflatex and report accessibility features
  validate-all <directory>      Validate every .tex file in a directory

  report <directory>            Generate a Markdown accessibility compliance report
  check-packages                Check whether LaTeX and required packages are installed

FLAGS (work with most commands)
  --dry-run                     Show what would change without writing any files
  --verbose                     Print each individual change made per file
  --plain                       Replace emoji with [OK]/[WARN]/[ERR] for screen readers
  --progress                    Show a progress bar for batch operations (requires tqdm)
  --format=pdf                  Output report as PDF instead of Markdown (requires pandoc)
  --output=<path>               Custom output path for the report file
  --version / -v                Print version and exit
  --help / -h                   Show this help and exit

EXAMPLES
  First time? Use the wizard:
    python3 latex-accessibility.py wizard

  Preview what a file needs (no changes written):
    python3 latex-accessibility.py add mylab.tex --dry-run

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

__version__ = "1.2.0"

import sys
import re
import platform
import subprocess
from datetime import datetime
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


def add_all_features(tex_file, html_url=None, dry_run=False, verbose=False):
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
    content, url_modified      = fix_plain_urls(content)
    content, bookmark_modified = add_bookmark_configuration(content)
    if html_url:
        content, notice_modified = add_accessibility_notice(content, html_url)
    else:
        notice_modified = False
    content, alt_modified, alt_count = add_alt_text_hints(content)

    modified = pkg_modified or url_modified or bookmark_modified or notice_modified or alt_modified

    # Advisory checks — never block or modify, run on original_content for accurate line numbers
    caption_issues = check_figure_captions(original_content)
    table_caption_issues = check_table_captions(original_content)
    color_issues = check_color_only_text(original_content)

    if dry_run:
        if modified:
            changes = []
            if pkg_modified:
                pkgs = []
                if '\\usepackage{bookmark}' not in original_content:
                    pkgs.append('bookmark')
                if '\\usepackage{enumitem}' not in original_content:
                    pkgs.append('enumitem')
                if pkgs:
                    changes.append(f'add package(s): {", ".join(pkgs)}')
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
        try:
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(content)
            if verbose:
                if pkg_modified:
                    pkgs = []
                    if '\\usepackage{bookmark}' not in original_content:
                        pkgs.append('bookmark')
                    if '\\usepackage{enumitem}' not in original_content:
                        pkgs.append('enumitem')
                    for pkg in pkgs:
                        print(f"  - Added package: {pkg}")
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


def fix_structure(tex_file, dry_run=False):
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


def process_directory(directory, command, use_progress=False, dry_run=False):
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
            return add_all_features(tex_file, dry_run=dry_run, verbose=_VERBOSE)
        elif command == 'fix-all':
            return fix_structure(tex_file, dry_run=dry_run)

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

        if command == 'add':
            result = add_all_features(tex_file, dry_run=dry_run, verbose=_VERBOSE)
            if not dry_run:
                if result is True:
                    print(f"{SYM_OK} Added accessibility features to {tex_file}")
                elif result is False:
                    print(f"{SYM_SKIP} {tex_file} already has accessibility features")
        elif command == 'fix':
            result = fix_structure(tex_file, dry_run=dry_run)
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
        process_directory(directory, command, use_progress=use_progress, dry_run=dry_run)

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

    else:
        print(f"{SYM_ERR} Error: Unknown command: {command}")
        print(f"\nValid commands: add, fix, add-all, fix-all, validate, validate-all, report, check-packages, wizard")
        print(f"Add --dry-run to add/fix/add-all/fix-all to preview changes without writing files.")
        print(f"\nFor help, run: {sys.argv[0]} --help")
        sys.exit(1)


if __name__ == '__main__':
    main()
