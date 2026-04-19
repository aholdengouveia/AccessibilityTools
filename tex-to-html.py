#!/usr/bin/env python3
"""
Unified LaTeX to HTML converter with multiple backends

Supports three conversion backends:
  - custom: Fast Python parser with semantic HTML (default, always available)
  - pandoc: Uses pandoc for robust LaTeX parsing (requires pandoc)
  - htlatex: Uses htlatex/make4ht for complex documents (requires TeX4ht)

Usage:
  python3 tex-to-html.py myfile.tex                    # Auto-detect best method
  python3 tex-to-html.py --backend=pandoc myfile.tex   # Use specific backend
  python3 tex-to-html.py --list-backends               # Show available backends
"""

__version__ = "1.2.2"

import sys
import re
import argparse
import subprocess
import shutil
from pathlib import Path


# ============================================================================
# Backend Detection
# ============================================================================

def check_command(cmd):
    """Check if a command is available"""
    return shutil.which(cmd) is not None


def detect_available_backends():
    """Detect which conversion backends are available"""
    backends = {
        'custom': True,  # Always available
        'pandoc': check_command('pandoc'),
        'htlatex': check_command('htlatex')
    }
    return backends


def get_best_backend():
    """Determine the best available backend (custom > pandoc > htlatex)"""
    available = detect_available_backends()

    # Prefer custom (fastest, most control)
    if available['custom']:
        return 'custom'
    elif available['pandoc']:
        return 'pandoc'
    elif available['htlatex']:
        return 'htlatex'

    return 'custom'  # Fallback to custom


# ============================================================================
# Input File Preprocessing
# ============================================================================

def preprocess_inputs(tex_content, base_path, processed_files=None):
    """
    Recursively expand \input{} and \include{} commands

    This allows documents to be composed of multiple files, which is common
    for large LaTeX documents.

    Args:
        tex_content: The LaTeX content to process
        base_path: Path object for the directory of the current file
        processed_files: Set of already processed files (to avoid infinite loops)

    Returns:
        Processed content with all inputs expanded
    """
    if processed_files is None:
        processed_files = set()

    # Pattern to match \input{filename} or \include{filename}
    # These can have optional .tex extension
    pattern = r'\\(?:input|include)\{([^}]+)\}'

    def replace_input(match):
        filename = match.group(1).strip()

        # Try multiple file resolution strategies
        possible_files = []

        # Strategy 1: Use filename as-is
        possible_files.append(base_path / filename)

        # Strategy 2: Add .tex extension if not present
        if not filename.endswith('.tex'):
            possible_files.append(base_path / f"{filename}.tex")

        # Strategy 3: Try removing .tex if present and adding it back
        if filename.endswith('.tex'):
            possible_files.append(base_path / filename[:-4])

        # Find the first file that exists
        input_file = None
        for candidate in possible_files:
            if candidate.exists() and candidate.is_file():
                input_file = candidate
                break

        if not input_file:
            # File not found, leave a comment and warning
            print(f"⚠️  Warning: Could not find input file: {filename}")
            print(f"   Searched in: {base_path}")
            return f"\n% WARNING: Input file not found: {filename}\n"

        # Check for circular dependencies
        input_file_str = str(input_file.resolve())
        if input_file_str in processed_files:
            print(f"⚠️  Warning: Circular input detected: {filename}")
            return f"\n% WARNING: Circular input detected: {filename}\n"

        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Add this file to processed set
            new_processed = processed_files.copy()
            new_processed.add(input_file_str)

            # Recursively process inputs in the included file
            processed_content = preprocess_inputs(content, input_file.parent, new_processed)

            # Add a comment to mark where the input was expanded
            return f"\n% === BEGIN: {filename} ===\n{processed_content}\n% === END: {filename} ===\n"

        except Exception as e:
            print(f"⚠️  Warning: Error reading {filename}: {e}")
            return f"\n% ERROR: Could not read input file: {filename}\n"

    # Replace all \input{} and \include{} commands
    processed = re.sub(pattern, replace_input, tex_content)

    return processed


# ============================================================================
# HTML Post-Processing (from clean-html.py)
# ============================================================================

