# PDF Compressor CLI

A Python command-line tool that **compresses large PDF files (1GB+)** down to a size small enough for AI tools like **Claude** or **ChatGPT** to upload and read (<100MB, ideally <30MB).

It processes PDFs page-by-page, so it **never loads the whole file into RAM** — well-suited for scanned documents and files packed with high-quality images.

```bash
# One-shot installer (macOS, Linux). Default backend is pipx (recommended):
curl -fsSL https://raw.githubusercontent.com/repo-phuocdt/pdf-compressor-cli/master/install.sh | bash

# Then just:
pdf-compressor-cli /path/to/big.pdf
```

> **Why not `brew install pdf-compressor-cli`?** Homebrew only searches its default registry (`homebrew-core`), and this tool lives in a personal repo. You have to tap first (`brew tap ...`). More importantly, the Homebrew formula builds PyMuPDF from source, which often fails on macOS without the right SDK. `pipx` uses prebuilt PyPI wheels and finishes in seconds — so the installer uses `pipx` by default. Force the Homebrew path with `METHOD=brew curl ... | bash` if you prefer it.

---

## Features

- **Interactive shell**: run with no arguments to open a Claude Code–style REPL with slash commands (`/preset`, `/target`, `/compress`, …). State persists between commands, so you can compress many files in one session.
- **Wizard mode** (`--wizard`): a one-shot step-by-step prompt that asks each option, then exits.
- Compress embedded images (downscale DPI + re-encode as JPEG) via three presets: `low` / `medium` / `high`.
- **`--rasterize` mode**: render each page as a JPEG at target DPI — drops vector/text content but is the most aggressive path. Ideal for AI vision which reads the page as an image anyway.
- Smart DPI detection: uses each image's actual placement rectangle (via `page.get_image_info`) to compute effective rendered DPI, so embedded images that don't span the full page still get correctly downscaled.
- Binary-search JPEG quality to hit a **target size** in MB.
- Pick a **page range** such as `1-50` or `1,3,5-10`.
- **Split** output into multiple smaller files by max size.
- Optional **OCR** for scanned PDFs (adds an invisible text layer).
- Pretty progress bar + summary table.
- Strips metadata and runs garbage collection to minimize size.
- Handles Ctrl+C gracefully and cleans up temp files.
- Detects encrypted PDFs and fails with a clear error.

---

## Requirements

- **macOS** (Apple Silicon or Intel)
- **Python 3.9+**
- **Homebrew** (used to install `tesseract` for OCR)

---

## Installation

Once installed, just run `pdf-compressor-cli <file>` from any terminal — **no source clone, no venv activation required**.

