# Installation Guide

## Requirements

| Tool | Required for | Install |
|------|-------------|---------|
| Python 3 | Everything | Usually pre-installed |
| pdflatex | PDF generation, `validate` command | See LaTeX section below |
| pandoc | `--backend=pandoc`, PDF reports | See pandoc section below |
| entr | `make watch` (auto-convert on save) | `sudo apt-get install entr` |
| tqdm | `--progress` flag | `pip install tqdm` |

---

## Python 3

Python 3 is required for all tools. Check your version:

```bash
python3 --version
```

Most Linux and macOS systems have Python 3 pre-installed. For Windows, download from [python.org](https://www.python.org/downloads/).

---

## LaTeX (for PDF generation and `validate`)

### Ubuntu / Debian
```bash
sudo apt-get install texlive-latex-base texlive-fonts-recommended
```

### macOS
Install [MacTeX](https://www.tug.org/mactex/).

### Windows
Install [MiKTeX](https://miktex.org) or [TeX Live](https://www.tug.org/texlive/).

---

## Pandoc (for `--backend=pandoc` and PDF reports)

### Option 1: From system repositories
```bash
sudo apt-get update && sudo apt-get install pandoc
```

### Option 2: Download latest directly (Ubuntu/Debian)
```bash
wget https://github.com/jgm/pandoc/releases/download/3.1.11/pandoc-3.1.11-1-amd64.deb
sudo dpkg -i pandoc-3.1.11-1-amd64.deb
rm pandoc-3.1.11-1-amd64.deb
```

### Option 3: Snap
```bash
sudo snap install pandoc
```

---

## Optional: tqdm (progress bar)

Enables the `--progress` flag for batch operations:

```bash
pip install tqdm
```

Without it, `--progress` falls back to standard output with a clear message.

---

## Optional: entr (auto-convert on file save)

Enables `make watch` to automatically re-convert `.tex` files when they change:

```bash
sudo apt-get install entr
```

---

## Verify Installation

```bash
# Check the accessibility tool
python3 latex-accessibility.py --version

# Check pdflatex
pdflatex --version

# Check pandoc (optional)
pandoc --version

# Run the built-in package checker
python3 latex-accessibility.py check-packages
```

---

## Troubleshooting

**`python3: command not found`**
Install Python 3 for your OS (see above).

**`pdflatex: command not found`**
Install a LaTeX distribution (see above). On Ubuntu: `sudo apt-get install texlive-latex-base`.

**pandoc installation fails**
Try `sudo apt-get update` first, then `sudo apt-get install -f` to fix broken dependencies. If that doesn't work, use the direct download (Option 2).

**`--progress` shows a warning about tqdm**
Run `pip install tqdm` to enable the progress bar. The tool works fine without it.