def post_process_html(html_file, css_path="../../css/accessible-lab.css"):
    """
    Clean and improve HTML:
    - Ensure proper HTML5 doctype
    - Add lang attribute and viewport meta
    - Link to CSS stylesheet
    - Improve semantic structure
    - Wrap sections with semantic HTML
    """
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove XML declaration
        content = re.sub(r'<\?xml[^>]*\?>\s*', '', content)

        # Ensure proper HTML5 doctype
        content = re.sub(r'<!DOCTYPE[^>]*>', '<!DOCTYPE html>', content)

        # Add lang attribute
        content = re.sub(r'<html[^>]*>', '<html lang="en-US">', content)

        # Add/update meta viewport
        if 'viewport' not in content:
            content = re.sub(
                r'(<head[^>]*>)',
                r'\1\n<meta name="viewport" content="width=device-width, initial-scale=1">',
                content
            )

        # Link to simplified CSS
        content = re.sub(
            r'<link[^>]*rel=["\']stylesheet["\'][^>]*>',
            f'<link href="{css_path}" rel="stylesheet" type="text/css">',
            content
        )

        # Improve semantic structure
        content = re.sub(r'<h3 class="likesectionHead"', '<h2', content)
        content = re.sub(r'class="likesectionHead"', '', content)
        content = re.sub(r'class="likesubsectionHead"', '', content)

        # Clean up excessive classes
        content = re.sub(r' class="noindent"', '', content)
        content = re.sub(r' class="indent"', '', content)
        content = re.sub(r' class="enumerate1"', '', content)

        # Wrap sections with semantic HTML
        lines = content.split('\n')
        new_lines = []
        section_open = False

        for line in lines:
            # Close previous section if new h2 starts
            if '<h2' in line and 'id=' in line and section_open:
                new_lines.append('</section>')
                section_open = False

            # Open new section
            if '<h2' in line and 'id=' in line:
                id_match = re.search(r'id=["\']([^"\']+)["\']', line)
                if id_match:
                    section_id = id_match.group(1)
                    new_lines.append(f'<section aria-labelledby="{section_id}">')
                    section_open = True

            new_lines.append(line)

        # Close last section if open
        if section_open:
            # Insert before </body>
            for i in range(len(new_lines) - 1, -1, -1):
                if '</body>' in new_lines[i]:
                    new_lines.insert(i, '</section>')
                    break

        content = '\n'.join(new_lines)

        # Write back
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)

        return True
    except Exception as e:
        print(f"Warning: Post-processing failed: {e}", file=sys.stderr)
        return False


# ============================================================================
# Custom Backend (Original tex-to-clean-html.py parser)
# ============================================================================

def extract_title(tex_content):
    """Extract title from \title{} command"""
    match = re.search(r'\\title\{([^}]+)\}', tex_content)
    return match.group(1) if match else "Lab Assignment"


def extract_author_info(tex_content):
    """Extract author information"""
    info = {}

    # Extract name - first try specific pattern for full names
    name_match = re.search(r'\\author\{[^}]*?([A-Z][a-z]+\s+[A-Z][a-z]+-[A-Z][a-z]+)', tex_content, re.DOTALL)
    if not name_match:
        # Try without hyphen
        name_match = re.search(r'\\author\{[^}]*?([A-Z][a-z]+\s+[A-Z][a-z]+)', tex_content, re.DOTALL)
    if not name_match:
        # Fall back to extracting anything in \author{}
        name_match = re.search(r'\\author\{([^}]+)\}', tex_content)

    info['name'] = name_match.group(1).strip() if name_match else "Author Name"

    # Extract website from preamble/author area only (before \begin{document})
    # This avoids picking up URLs from the document body
    preamble = tex_content.split(r'\begin{document}')[0] if r'\begin{document}' in tex_content else tex_content
    website_match = re.search(r'\\url\{(https://[^}]+)\}', preamble)
    info['website'] = website_match.group(1) if website_match else None

    # Extract GitHub (return None if not found)
    github_match = re.search(r'\\faGithub.*?\{:\s*([^}]+)\}', tex_content)
    info['github'] = github_match.group(1).strip() if github_match else None

    return info


def extract_sections(body):
    """Extract all section titles and IDs for TOC generation"""
    sections = []

    # Find all section headers
    for match in re.finditer(r'\\((?:sub)?section)\*?\{([^}]+)\}', body):
        section_type = match.group(1)
        title = match.group(2)
        section_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

        # Determine if it's a subsection
        is_subsection = section_type == 'subsection'

        sections.append({
            'title': title,
            'id': section_id,
            'is_subsection': is_subsection
        })

    return sections


def generate_toc(sections):
    """Generate HTML for table of contents"""
    if not sections:
        return ""

    html = '''        <nav role="navigation" aria-label="Table of Contents" class="toc">
            <h2>On this page:</h2>
            <ul>
'''

    for section in sections:
        if section['is_subsection']:
            # Skip subsections in TOC to keep it concise
            continue
        html += f'                <li><a href="#{section["id"]}">{section["title"]}</a></li>\n'

    html += '''            </ul>
        </nav>

'''

    return html


