#!/usr/bin/env bash
# install.sh — one-shot installer for pdf-compressor on macOS.
#
# Can be run as:
#   curl -fsSL https://raw.githubusercontent.com/repo-phuocdt/pdf-compressor-cli/master/install.sh | bash
#
# What it does:
#   1. Checks for Homebrew (prints link if missing).
#   2. Taps this repo as a Homebrew tap.
#   3. Installs the pdf-compressor formula (pulls in tesseract + python@3.12).
#   4. Prints a quick-start usage example.

set -euo pipefail

REPO_OWNER="repo-phuocdt"
REPO_NAME="pdf-compressor-cli"
TAP="${REPO_OWNER}/${REPO_NAME}"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"

bold()  { printf "\033[1m%s\033[0m\n" "$*"; }
info()  { printf "\033[36m==>\033[0m %s\n" "$*"; }
warn()  { printf "\033[33m!!\033[0m %s\n" "$*" >&2; }
die()   { printf "\033[31mxx\033[0m %s\n" "$*" >&2; exit 1; }

bold "pdf-compressor installer"
echo

if ! command -v brew >/dev/null 2>&1; then
    die "Homebrew is not installed. Install it first: https://brew.sh"
fi
info "brew found: $(brew --version | head -n 1)"

# Tap (idempotent — brew skips if already tapped)
if brew tap | grep -Fxq "$TAP"; then
    info "tap $TAP already present, skipping"
else
    info "tapping $TAP from $REPO_URL"
    brew tap "$TAP" "$REPO_URL"
fi

# Install (or upgrade if already installed)
if brew list pdf-compressor-cli >/dev/null 2>&1; then
    info "pdf-compressor-cli already installed — upgrading"
    brew upgrade pdf-compressor-cli || true
else
    info "installing pdf-compressor-cli"
    brew install pdf-compressor-cli
fi

echo
bold "Done."
echo
echo "Try it:"
echo "    pdf-compressor --version"
echo "    pdf-compressor /path/to/big.pdf"
echo "    pdf-compressor                     # interactive shell"
echo
