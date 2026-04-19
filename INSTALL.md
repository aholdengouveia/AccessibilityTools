# Installation Guide

## Installing Pandoc (Recommended)

Pandoc is the best tool for converting .tex to HTML, especially with the accessibility package.

### Option 1: From Ubuntu repositories (easiest)
```bash
sudo apt-get update
sudo apt-get install pandoc
```

### Option 2: Download latest version directly
```bash
# Download the latest .deb file
wget https://github.com/jgm/pandoc/releases/download/3.1.11/pandoc-3.1.11-1-amd64.deb

# Install it
sudo dpkg -i pandoc-3.1.11-1-amd64.deb

# Clean up
rm pandoc-3.1.11-1-amd64.deb
```

### Option 3: Using snap
```bash
sudo snap install pandoc
```

## Installing Watch Tools (Optional)

For automatic conversion when files change:

```bash
sudo apt-get install inotify-tools entr
```

## Verify Installation

```bash
pandoc --version
inotifywait --help
```

## Why Pandoc?

The .tex files use the `accessibility` package which has PDF-specific commands that don't work with make4ht/htlatex. Pandoc handles these correctly and produces cleaner HTML.

## Test After Installation

```bash
cd IntroData/labs
make                 # Should work now!
```

## Troubleshooting

If pandoc installation fails, you may need to:
1. Update your package list: `sudo apt-get update`
2. Fix any broken dependencies: `sudo apt-get install -f`
3. Try the direct download method (Option 2 above)
