# PDF Compressor CLI

A Python command-line tool that **compresses large PDF files (1GB+)** down to a size small enough for AI tools like **Claude** or **ChatGPT** to upload and read (<100MB, ideally <30MB).

It processes PDFs page-by-page, so it **never loads the whole file into RAM** — well-suited for scanned documents and files packed with high-quality images.

```bash
# Fastest install (recommended) — works on macOS, Linux, Windows:
pipx install git+https://github.com/repo-phuocdt/pdf-compressor-cli.git

pdf-compressor /path/to/big.pdf      # done — no source clone needed
```

> Prefer Homebrew? See the [Homebrew tap option](#option-2-homebrew-tap) below.

---

## Features

- **Interactive shell**: run with no arguments to open a Claude Code–style REPL with slash commands (`/preset`, `/target`, `/compress`, …). State persists between commands, so you can compress many files in one session.
- **Wizard mode** (`--wizard`): a one-shot step-by-step prompt that asks each option, then exits.
- Compress embedded images (downscale DPI + re-encode as JPEG) via three presets: `low` / `medium` / `high`.
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

Once installed, just run `pdf-compressor <file>` from any terminal — **no source clone, no venv activation required**.

### Option 1: pipx (fastest, works everywhere)

```bash
pipx install git+https://github.com/repo-phuocdt/pdf-compressor-cli.git
```

`pipx` creates an isolated venv for the tool and puts `pdf-compressor` on your `$PATH`. This is the **recommended quick path** — it works on macOS, Linux, and Windows with no extra setup.

If you don't have pipx yet:

```bash
brew install pipx && pipx ensurepath
```

For OCR support: `brew install tesseract`.

### Option 2: Homebrew tap

You need to `brew tap` this repo first (Homebrew doesn't auto-discover formulas from arbitrary repos):

```bash
brew tap repo-phuocdt/pdf-compressor-cli https://github.com/repo-phuocdt/pdf-compressor-cli.git
brew install pdf-compressor
```

> **Why `brew install pdf-compressor` alone doesn't work**: Homebrew only searches `homebrew-core` by default. You must either `brew tap` first, or install directly from the formula URL:
>
> ```bash
> brew install --build-from-source \
>   https://raw.githubusercontent.com/repo-phuocdt/pdf-compressor-cli/master/Formula/pdf-compressor.rb
> ```

To always track the latest master (no pinned version):

```bash
brew install --HEAD pdf-compressor
```

The formula also pulls in `tesseract` (as a recommended dep) so `--ocr` works out of the box.

### Option 3: pip (global install)

```bash
pip install git+https://github.com/repo-phuocdt/pdf-compressor-cli.git
```

### Option 4: Clone and run from source (for development)

```bash
git clone https://github.com/repo-phuocdt/pdf-compressor-cli.git
cd pdf-compressor-cli
chmod +x setup.sh && ./setup.sh
source venv/bin/activate
pdf-compressor --help
```

`setup.sh` checks for Homebrew, installs `tesseract`, creates a venv, and runs `pip install -e .`.

---

## Quick start

### Interactive shell (claudekit-style REPL) — default

Run with no arguments and the tool opens an **interactive shell** inspired by Claude Code: type slash commands, state persists between commands, and you can compress many files without exiting:

```bash
pdf-compressor
# or
pdf-compressor -I
# or pre-load a file:
pdf-compressor -i big.pdf -I
```

Example session:

```
pdf-compressor› /help                      # list all commands
pdf-compressor› /preset low                # change the preset
pdf-compressor› /target 25                 # target output size = 25 MB
pdf-compressor› /pages 1-50                # only the first 50 pages
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
pdf-compressor --wizard
```

The tool asks for input/output/quality/target/pages/split/OCR/verbose in order, shows a confirmation table, then runs and exits.

---

### Flag mode (for power users / scripts)

#### 1. Basic compression with the default `medium` preset

```bash
pdf-compressor big.pdf
# or
pdf-compressor -i big.pdf
```

Default output: `big_compressed.pdf` next to the input.

#### 2. Aggressive compression with the low preset

```bash
pdf-compressor big.pdf -q low -o tiny.pdf
```

#### 3. Compress to a specific target size (e.g. ~25 MB)

```bash
pdf-compressor big.pdf -t 25
```

The tool binary-searches JPEG quality in the range [10, 85] until the output is within ±10% of the target.

#### 4. Process only a page range

```bash
pdf-compressor big.pdf --pages "1-50"
pdf-compressor big.pdf --pages "1,3,5-10"
```

#### 5. Split output into parts ≤ 30 MB each

```bash
pdf-compressor big.pdf --split 30
```

Produces `big_compressed_part1.pdf`, `big_compressed_part2.pdf`, …

#### 6. OCR for scanned PDFs

```bash
pdf-compressor scanned.pdf --ocr
```

Adds an invisible text layer to pages that currently have no text, so AI tools can extract the content.

#### 7. Verbose output

```bash
pdf-compressor big.pdf -v
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
→ Try `-q low` or combine it with `-t 20` to force a target size. For PDFs packed with vector art or heavy embedded fonts, splitting with `--split` can help.

---

## Project layout

```
pdf-compressor/
├── compress_pdf.py         # Main CLI (single, self-contained file)
├── pyproject.toml          # Package metadata + `pdf-compressor` entry point
├── requirements.txt        # Python dependencies (used by setup.sh)
├── setup.sh                # Dev setup script for macOS
├── Formula/
│   └── pdf-compressor.rb   # Homebrew formula
├── scripts/
│   └── gen_formula.py      # Regenerate formula resources from PyPI
└── README.md               # This file
```

---

## Publishing to Homebrew (for maintainers)

To let others run `brew install pdf-compressor`, you need a dedicated **tap repo** on GitHub:

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

### 4. Create the tap repo

The repo must be named `homebrew-<tap-name>` — here, `homebrew-pdf-compressor-cli`:

```bash
# On GitHub: create the repo `homebrew-pdf-compressor-cli`
git clone https://github.com/repo-phuocdt/homebrew-pdf-compressor-cli.git
cp Formula/pdf-compressor.rb homebrew-pdf-compressor-cli/Formula/
cd homebrew-pdf-compressor-cli
git add . && git commit -m "Initial formula" && git push
```

### 5. End-user install

```bash
brew tap repo-phuocdt/pdf-compressor-cli
brew install pdf-compressor
```

> **Tip**: test locally before pushing with `brew install --build-from-source ./Formula/pdf-compressor.rb`.
