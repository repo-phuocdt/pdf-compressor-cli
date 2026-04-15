#!/usr/bin/env bash
# setup.sh - bootstrap the pdf-compressor environment on macOS.
#
# - Checks Homebrew and tesseract (installs tesseract via brew if missing).
# - Checks Python 3.
# - Creates a local venv and installs Python dependencies.
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ensure this script itself is executable
chmod +x "$0" 2>/dev/null || true

echo "==> pdf-compressor setup (macOS)"

# --- Homebrew ---
if ! command -v brew >/dev/null 2>&1; then
    echo "ERROR: Homebrew is not installed."
    echo "Install it first from: https://brew.sh"
    echo "Then re-run ./setup.sh"
    exit 1
fi
echo "  brew found: $(brew --version | head -n 1)"

# --- Tesseract (optional, for --ocr) ---
if ! command -v tesseract >/dev/null 2>&1; then
    echo "  tesseract not found; installing via Homebrew..."
    brew install tesseract
else
    echo "  tesseract found: $(tesseract --version 2>&1 | head -n 1)"
fi

# --- Python 3 ---
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 is not installed. Install it via 'brew install python' first."
    exit 1
fi
echo "  python: $(python3 --version)"

# --- Virtualenv ---
if [ ! -d "venv" ]; then
    echo "==> Creating virtualenv at ./venv"
    python3 -m venv venv
else
    echo "  venv already exists, reusing"
fi

# shellcheck disable=SC1091
source venv/bin/activate

echo "==> Upgrading pip"
pip install --upgrade pip >/dev/null

echo "==> Installing pdf-compressor (editable)"
pip install -e .

echo ""
echo "Setup complete."
echo ""
echo "To use the tool:"
echo "    source venv/bin/activate"
echo "    pdf-compressor --help"
echo "    pdf-compressor /path/to/big.pdf"
echo ""