### Option 1: One-shot installer (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/repo-phuocdt/pdf-compressor-cli/master/install.sh | bash
```

The installer uses `pipx` under the hood (fast, reliable, uses prebuilt wheels). It bootstraps `pipx` via Homebrew or `pip --user` if missing, installs `tesseract` for OCR, and places `pdf-compressor-cli` on your `$PATH`.

### Option 2: pipx (manual)

```bash
pipx install git+https://github.com/repo-phuocdt/pdf-compressor-cli.git
```

If you don't have pipx yet: `brew install pipx && pipx ensurepath`. For OCR: `brew install tesseract`.

### Option 3: Homebrew tap (advanced)

> Heads up: the Homebrew formula builds **PyMuPDF from source**, which requires the Xcode Command Line Tools and can take several minutes. If that fails on your machine, use Option 1 or 2 instead.

```bash
METHOD=brew curl -fsSL https://raw.githubusercontent.com/repo-phuocdt/pdf-compressor-cli/master/install.sh | bash
```

Or the two steps manually:

```bash
brew tap repo-phuocdt/pdf-compressor-cli https://github.com/repo-phuocdt/pdf-compressor-cli.git
brew install pdf-compressor-cli
```

To always track the latest master commit: `brew install --HEAD pdf-compressor-cli`.

### Option 4: pip (global install)

```bash
pip install git+https://github.com/repo-phuocdt/pdf-compressor-cli.git
```

### Option 5: Clone and run from source (for development)

```bash
git clone https://github.com/repo-phuocdt/pdf-compressor-cli.git
cd pdf-compressor-cli
chmod +x setup.sh && ./setup.sh
source venv/bin/activate
pdf-compressor-cli --help
```

`setup.sh` checks for Homebrew, installs `tesseract`, creates a venv, and runs `pip install -e .`.

---

## Quick start

### Interactive shell (claudekit-style REPL) — default

Run with no arguments and the tool opens an **interactive shell** inspired by Claude Code: type slash commands, state persists between commands, and you can compress many files without exiting:

```bash
pdf-compressor-cli
# or
pdf-compressor-cli -I
# or pre-load a file:
pdf-compressor-cli -i big.pdf -I
```

Example session:

```
pdf-compressor› /help                      # list all commands
pdf-compressor› /preset low                # change the preset
pdf-compressor› /target 25                 # target output size = 25 MB
pdf-compressor› /pages 1-50                # only the first 50 pages
pdf-compressor› /rasterize on              # aggressive mode for scans
pdf-compressor› /status                    # show current settings
pdf-compressor› big.pdf                    # just paste a path → compress
pdf-compressor› another.pdf                # next file, same settings
pdf-compressor› /target off                # clear target, back to preset
pdf-compressor› /exit                      # quit
```

#### Slash commands

| Command | Description |
| --- | --- |
| `/help`, `/?` | Show the command table |
| `/status`, `/show` | Show current settings |
| `/preset <low\|medium\|high>` | Change quality preset |
| `/target <MB> \| off` | Set target output size |
| `/dpi <N> \| off` | Override preset DPI |
| `/pages <range> \| all` | Set page range (`"1-50"` / `"1,3,5-10"`) |
| `/split <MB> \| off` | Split output into chunks |
| `/ocr on\|off` | Toggle OCR (no argument = toggle) |
| `/rasterize on\|off` | Aggressive: render each page as a JPEG |
| `/verbose on\|off` | Toggle verbose logging |
| `/output <path> \| default` | Set output path |
| `/compress <path>` | Compress a file with current settings |
| `<path>` | Shortcut for `/compress <path>` (paste/drop the file) |
| Enter (blank line) | Re-run on the most recent file |
| `/reset` | Reset settings to defaults |
| `/clear`, `/cls` | Clear the screen |
| `/exit`, `/quit`, `q`, Ctrl+D | Exit the shell |

**Tip**: Ctrl+C at the prompt cancels the current line (it does not exit the shell). Ctrl+C during compression aborts the running job and returns you to the shell.

---

### Wizard mode (one-shot, prompts in sequence then exits)

If you only need to run once and want the tool to ask for each option:

```bash
pdf-compressor-cli --wizard
```

The tool asks for input/output/quality/target/pages/split/OCR/verbose in order, shows a confirmation table, then runs and exits.

---

### Flag mode (for power users / scripts)

#### 1. Basic compression with the default `medium` preset

```bash
pdf-compressor-cli big.pdf
# or
pdf-compressor-cli -i big.pdf
```

Default output: `big_compressed.pdf` next to the input.

#### 2. Aggressive compression with the low preset

```bash
pdf-compressor-cli big.pdf -q low -o tiny.pdf
```

#### 3. Maximum compression — rasterize every page

```bash
pdf-compressor-cli big.pdf -q low --rasterize
```

Drops vector/text content and renders each page as a JPEG at the target DPI. Best for scanned docs or when the output is only going to an AI vision model.

#### 4. Compress to a specific target size (e.g. ~25 MB)

```bash
pdf-compressor-cli big.pdf -t 25
```

The tool binary-searches JPEG quality in the range [10, 85] until the output is within ±10% of the target.

#### 5. Process only a page range

```bash
pdf-compressor-cli big.pdf --pages "1-50"
pdf-compressor-cli big.pdf --pages "1,3,5-10"
```

#### 6. Split output into parts ≤ 30 MB each

```bash
pdf-compressor-cli big.pdf --split 30
```

Produces `big_compressed_part1.pdf`, `big_compressed_part2.pdf`, …

#### 7. OCR for scanned PDFs

```bash
pdf-compressor-cli scanned.pdf --ocr
```

Adds an invisible text layer to pages that currently have no text, so AI tools can extract the content.

#### 8. Verbose output

```bash
pdf-compressor-cli big.pdf -v
```

---

## CLI reference

| Flag | Description |
| --- | --- |
| `<file>` (positional) | Input PDF. Omit to open the interactive shell |
| `-i, --input FILE` | Alternate way to pass the input PDF |
| `-I, --interactive` | Force the interactive shell (claudekit-style REPL) |
| `--wizard` | One-shot wizard: prompts for each option, then exits |
| `-o, --output FILE` | Output file (default: `{name}_compressed.pdf`) |
| `-q, --quality TEXT` | Preset: `low` \| `medium` \| `high` (default: `medium`) |
| `-t, --target-size INT` | Target size in MB (triggers binary search) |
| `--dpi INT` | Custom DPI (overrides the preset) |
| `--pages TEXT` | Page range, e.g. `"1-50"` or `"1,3,5-10"` |
| `--split INT` | Split output into chunks of at most N MB |
| `--ocr` | Run OCR on scanned pages (requires `tesseract` + `pytesseract`) |
| `--rasterize` | Render each page as a JPEG at target DPI (drops vector/text content; ideal for AI vision) |
| `-v, --verbose` | Verbose logging |
| `-V, --version` | Show version and exit |
| `-h, --help` | Show help and exit |

---

## Quality presets

| Preset | DPI | JPEG quality | When to use |
| --- | --- | --- | --- |
| `low` | 72 | 30 | Text/AI consumption only — image fidelity doesn't matter |
| `medium` | 150 | 50 | Balanced size vs. quality (default) |
| `high` | 200 | 70 | Preserve image quality, lighter compression |

---

## Notes

- **Encrypted PDFs**: the tool fails fast with a clear error. Decrypt the file with another tool first (e.g. `qpdf --decrypt input.pdf output.pdf`) before running.
- **RAM**: only one page lives in memory at a time, so a 1GB file won't blow up RAM.
- **OCR**: OCR is slow because each page must be rendered and recognized. For 500+ page files, consider narrowing with `--pages`.
- **Target size**: if the target is smaller than the minimum achievable, the tool saves a "best effort" result (closest under/over the target) and warns in verbose mode.
- **Ctrl+C**: during a run, Ctrl+C cleans up temporary files and exits with code 130.

---

## Troubleshooting

**`tesseract: command not found` when using `--ocr`**
→ Install it via Homebrew: `brew install tesseract`.

**`ModuleNotFoundError: fitz`**
→ The venv isn't activated. Run `source venv/bin/activate` and try again.

**The output file is still too large**
→ Try `-q low --rasterize` or combine `-t <MB>` to force a target size. For PDFs packed with vector art or heavy embedded fonts, splitting with `--split` can help.

**`brew install pdf-compressor-cli` hangs or fails on PyMuPDF**
→ The Homebrew formula compiles PyMuPDF from source. Switch to the pipx path (Option 1 or 2) which uses a prebuilt wheel and finishes in seconds.

---

## Project layout

```
pdf-compressor/
├── compress_pdf.py             # Main CLI (single, self-contained file)
├── pyproject.toml              # Package metadata + `pdf-compressor` entry point
├── requirements.txt            # Python dependencies (used by setup.sh)
├── setup.sh                    # Dev setup script for macOS
├── install.sh                  # One-shot pipx/brew install script
├── Formula/
│   └── pdf-compressor-cli.rb   # Homebrew formula
├── scripts/
│   └── gen_formula.py          # Regenerate formula resources from PyPI
└── README.md                   # This file
```

---

## Publishing to Homebrew (for maintainers)

End-users get the tool by tapping this repo and installing the formula that lives here. The one-shot `install.sh` script does both steps for them. When you cut a new release:

### 1. Tag a release on the main repo

```bash
git tag v0.1.0
git push origin v0.1.0
```

GitHub will host the tarball at `https://github.com/repo-phuocdt/pdf-compressor-cli/archive/refs/tags/v0.1.0.tar.gz`.

### 2. Compute the tarball sha256

```bash
curl -sL https://github.com/repo-phuocdt/pdf-compressor-cli/archive/refs/tags/v0.1.0.tar.gz \
    | shasum -a 256
```

### 3. Regenerate the formula with the latest PyPI resources

```bash
pip install -e .       # install the exact versions into the current env
python scripts/gen_formula.py \
    --source-url https://github.com/repo-phuocdt/pdf-compressor-cli/archive/refs/tags/v0.1.0.tar.gz \
    --source-sha256 <sha256-from-step-2>
```

### 4. Commit + push the updated formula

```bash
git add Formula/pdf-compressor-cli.rb
git commit -m "Bump formula to v0.1.0"
git push
```

### 5. End-user install

```bash
# One-shot (pipx under the hood):
curl -fsSL https://raw.githubusercontent.com/repo-phuocdt/pdf-compressor-cli/master/install.sh | bash

# Or force Homebrew:
METHOD=brew curl -fsSL https://raw.githubusercontent.com/repo-phuocdt/pdf-compressor-cli/master/install.sh | bash
```

> **Tip**: test locally before pushing with `brew install --build-from-source ./Formula/pdf-compressor-cli.rb`.
