# Installation Guide

## Requirements

| Tool | Required for | Min version | Install |
|------|-------------|-------------|---------|
| Python 3 | Everything | 3.7+ | Usually pre-installed |
| pdflatex | PDF generation, `validate` | Any | See LaTeX section below |
| pandoc | `--backend=pandoc`, PDF reports | Any | See pandoc section below |
| Node.js | pa11y (HTML auditing) | **14+** | See pa11y section below |
| pa11y | `check-html`, `check-html-all` | Any | See pa11y section below |
| Java | veraPDF (PDF auditing) | 8+ | See veraPDF section below |
| veraPDF | `check-pdf`, `check-pdf-all` | Any | See veraPDF section below |
| entr | `make watch` (auto-convert on save) | Any | `sudo apt-get install entr` |
| tqdm | `--progress` flag | Any | `pip install tqdm` |

---

## Python 3

Python 3 is required for all tools. Check your version:

```bash
python3 --version
```

Most Linux and macOS systems have Python 3 pre-installed. For Windows, download from [python.org](https://www.python.org/downloads/).

**Troubleshooting:**

`python3: command not found`
: Install Python 3 for your OS. On Ubuntu: `sudo apt-get install python3`

`python3 --version` shows 3.6 or lower
: The tool requires Python 3.7+. On Ubuntu 22.04 the default is 3.10, so this is only an issue on older systems. Upgrade with `sudo apt-get install python3.10`.

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

**Troubleshooting:**

`pdflatex: command not found`
: LaTeX is not installed. Run the install command for your OS above.

`LaTeX Error: File 'bookmark.sty' not found`
: The required package isn't in your LaTeX installation. Install the extended package set: `sudo apt-get install texlive-latex-recommended texlive-latex-extra`

`sudo apt-get install texlive-latex-base` fails with dependency errors
: Run `sudo apt-get update` first, then `sudo apt-get install -f` to fix broken dependencies, then retry.

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

**Troubleshooting:**

`pandoc: command not found`
: Install using one of the options above.

`sudo apt-get install pandoc` installs a very old version
: The Ubuntu repositories often have an outdated pandoc. Use Option 2 (direct download) to get the current version.

`dpkg: error processing package`
: Run `sudo apt-get install -f` to fix broken dependencies, then retry.

---

## Optional: pa11y (HTML accessibility auditing)

Enables the `check-html` and `check-html-all` commands for WCAG 2.1 AA auditing of generated HTML files.

### Step 1 — Install Node.js 20 LTS

**Important:** pa11y requires Node.js 14 or higher. The version bundled with Ubuntu 22.04 is v12, which is too old. Install a current version via NodeSource:

```bash
# Remove old Node.js packages first (required to avoid conflicts)
sudo apt-get remove -y nodejs libnode-dev libnode72
sudo apt-get autoremove -y

# Add NodeSource repository and install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

If `libnode72` is not found during removal, that's fine — skip it and continue.

Verify the version — it should show v20.x.x:
```bash
node --version
npm --version
```

### Step 2 — Install pa11y

```bash
npm install -g pa11y
```

Verify:
```bash
pa11y --version
```

**Troubleshooting:**

`npm WARN EBADENGINE ... node: '>= 14' ... current: { node: 'v12' }`
: Your Node.js is too old. Follow Step 1 above to install Node.js 20 via NodeSource, then retry `npm install -g pa11y`.

`npm install -g pa11y` fails with `EACCES permission denied`
: npm is trying to write to a system directory. Fix with: `sudo npm install -g pa11y` or configure npm to use a user-writable directory: `npm config set prefix ~/.npm-global` then add `export PATH="$HOME/.npm-global/bin:$PATH"` to your `~/.bashrc`.

`pa11y: command not found` after installing
: Your PATH doesn't include npm's global bin directory. Run `npm bin -g` to find where pa11y was installed, then add that directory to your PATH.

`curl: command not found`
: Install curl first: `sudo apt-get install curl`

---

## Optional: veraPDF (PDF accessibility auditing)

Enables the `check-pdf` and `check-pdf-all` commands for PDF/UA compliance checking of generated PDFs.

### Step 1 — Install Java

veraPDF requires Java 8 or higher. Check if Java is already installed:

```bash
java -version
```

If not installed:
```bash
sudo apt-get install default-jre
```

### Step 2 — Install veraPDF

1. Download the latest installer jar from the veraPDF GitHub releases page:
   **github.com/veraPDF/veraPDF-apps/releases/latest**
   - Look for a file ending in `-installer.jar` under Assets.
   - Do not use hardcoded version URLs — filenames change with each release and old links return 404.
2. Run the installer (adjust filename to match what you downloaded):
   ```bash
   java -jar ~/Downloads/verapdf-*-installer.jar
   ```
3. Follow the prompts — the default install location (`/opt/verapdf`) works fine.
4. Add veraPDF to your PATH if the installer doesn't do it automatically:
   ```bash
   echo 'export PATH="/opt/verapdf:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

Verify:
```bash
verapdf --version
```

**Troubleshooting:**

`java: command not found`
: Install Java first (Step 1 above).

`404 Not Found` when downloading
: Do not use hardcoded version URLs — they go stale as new releases ship. Go to [github.com/veraPDF/veraPDF-apps/releases/latest](https://github.com/veraPDF/veraPDF-apps/releases/latest) and download the `-installer.jar` from the Assets section.

`verapdf: command not found` after installing
: The install directory isn't in your PATH. Find where veraPDF was installed (the installer will tell you) and add it: `echo 'export PATH="/path/to/verapdf:$PATH"' >> ~/.bashrc && source ~/.bashrc`

`java -jar verapdf-installer.jar` shows a graphical window but you're on a headless server
: Use the console installer: `java -jar verapdf-installer.jar -console`

---

## Optional: tqdm (progress bar)

Enables the `--progress` flag for batch operations:

```bash
pip install tqdm
```

Without it, `--progress` falls back to standard output with a clear message.

**Troubleshooting:**

`pip: command not found`
: Try `pip3 install tqdm` or `python3 -m pip install tqdm`.

`--progress` still shows the tqdm warning after installing
: Make sure you're installing for the same Python that runs the tool: `python3 -m pip install tqdm`

---

## Optional: entr (auto-convert on file save)

Enables `make watch` to automatically re-convert `.tex` files when they change:

```bash
sudo apt-get install entr
```

**Troubleshooting:**

`entr: command not found`
: Install with `sudo apt-get install entr`. If unavailable, use `make` manually instead of `make watch`.

---

## Verify Everything

Run this after installing to confirm each tool is available:

```bash
# Core tool
python3 latex-accessibility.py --version

# LaTeX
pdflatex --version

# Pandoc (optional)
pandoc --version

# Node.js and pa11y (optional)
node --version
pa11y --version

# Java and veraPDF (optional)
java -version
verapdf --version

# Built-in package checker
python3 latex-accessibility.py check-packages
```
