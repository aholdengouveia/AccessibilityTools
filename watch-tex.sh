#!/bin/bash
# Watch for changes to .tex files and automatically convert to HTML
# Usage:
#   ./watch-tex.sh <directory>
#   ./watch-tex.sh                    (uses current directory)

# Set target directory
TARGET_DIR="${1:-.}"

# Check if directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory $TARGET_DIR does not exist"
    exit 1
fi

# Get absolute path
TARGET_DIR=$(cd "$TARGET_DIR" && pwd)

echo "Watching for changes to .tex files in $TARGET_DIR"
echo "Press Ctrl+C to stop"
echo ""

# Check if inotifywait is available
if ! command -v inotifywait &> /dev/null; then
    echo "Error: inotifywait is not installed"
    echo "Install with: sudo apt-get install inotify-tools"
    exit 1
fi

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    echo "Install with: sudo apt-get install python3"
    exit 1
fi

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Initial conversion
echo "Running initial conversion..."
for tex_file in "$TARGET_DIR"/*.tex; do
    if [ -f "$tex_file" ]; then
        python3 "$SCRIPT_DIR/tex-to-html.py" "$tex_file"
    fi
done
echo ""
echo "Now watching for changes..."
echo ""

# Watch for changes and convert
cd "$TARGET_DIR" || exit 1
inotifywait -m -e close_write,moved_to,create --format '%f' *.tex 2>/dev/null | while read file; do
    if [[ "$file" == *.tex ]]; then
        echo "Change detected in $file"
        python3 "$SCRIPT_DIR/tex-to-html.py" "$TARGET_DIR/$file"
        echo ""
    fi
done