def generate_breadcrumbs(tex_file_path, page_title):
    """
    Generate breadcrumb navigation based on file path

    CUSTOMIZATION NOTE: This section_map is site-specific and should be
    customized for your directory structure. Breadcrumbs will only appear
    if the file path matches one of the keys in section_map.

    To customize, edit the section_map dictionary below with your own
    course/section names and URLs.
    """
    path = Path(tex_file_path)

    # CUSTOMIZE THIS: Map directory names to section info
    # Example: 'DirectoryName': {'name': 'Display Name', 'url': '/path/'}
    section_map = {
        # Add your own sections here, for example:
        # 'IntroData': {'name': 'Introduction to Data', 'url': '/IntroData/'},
        # 'AdvData': {'name': 'Advanced Data', 'url': '/AdvData/'},
    }

    # Find which section this file belongs to
    section_info = None
    for section_key, section_data in section_map.items():
        if section_key in str(path):
            section_info = section_data
            section_name = section_key
            break

    if not section_info:
        # No breadcrumbs if section_map is empty or path doesn't match
        return ""

    html = '''        <nav aria-label="Breadcrumb" class="breadcrumb-nav">
            <ol class="breadcrumb">
                <li><a href="/">Home</a></li>
'''
    html += f'                <li><a href="{section_info["url"]}">{section_info["name"]}</a></li>\n'
    html += f'                <li aria-current="page">{page_title}</li>\n'
    html += '''            </ol>
        </nav>

'''

    return html


def detect_code_language(code):
    """Detect the programming language of code block"""
    code_lower = code.lower()

    # Check for awk (must come before bash)
    if re.search(r'\bawk\b|\{print\s+\$|\$[0-9]+\b|BEGIN\s*\{|END\s*\{', code, re.IGNORECASE):
        return 'awk'

    # Check for sed (must come before bash)
    if re.search(r'\bsed\b|s/.*/.*/|[0-9]+,\$d|[0-9]+p', code):
        return 'sed'

    # Check for SQL
    if re.search(r'\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|FROM|WHERE|JOIN|TABLE)\b', code, re.IGNORECASE):
        return 'sql'

    # Check for bash/shell
    if re.search(r'\b(sudo|chmod|chown|grep|ls|cd|mkdir|rm|cp|mv|cat|echo|export|if\s+\[|then|fi|bash|sh)\b', code):
        return 'bash'

    # Default
    return 'text'


def convert_verbatim(block):
    """Convert verbatim environment to HTML code block"""
    # Extract code from verbatim environment
    match = re.search(r'\\begin\{verbatim\}(.*?)\\end\{verbatim\}', block, re.DOTALL)
    if not match:
        return ""

    code = match.group(1).strip()

    # Detect language
    lang = detect_code_language(code)

    # Return formatted code block
    html = f'<pre><code lang="{lang}">{code}</code></pre>\n\n'
    return html


def convert_itemize(block):
    """Convert itemize environment to HTML ul"""
    # Extract items - capture everything between \item and next \item or \end{itemize}
    items = re.findall(r'\\item\s+((?:(?!\\item|\\end\{itemize\}).)+)', block, re.DOTALL)
    if not items:
        return ""

    html = "<ul>\n"
    for item in items:
        # Check if item contains verbatim block
        if '\\begin{verbatim}' in item:
            # Extract text before verbatim
            parts = re.split(r'(\\begin\{verbatim\}.*?\\end\{verbatim\})', item, flags=re.DOTALL)
            item_html = ""
            for part in parts:
                if '\\begin{verbatim}' in part:
                    # Convert verbatim block
                    verb_match = re.search(r'\\begin\{verbatim\}(.*?)\\end\{verbatim\}', part, re.DOTALL)
                    if verb_match:
                        code = verb_match.group(1).strip()
                        lang = detect_code_language(code)
                        item_html += f'\n<pre><code lang="{lang}">{code}</code></pre>\n'
                else:
                    item_html += clean_latex(part.strip())
            html += f"<li>{item_html}</li>\n"
        else:
            item = clean_latex(item.strip())
            html += f"<li>{item}</li>\n"
    html += "</ul>\n\n"
    return html


def convert_enumerate(block):
    """Convert enumerate environment to HTML ol"""
    # Extract items - capture everything between \item and next \item or \end{enumerate}
    items = re.findall(r'\\item\s+((?:(?!\\item|\\end\{enumerate\}).)+)', block, re.DOTALL)
    if not items:
        return ""

    html = "<ol>\n"
    for item in items:
        # Check if item contains verbatim block
        if '\\begin{verbatim}' in item:
            # Extract text before and after verbatim
            parts = re.split(r'(\\begin\{verbatim\}.*?\\end\{verbatim\})', item, flags=re.DOTALL)
            item_html = ""
            for part in parts:
                if '\\begin{verbatim}' in part:
                    # Convert verbatim block
                    verb_match = re.search(r'\\begin\{verbatim\}(.*?)\\end\{verbatim\}', part, re.DOTALL)
                    if verb_match:
                        code = verb_match.group(1).strip()
                        lang = detect_code_language(code)
                        item_html += f'\n<pre><code lang="{lang}">{code}</code></pre>\n'
                else:
                    cleaned = clean_latex(part.strip())
                    if cleaned:
                        item_html += cleaned
            html += f"<li>{item_html}</li>\n"
        else:
            item = clean_latex(item.strip())
            html += f"<li>{item}</li>\n"
    html += "</ol>\n\n"
    return html


