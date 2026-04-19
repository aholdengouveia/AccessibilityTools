#!/usr/bin/env python3
"""
Add lab PDF and HTML links to topic HTML files

This tool automatically adds lab assignment links to topic pages.
It looks for HTML files in a directory and adds links to matching
labs in the labs/ subdirectory.

Usage:
    python3 add-lab-links.py <directory>

Example:
    python3 add-lab-links.py /path/to/IntroLinux
    python3 add-lab-links.py ../IntroData

Directory structure expected:
    directory/
        topic1.html          # Topic page
        topic2.html          # Topic page
        resources.html       # (skipped)
        labs/
            topic1.html      # Matching lab
            topic1.pdf       # Matching lab PDF
            topic2.html
            topic2.pdf
"""

import sys
import re
from pathlib import Path

def add_lab_links(content, lab_name):
    """Add links to matching lab HTML and PDF in the suggested activities section"""

    # First, remove old format links if they exist
    old_pattern1 = r'\s*<li><a href="labs/' + re.escape(lab_name) + r'\.html">Lab Assignment \(HTML\)</a> - Accessible web version</li>\s*\n'
    old_pattern2 = r'\s*<li><a href="labs/' + re.escape(lab_name) + r'\.pdf">Lab Assignment \(PDF\)</a> - Printable version</li>\s*\n'
    content = re.sub(old_pattern1, '', content)
    content = re.sub(old_pattern2, '', content)

    # Check if new format links already exist
    if f'Lab assignment: <a href="labs/{lab_name}.pdf">PDF version</a>' in content:
        return content, False

    # Pattern to find the suggested activities section
    # Look for the opening <ul> after "Suggested Activities and Discussion Topics:"
    pattern = r'(<p>Suggested Activities and Discussion Topics:\s*<ul>)'

    # Create the lab links to insert
    lab_links = f'''        <li>Lab assignment: <a href="labs/{lab_name}.pdf">PDF version</a> (<a href="labs/{lab_name}.html">accessible HTML version</a>)</li>
'''

    # Insert the links right after the opening <ul>
    replacement = r'\1\n' + lab_links
    new_content = re.sub(pattern, replacement, content)

    if new_content != content:
        return new_content, True

    return content, False

def main():
    # Check for directory argument
    if len(sys.argv) < 2:
        print("❌ Error: Missing directory argument")
        print("\nUsage: python3 add-lab-links.py <directory>")
        print("\nExample:")
        print("  python3 add-lab-links.py /path/to/IntroLinux")
        print("  python3 add-lab-links.py ../IntroData")
        print("\nExpected structure:")
        print("  directory/")
        print("    topic1.html")
        print("    topic2.html")
        print("    labs/")
        print("      topic1.html")
        print("      topic1.pdf")
        sys.exit(1)

    # Get directory from command line
    target_dir = Path(sys.argv[1])

    # Validate directory exists
    if not target_dir.exists():
        print(f"❌ Error: Directory not found: {target_dir}")
        print("\nSuggestions:")
        print("  • Check the path is correct")
        print("  • Use 'ls' to see available directories")
        sys.exit(1)

    if not target_dir.is_dir():
        print(f"❌ Error: {target_dir} is not a directory")
        sys.exit(1)

    # Check if labs subdirectory exists
    labs_dir = target_dir / 'labs'
    if not labs_dir.exists():
        print(f"❌ Error: No 'labs' subdirectory found in {target_dir}")
        print(f"\nExpected: {labs_dir}")
        print("\nThis tool requires a 'labs/' subdirectory with lab HTML/PDF files.")
        sys.exit(1)

    print(f"Processing HTML files in: {target_dir}")
    print(f"Looking for labs in: {labs_dir}\n")

    # Get all HTML files (excluding resources.html)
    html_files = list(target_dir.glob('*.html'))

    modified_count = 0

    for html_file in sorted(html_files):
        # Skip resources.html
        if html_file.name == 'resources.html':
            continue

        lab_name = html_file.stem  # filename without extension

        # Check if matching lab exists
        lab_html = labs_dir / f'{lab_name}.html'
        if not lab_html.exists():
            print(f"○ Skipping {html_file.name} - no matching lab found")
            continue

        # Read file
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Add lab links
        new_content, modified = add_lab_links(content, lab_name)

        if modified:
            # Write back
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ Added lab links to {html_file.name}")
            modified_count += 1
        else:
            print(f"○ {html_file.name} already has lab links")

    print(f"\n✓ Modified {modified_count} files")

if __name__ == '__main__':
    main()
