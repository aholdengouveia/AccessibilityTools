#!/bin/bash
# Update both PDF and HTML outputs from a .tex file
# This script prompts for the .tex file location and generates both formats
# Usage: ./update-tex-outputs.sh

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "  TEX to PDF and HTML Converter"
echo "========================================="
echo ""

# Function to prompt for file path
get_tex_file() {
    while true; do
        echo -n "Enter the path to your .tex file (or 'q' to quit): "
        read -r input

        # Check for quit
        if [[ "$input" == "q" ]] || [[ "$input" == "Q" ]]; then
            echo "Exiting..."
            exit 0
        fi

        # Expand tilde to home directory
        input="${input/#\~/$HOME}"

        # Check if file exists
        if [[ ! -f "$input" ]]; then
            echo -e "${RED}Error: File not found: $input${NC}"
            echo "Please check the path and try again."
            echo ""
            continue
        fi

        # Check if file has .tex extension
        if [[ ! "$input" == *.tex ]]; then
            echo -e "${YELLOW}Warning: File does not have .tex extension${NC}"
            echo -n "Continue anyway? (y/n): "
            read -r confirm
            if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
                echo ""
                continue
            fi
        fi

        # File is valid
        TEX_FILE="$input"
        return 0
    done
}

# Function to check required tools
check_dependencies() {
    local missing_tools=()

    if ! command -v pdflatex &> /dev/null; then
        missing_tools+=("pdflatex (install with: sudo apt-get install texlive-latex-base)")
    fi

    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    fi

    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        echo -e "${RED}Error: Missing required tools:${NC}"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        exit 1
    fi

    # Check for tex-to-html.py script
    if [[ ! -f "$SCRIPT_DIR/tex-to-html.py" ]]; then
        echo -e "${RED}Error: tex-to-html.py not found in tools directory${NC}"
        echo "Expected location: $SCRIPT_DIR/tex-to-html.py"
        exit 1
    fi
}

# Function to compile PDF
compile_pdf() {
    local tex_file="$1"
    local tex_dir=$(dirname "$tex_file")
    local tex_basename=$(basename "$tex_file")
    local pdf_file="${tex_file%.tex}.pdf"

    echo -e "${YELLOW}Compiling PDF...${NC}"

    # Change to the directory containing the .tex file
    cd "$tex_dir"

    # Run pdflatex (redirect verbose output but show errors)
    if pdflatex -interaction=nonstopmode "$tex_basename" > /dev/null 2>&1; then
        # Run twice to resolve references
        pdflatex -interaction=nonstopmode "$tex_basename" > /dev/null 2>&1

        # Clean up auxiliary files
        rm -f *.aux *.log *.out *.toc

        echo -e "${GREEN}✓ PDF created: $pdf_file${NC}"
        return 0
    else
        echo -e "${RED}✗ PDF compilation failed${NC}"
        echo "Run 'pdflatex $tex_basename' manually to see detailed errors"
        return 1
    fi
}

# Function to compile HTML
compile_html() {
    local tex_file="$1"
    local html_file="${tex_file%.tex}.html"

    echo -e "${YELLOW}Generating HTML...${NC}"

    if python3 "$SCRIPT_DIR/tex-to-html.py" "$tex_file"; then
        echo -e "${GREEN}✓ HTML created: $html_file${NC}"
        return 0
    else
        echo -e "${RED}✗ HTML generation failed${NC}"
        return 1
    fi
}

# Function to show file info
show_file_info() {
    local file="$1"
    local file_dir=$(dirname "$file")
    local file_name=$(basename "$file")
    local abs_path=$(cd "$file_dir" && pwd)/"$file_name"

    echo ""
    echo "File Information:"
    echo "  Name:      $file_name"
    echo "  Directory: $abs_path"
    echo "  Size:      $(du -h "$file" | cut -f1)"
    echo ""
}

# Main execution
main() {
    # Check dependencies
    check_dependencies

    # Get .tex file from user
    get_tex_file

    # Show file info
    show_file_info "$TEX_FILE"

    # Confirm before proceeding
    echo -n "Generate PDF and HTML from this file? (y/n): "
    read -r confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Operation cancelled."
        exit 0
    fi

    echo ""
    echo "Starting conversion..."
    echo ""

    # Track success
    pdf_success=0
    html_success=0

    # Compile PDF
    if compile_pdf "$TEX_FILE"; then
        pdf_success=1
    fi

    echo ""

    # Compile HTML
    if compile_html "$TEX_FILE"; then
        html_success=1
    fi

    # Summary
    echo ""
    echo "========================================="
    echo "  Conversion Summary"
    echo "========================================="

    if [[ $pdf_success -eq 1 ]]; then
        echo -e "${GREEN}✓ PDF: Success${NC}"
    else
        echo -e "${RED}✗ PDF: Failed${NC}"
    fi

    if [[ $html_success -eq 1 ]]; then
        echo -e "${GREEN}✓ HTML: Success${NC}"
    else
        echo -e "${RED}✗ HTML: Failed${NC}"
    fi

    echo "========================================="

    # Exit with error if both failed
    if [[ $pdf_success -eq 0 ]] && [[ $html_success -eq 0 ]]; then
        exit 1
    fi
}

# Run main function
main