def convert_todolist(block):
    """Convert todolist environment to accessible HTML checklist.

    \item [\done]  -> checked item (✓)
    \item [\wontfix] -> crossed-out item (✗)
    plain \item    -> unchecked item (☐)
    """
    # Find each \item, capturing the optional argument and content
    items = re.findall(
        r'\\item\s*(?:\[([^\]]*)\])?\s*((?:(?!\\item|\\end\{todolist\}).)+)',
        block, re.DOTALL
    )
    if not items:
        return ""

    html = '<ul class="checklist" role="list">\n'
    for opt, content in items:
        opt = opt.strip()
        if re.search(r'\\done', opt):
            marker = '<span role="img" aria-label="checked" class="check-done">&#x2713;</span>'
        elif re.search(r'\\wontfix', opt):
            marker = '<span role="img" aria-label="will not fix" class="check-wontfix">&#x2717;</span>'
        else:
            marker = '<span role="img" aria-label="unchecked" class="check-open">&#x2610;</span>'
        text = clean_latex(content.strip())
        if text:
            html += f'<li>{marker} {text}</li>\n'
    html += '</ul>\n\n'
    return html


def convert_figure(block):
    """Convert figure to HTML"""
    # Extract image filename
    img_match = re.search(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', block)
    if not img_match:
        return ""

    img_src = img_match.group(1)

    # Extract caption
    caption_match = re.search(r'\\caption\{([^}]+)\}', block)
    caption = caption_match.group(1) if caption_match else ""

    # Extract alt text
    alt_match = re.search(r'\\alt\{([^}]+)\}', block)
    alt_text = alt_match.group(1) if alt_match else caption

    html = "<figure>\n"
    html += f'<img src="{img_src}" alt="{clean_latex(alt_text)}">\n'
    if caption:
        html += f"<figcaption>{clean_latex(caption)}</figcaption>\n"
    html += "</figure>\n\n"

    return html


def convert_table(block):
    """
    Convert LaTeX table/tabular/longtable environment to accessible HTML table

    Supports:
    - table, tabular, and longtable environments
    - Column specifications (|l|c|r|, etc.)
    - \\hline for horizontal rules
    - \\caption for table captions
    - & for cell separators
    - \\\\ for row separators
    - \\textbf{} for bold (header detection)
    - longtable-specific commands (\\endfirsthead, \\endhead, \\endfoot, \\endlastfoot)
    """
    # Extract caption if present (can be inside or outside the environment)
    # Also handle \label{} that may follow the caption
    caption_match = re.search(r'\\caption\{([^}]+)\}', block)
    caption = caption_match.group(1) if caption_match else None

    # Try to match longtable first, then tabular
    # Column specs may contain nested braces like p{3cm}, m{5cm} etc.
    # Optional alignment [c] or [H] may appear before the column spec
    col_spec = r'(?:\[[^\]]*\])?\{(?:[^{}]|\{[^{}]*\})*\}'
    tabular_match = re.search(r'\\begin\{longtable\}' + col_spec + r'(.*?)\\end\{longtable\}', block, re.DOTALL)
    if not tabular_match:
        tabular_match = re.search(r'\\begin\{tabular\}' + col_spec + r'(.*?)\\end\{tabular\}', block, re.DOTALL)

    if not tabular_match:
        return ""

    tabular_content = tabular_match.group(1).strip()

    # For longtable, handle caption that appears before the table data
    # Caption may be followed by \label{...} and then \\
    if '\\caption{' in tabular_content and not caption:
        caption_match_inline = re.match(r'\\caption\{([^}]+)\}\s*(?:\\label\{[^}]*\}\s*)?\\\\\s*', tabular_content)
        if caption_match_inline:
            caption = caption_match_inline.group(1)
            tabular_content = tabular_content[caption_match_inline.end():]

    # Remove \\hline commands (we'll use CSS for styling)
    tabular_content = re.sub(r'\\hline\s*', '', tabular_content)

    # Remove \label{...} commands (already extracted or not needed in HTML)
    tabular_content = re.sub(r'\\label\{[^}]*\}\s*', '', tabular_content)

    # Handle \multicolumn rows:
    # - Pagination notices ("continued from/to next page") are removed entirely
    # - Semantic header rows (e.g. "Faculty Representatives:") become full-width th cells
    # Use a pattern that handles nested braces like \textbf{...}
    mc_content_pat = r'\\multicolumn\{[^}]*\}\{[^}]*\}\{((?:[^{}]|\{[^{}]*\})*)\}'

    def handle_multicolumn(m):
        inner = m.group(1).strip()
        # Strip \textbf{} and similar formatting wrappers to get plain text
        plain = re.sub(r'\\textbf\{([^}]+)\}', r'\1', inner)
        plain = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', plain).strip()
        # Drop pagination notices silently
        if re.search(r'continued|next page|preceding page', plain, re.IGNORECASE):
            return ''
        # Keep semantic headers as a sentinel for row-building
        return f'__MULTICOLUMN__{plain}__ENDMULTICOLUMN__\\\\'

    tabular_content = re.sub(mc_content_pat, handle_multicolumn, tabular_content)

    # Remove the longtable end-marker commands (but keep the rows before them)
    tabular_content = re.sub(r'\s*\\endfirsthead\s*', '\n', tabular_content)
    tabular_content = re.sub(r'\s*\\endhead\s*', '\n', tabular_content)
    tabular_content = re.sub(r'\s*\\endfoot\s*', '\n', tabular_content)
    tabular_content = re.sub(r'\s*\\endlastfoot\s*', '\n', tabular_content)

    # Split into rows (separated by \\\\)
    rows = [row.strip() for row in re.split(r'\\\\', tabular_content) if row.strip()]

    # Remove duplicate consecutive rows (happens with longtable headers)
    # Also remove rows that are just the caption text or single-cell non-data rows
    deduplicated_rows = []
    prev_row = None
    for row in rows:
        row_stripped = row.strip()

        # Skip if it's the same as previous row (duplicate)
        if row_stripped == prev_row:
            continue

        # Skip if it's just the caption text (shouldn't be a table row)
        if caption and row_stripped == caption.strip():
            continue

        # Skip single-cell rows that match the caption (no & separators)
        if caption and '&' not in row_stripped and caption.strip() in row_stripped:
            continue

        deduplicated_rows.append(row)
        prev_row = row_stripped
    rows = deduplicated_rows

    if not rows:
        return ""

    # Start table HTML with accessibility attributes
    html = '<div class="table-container">\n<table>\n'

    if caption:
        # Use caption as table caption
        caption_id = re.sub(r'[^a-z0-9]+', '-', caption.lower()).strip('-')
        html += f'<caption id="{caption_id}">{caption}</caption>\n'

    # Check if first row is a header (contains \\textbf or all cells look like headers)
    first_row = rows[0]
    is_header_row = bool(re.search(r'\\textbf\{', first_row))

    # Count actual columns from the first data row (skip multicolumn sentinels)
    col_count = 1
    for row in rows:
        if not re.match(r'__MULTICOLUMN__', row.strip()):
            col_count = len(re.split(r'(?<!\\)&', row))
            break

    # Process rows
    in_thead = False
    for i, row in enumerate(rows):
        # Handle full-width section header rows from \multicolumn
        mc_match = re.match(r'__MULTICOLUMN__(.*)__ENDMULTICOLUMN__', row.strip())
        if mc_match:
            if not in_thead and i == 0:
                html += '<tbody>\n'
            text = mc_match.group(1).strip()
            # Use td (not th) with role="rowheader" — this labels the following rows
            # without falsely implying column-header semantics (scope="colgroup" would be wrong)
            html += (f'<tr role="row"><td colspan="{col_count}" '
                     f'class="table-section-header" role="rowheader">{text}</td></tr>\n')
            continue

        # Split into cells on unescaped & only (\& is a literal ampersand in LaTeX)
        cells = [cell.strip() for cell in re.split(r'(?<!\\)&', row)]

        # Determine if this is a header row
        is_header = (i == 0 and is_header_row)

        # Start thead or tbody
        if is_header and not in_thead:
            html += '<thead>\n'
            in_thead = True
        elif not is_header and in_thead:
            html += '</thead>\n<tbody>\n'
            in_thead = False
        elif i == 0 and not is_header:
            html += '<tbody>\n'

        html += '<tr>\n'

        for cell in cells:
            # Clean LaTeX commands from cell
            cell_clean = clean_latex(cell)

            # Use th for header cells, td for data cells
            tag = 'th' if is_header else 'td'
            scope = ' scope="col"' if is_header else ''
            html += f'<{tag}{scope}>{cell_clean}</{tag}>\n'

        html += '</tr>\n'

    # Close thead or tbody
    if in_thead:
        html += '</thead>\n'
    else:
        html += '</tbody>\n'

    html += '</table>\n</div>\n\n'

    return html


def clean_latex(text):
    """Remove/convert LaTeX commands to plain text/HTML"""
    # Remove comments (% not preceded by \ — \% is an escaped literal percent)
    text = re.sub(r'(?<!\\)%.*$', '', text, flags=re.MULTILINE)

    # Convert URLs (allow optional whitespace between \url and {)
    text = re.sub(r'\\url\s*\{([^}]+)\}', r'<a href="\1">\1</a>', text)
    text = re.sub(r'\\href\s*\{([^}]+)\}\s*\{([^}]+)\}', r'<a href="\1">\2</a>', text)

    # Convert standalone URLs to clickable links (not already in href attributes)
    text = re.sub(
        r'(?<!href=")(?<!")(?<!>)(https?://[^\s<>"]+)',
        r'<a href="\1">\1</a>',
        text
    )

    # Convert escaped special characters
    text = re.sub(r'\\&', '&amp;', text)
    text = re.sub(r'\\%', '%', text)
    text = re.sub(r'\\_', '_', text)
    text = re.sub(r'\\\$', '$', text)
    text = re.sub(r'\\#', '#', text)

    # Remove spacing/layout commands entirely (command + argument discarded)
    text = re.sub(r'\\(?:v|h)space\*?\{[^}]*\}', '', text)
    text = re.sub(r'\\(?:vskip|hskip)\s+[0-9a-z.]+', '', text)
    text = re.sub(r'\\(?:smallskip|medskip|bigskip|noindent|newline|linebreak|pagebreak|clearpage|newpage)\b\*?', '', text)

    # Remove \rule{}{} remnants (standalone rules are handled at block level)
    text = re.sub(r'\\rule\{[^}]*\}\{[^}]*\}', '', text)

    # Convert text formatting
    text = re.sub(r'\\textbf\{([^}]+)\}', r'<strong>\1</strong>', text)
    text = re.sub(r'\\textit\{([^}]+)\}', r'<em>\1</em>', text)
    text = re.sub(r'\\emph\{([^}]+)\}', r'<em>\1</em>', text)

    # Remove other LaTeX commands
    text = re.sub(r'\\[a-zA-Z]+\*?\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+\*?', '', text)

    # Clean up spacing
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    return text


def convert_content(content):
    """Convert LaTeX content to HTML"""
    html = ""

    # First, extract table environments (including longtable) to prevent them from being split
    # We'll replace them with placeholders, process normally, then restore them
    table_placeholders = {}
    placeholder_counter = [0]  # Use list to allow modification in nested function

    def replace_table(match):
        placeholder = f"___TABLE_PLACEHOLDER_{placeholder_counter[0]}___"
        table_placeholders[placeholder] = match.group(0)
        placeholder_counter[0] += 1
        return placeholder

    # Extract longtable, table, standalone tabular, and todolist environments
    content = re.sub(r'\\begin\{longtable\}.*?\\end\{longtable\}', replace_table, content, flags=re.DOTALL)
    content = re.sub(r'\\begin\{table\}.*?\\end\{table\}', replace_table, content, flags=re.DOTALL)
    # Only match standalone tabular (not inside table)
    content = re.sub(r'\\begin\{center\}[^\\]*\\begin\{tabular\}.*?\\end\{tabular\}[^\\]*\\end\{center\}', replace_table, content, flags=re.DOTALL)
    content = re.sub(r'\\begin\{todolist\}.*?\\end\{todolist\}', replace_table, content, flags=re.DOTALL)

    # Split into blocks
    blocks = re.split(r'\n\n+', content)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Check if this block contains a table placeholder and restore it
        if block in table_placeholders:
            block = table_placeholders[block]
        else:
            # Check if a placeholder is embedded in this block (e.g., wrapped
            # in \begin{center}...\end{center} or preceded by comments)
            for ph_key, ph_val in table_placeholders.items():
                if ph_key in block:
                    block = ph_val
                    break

        # Skip blocks that are just environment endings
        if re.match(r'^\\end\{(itemize|enumerate|todolist|figure|table|tabular|longtable|verbatim|quote|center)\}$', block):
            continue

        # Handle \rule{}{} as a standalone horizontal divider
        if re.match(r'^\s*(?:\\noindent\s*)?\\rule\{[^}]*\}\{[^}]*\}\s*$', block):
            html += '<hr>\n'
            continue

        # Handle verbatim (code blocks) - must come before other checks
        if '\\begin{verbatim}' in block:
            html += convert_verbatim(block)
        # Handle todolist (checklist) - before itemize so it isn't misrouted
        elif '\\begin{todolist}' in block:
            html += convert_todolist(block)
        # Handle itemize (bullet lists)
        elif '\\begin{itemize}' in block:
            html += convert_itemize(block)
        # Handle enumerate (numbered lists)
        elif '\\begin{enumerate}' in block:
            html += convert_enumerate(block)
        # Handle tables (including restored longtable placeholders)
        elif '\\begin{table}' in block or '\\begin{tabular}' in block or '\\begin{longtable}' in block:
            html += convert_table(block)
        # Handle figures
        elif '\\begin{figure}' in block or '\\includegraphics' in block:
            html += convert_figure(block)
        # Regular paragraph
        else:
            # Clean up LaTeX commands
            para = clean_latex(block)
            if para:
                html += f'<p>{para}</p>\n\n'

    return html


def convert_section(section_text, section_level='h2'):
    """Convert a section to HTML"""
    # Extract section title
    title_match = re.search(r'\\(?:sub)?section\*?\{([^}]+)\}', section_text)
    if not title_match:
        return ""

    title = title_match.group(1)
    section_id = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

    html = f'<section role="region" aria-labelledby="{section_id}">\n'
    html += f'<{section_level} id="{section_id}">{title}</{section_level}>\n'

    # Get content after section title
    content = section_text[title_match.end():]

    # Convert content
    html += convert_content(content)
    html += '</section>\n\n'

    return html


def backend_custom(tex_file, css_path="../../css/accessible-lab.css"):
    """
    Custom Python parser backend
    Fast, generates clean semantic HTML with full control
    """
    # Read .tex file
    tex_path = Path(tex_file)
    with open(tex_file, 'r', encoding='utf-8') as f:
        tex_content = f.read()

    # Preprocess to expand \input{} and \include{} commands
    tex_content = preprocess_inputs(tex_content, tex_path.parent)

    # Extract metadata
    title = extract_title(tex_content)
    author_info = extract_author_info(tex_content)

    # Get PDF filename for accessibility notice
    pdf_file = Path(tex_file).with_suffix('.pdf').name

    # Extract document body
    body_match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', tex_content, re.DOTALL)
    if not body_match:
        print(f"Error: No document environment found in {tex_file}", file=sys.stderr)
        return False

    body = body_match.group(1)

    # Extract sections for TOC
    sections = extract_sections(body)
    toc_html = generate_toc(sections)

    # Generate breadcrumbs
    breadcrumb_html = generate_breadcrumbs(tex_file, title)

    # Build author info lines (conditionally include or comment out)
    website_line = f'            <p>Website: <a href="{author_info["website"]}">{author_info["website"]}</a></p>\n' if author_info['website'] else '            <!-- <p>Website: <a href="https://example.com">https://example.com</a></p> -->\n'
    github_line = f'            <p>GitHub: <a href="https://github.com/{author_info["github"]}" aria-label="GitHub profile">{author_info["github"]}</a></p>\n' if author_info['github'] else '            <!-- <p>GitHub: <a href="https://github.com/username" aria-label="GitHub profile">username</a></p> -->\n'

    # Start HTML
    html = f'''<!DOCTYPE html>
<html lang="en-US">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link href="{css_path}" rel="stylesheet" type="text/css">
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to main content</a>
    <header role="banner">
        <h1>{title}</h1>
        <div class="author">
            <p>{author_info['name']}</p>
{website_line}{github_line}        </div>
    </header>

{breadcrumb_html}    <main role="main" id="main-content">
        <section role="region" aria-labelledby="pdf-version-notice" class="accessibility-notice">
            <h2 id="pdf-version-notice">PDF Version Available</h2>
            <p>This document is also available in PDF format: <a href="{pdf_file}">{pdf_file}</a></p>
            <p>The PDF version includes bookmarks for easy navigation and is optimized for printing.</p>
        </section>

{toc_html}'''

    # Split into sections
    sections = re.split(r'(\\(?:sub)?section\*?\{[^}]+\})', body)

    current_section = ""
    for i, part in enumerate(sections):
        if re.match(r'\\(?:sub)?section\*?\{', part):
            # This is a section header
            if current_section:
                html += convert_section(current_section)
            current_section = part
        else:
            current_section += part

    # Process last section
    if current_section:
        html += convert_section(current_section)

    # Close HTML
    html += '''    </main>
</body>
</html>
'''

    # Write HTML file
    html_file = Path(tex_file).with_suffix('.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)

    return html_file


def backend_pandoc(tex_file, css_path="../../css/accessible-lab.css"):
    """
    Pandoc backend
    Robust LaTeX parsing, good for complex documents

    Note: Pandoc can handle \input{} natively, but we preprocess anyway
    to ensure consistent behavior across all backends and better error reporting.
    """
    tex_path = Path(tex_file)
    html_file = tex_path.with_suffix('.html')

    # Read and preprocess the tex file to expand \input{} commands
    try:
        with open(tex_file, 'r', encoding='utf-8') as f:
            tex_content = f.read()

        # Preprocess to expand inputs
        tex_content = preprocess_inputs(tex_content, tex_path.parent)

        # Extract title for metadata
        title_match = re.search(r'\\title\{([^}]+)\}', tex_content)
        title = title_match.group(1) if title_match else None

        # Create temporary preprocessed file
        temp_tex = tex_path.parent / f"{tex_path.stem}_pandoc_temp.tex"
        with open(temp_tex, 'w', encoding='utf-8') as f:
            f.write(tex_content)

    except Exception as e:
        print(f"Error: Failed to preprocess {tex_file}: {e}", file=sys.stderr)
        return None

    # Build pandoc command (use temp file)
    cmd = [
        'pandoc',
        str(temp_tex),
        '--from', 'latex',
        '--to', 'html5',
        '--standalone',
        '--metadata', 'lang=en-US',
        '--css', css_path,
        '--output', str(html_file)
    ]

    if title:
        cmd.extend(['--metadata', f'title={title}'])

    # Run pandoc
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return html_file
    except subprocess.CalledProcessError as e:
        print(f"Error: pandoc conversion failed: {e.stderr}", file=sys.stderr)
        return None
    finally:
        # Clean up temporary file
        if temp_tex.exists():
            temp_tex.unlink()


def backend_htlatex(tex_file, css_path="../../css/accessible-lab.css"):
    """
    htlatex backend
    Best for complex LaTeX with custom packages
    """
    tex_path = Path(tex_file)
    base_name = tex_path.stem
    html_file = tex_path.with_suffix('.html')
    temp_tex = tex_path.parent / f"{base_name}_temp.tex"

    try:
        # Read original .tex file
        with open(tex_file, 'r', encoding='utf-8') as f:
            tex_content = f.read()

        # Preprocess to expand \input{} and \include{} commands
        tex_content = preprocess_inputs(tex_content, tex_path.parent)

        # Create temporary tex file without accessibility package
        # (htlatex has issues with the accessibility package)
        cleaned_content = re.sub(
            r'\\usepackage\[tagged, highstructure\]\{accessibility\}',
            '',
            tex_content
        )

        with open(temp_tex, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

        # Run htlatex
        cmd = [
            'htlatex',
            str(temp_tex),
            'xhtml,charset=utf-8,fn-in',
            ' -cunihtf -utf8'
        ]

        result = subprocess.run(
            cmd,
            cwd=tex_path.parent,
            capture_output=True,
            text=True
        )

        # Move generated HTML to correct name
        temp_html = tex_path.parent / f"{base_name}_temp.html"
        if temp_html.exists():
            temp_html.rename(html_file)

            # Clean up temporary files
            for pattern in ['*.aux', '*.log', '*.4ct', '*.4tc', '*.dvi',
                          '*.idv', '*.lg', '*.tmp', '*.xref', '*.css']:
                for temp_file in tex_path.parent.glob(f"{base_name}_temp.*"):
                    temp_file.unlink(missing_ok=True)
                for temp_file in tex_path.parent.glob(f"{base_name}.{pattern[2:]}"):
                    if temp_file.stem == base_name:
                        temp_file.unlink(missing_ok=True)

            return html_file
        else:
            print(f"Error: htlatex did not generate expected output", file=sys.stderr)
            return None

    except Exception as e:
        print(f"Error: htlatex conversion failed: {e}", file=sys.stderr)
        return None
    finally:
        # Remove temporary tex file
        if temp_tex.exists():
            temp_tex.unlink()


# ============================================================================
# Main Conversion Function
# ============================================================================

def convert_tex_to_html(tex_file, backend=None, css_path="../../css/accessible-lab.css"):
    """
    Main conversion function

    Args:
        tex_file: Path to .tex file
        backend: 'custom', 'pandoc', 'htlatex', or None for auto-detect
        css_path: Path to CSS file

    Returns:
        True if successful, False otherwise
    """
    tex_path = Path(tex_file)

    if not tex_path.exists():
        print(f"Error: File {tex_file} not found", file=sys.stderr)
        return False

    # Determine backend
    if backend is None:
        backend = get_best_backend()
        print(f"Auto-selected backend: {backend}")

    # Verify backend is available
    available = detect_available_backends()
    if backend not in available or not available[backend]:
        print(f"Error: Backend '{backend}' is not available", file=sys.stderr)
        print(f"Available backends: {[k for k, v in available.items() if v]}", file=sys.stderr)
        return False

    # Run conversion
    print(f"Converting {tex_file} using {backend} backend...")

    html_file = None
    if backend == 'custom':
        html_file = backend_custom(tex_file, css_path)
    elif backend == 'pandoc':
        html_file = backend_pandoc(tex_file, css_path)
    elif backend == 'htlatex':
        html_file = backend_htlatex(tex_file, css_path)
    else:
        print(f"Error: Unknown backend '{backend}'", file=sys.stderr)
        return False

    if not html_file:
        return False

    # Post-process HTML (except for custom backend which already generates clean HTML)
    if backend != 'custom':
        print(f"Post-processing HTML...")
        post_process_html(html_file, css_path)

    print(f"✓ Created {html_file}")
    return True


# ============================================================================
# Command-Line Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Convert LaTeX .tex files to accessible HTML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Backends:
  custom   - Fast Python parser, clean semantic HTML (always available)
  pandoc   - Robust LaTeX parsing via pandoc (requires pandoc)
  htlatex  - Complex document support via htlatex (requires TeX4ht)

Examples:
  %(prog)s myfile.tex                    # Auto-detect best backend
  %(prog)s --backend=pandoc myfile.tex   # Use pandoc explicitly
  %(prog)s --list-backends               # Show available backends
        '''
    )

    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )

    parser.add_argument('tex_file', nargs='?', help='.tex file to convert')
    parser.add_argument(
        '--backend',
        choices=['custom', 'pandoc', 'htlatex'],
        help='Conversion backend (default: auto-detect)'
    )
    parser.add_argument(
        '--css',
        default='../../css/accessible-lab.css',
        help='Path to CSS file (default: ../../css/accessible-lab.css)'
    )
    parser.add_argument(
        '--list-backends',
        action='store_true',
        help='List available backends and exit'
    )

    args = parser.parse_args()

    # Handle --list-backends
    if args.list_backends:
        available = detect_available_backends()
        print("Available backends:")
        for backend, is_available in available.items():
            status = "✓" if is_available else "✗"
            print(f"  {status} {backend}")
        sys.exit(0)

    # Require tex_file if not listing backends
    if not args.tex_file:
        parser.error("the following arguments are required: tex_file")

    # Convert
    success = convert_tex_to_html(args.tex_file, args.backend, args.css)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
