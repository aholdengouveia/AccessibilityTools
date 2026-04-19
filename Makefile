# Makefile to automatically convert .tex files to HTML
# Usage:
#   make              - Convert all .tex files to HTML
#   make whatisdata   - Convert only whatisdata.tex
#   make clean        - Remove generated HTML and CSS files
#   make watch        - Watch for changes and auto-convert (requires entr)

# Find the tools directory and Python converter
TOOLS_DIR := $(dir $(lastword $(MAKEFILE_LIST)))
CONVERTER := $(TOOLS_DIR)tex-to-html.py

# Find all .tex files in current directory
TEX_FILES := $(wildcard *.tex)
HTML_FILES := $(TEX_FILES:.tex=.html)

# Default target: convert all .tex files
all: $(HTML_FILES)

# Rule to convert .tex to .html using the clean Python converter
%.html: %.tex
	@python3 $(CONVERTER) $<


# Watch for changes and auto-convert
watch:
	@if command -v entr > /dev/null; then \
		echo "Watching for changes in .tex files... (Press Ctrl+C to stop)"; \
		ls *.tex | entr -c make all; \
	else \
		echo "Error: 'entr' is not installed."; \
		echo "Install with: sudo apt-get install entr"; \
		exit 1; \
	fi

# Clean generated files
clean:
	@echo "Cleaning generated HTML files..."
	@rm -f $(HTML_FILES)
	@rm -f *.4ct *.4tc *.aux *.css *.dvi *.idv *.lg *.log *.tmp *.xref
	@echo "✓ Cleaned"

# Help
help:
	@echo "Makefile for converting .tex files to HTML"
	@echo ""
	@echo "Targets:"
	@echo "  make          - Convert all .tex files to HTML"
	@echo "  make <file>   - Convert specific .tex file (without .tex extension)"
	@echo "  make watch    - Watch for changes and auto-convert (requires entr)"
	@echo "  make clean    - Remove generated HTML files"
	@echo "  make help     - Show this help message"
	@echo ""
	@echo "Features:"
	@echo "  - Generates clean, accessible HTML5"
	@echo "  - Semantic structure with proper ARIA labels"
	@echo "  - No complex LaTeX-generated classes"
	@echo ""
	@echo "Requirements:"
	@echo "  - Python 3 (usually pre-installed)"
	@echo "  - entr: For watch mode (optional - sudo apt-get install entr)"

.PHONY: all watch clean help
