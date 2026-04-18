#!/usr/bin/env bash
# install.sh — one-shot installer for pdf-compressor-cli.
#
# Can be run as:
#   curl -fsSL https://raw.githubusercontent.com/repo-phuocdt/pdf-compressor-cli/master/install.sh | bash
#
# Strategy: prefer `pipx` (fast, reliable, uses PyPI wheels). Fall back to
# `brew tap + brew install` only if explicitly requested via METHOD=brew.
# Reason: PyMuPDF sdists compile MuPDF from C, which often fails on macOS
# without matching SDK + toolchain. pipx uses prebuilt wheels and finishes
# in seconds.

set -euo pipefail

REPO_OWNER="repo-phuocdt"
REPO_NAME="pdf-compressor-cli"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
TAP="${REPO_OWNER}/${REPO_NAME}"
METHOD="${METHOD:-pipx}"    # pipx (default) | brew

bold()  { printf "\033[1m%s\033[0m\n" "$*"; }
info()  { printf "\033[36m==>\033[0m %s\n" "$*"; }
warn()  { printf "\033[33m!!\033[0m %s\n" "$*" >&2; }
die()   { printf "\033[31mxx\033[0m %s\n" "$*" >&2; exit 1; }

bold "pdf-compressor-cli installer  (method: ${METHOD})"
echo

install_via_pipx() {
    if ! command -v pipx >/dev/null 2>&1; then
        if command -v brew >/dev/null 2>&1; then
            info "pipx not found, installing via Homebrew"
            brew install pipx
            pipx ensurepath
        elif command -v python3 >/dev/null 2>&1; then
            info "pipx not found, installing via pip --user"
            python3 -m pip install --user pipx
            python3 -m pipx ensurepath
        else
            die "Need either Homebrew or python3 to bootstrap pipx."
        fi
    fi
    info "pipx found: $(pipx --version)"

    if command -v brew >/dev/null 2>&1 && ! command -v tesseract >/dev/null 2>&1; then
        info "installing tesseract via Homebrew (needed for --ocr)"
        brew install tesseract || warn "tesseract install failed; --ocr will be disabled"
    fi

    info "installing pdf-compressor-cli via pipx"
    if pipx list 2>/dev/null | grep -q "pdf-compressor"; then
        pipx upgrade pdf-compressor || pipx install --force "git+${REPO_URL}"
    else
        pipx install "git+${REPO_URL}"
    fi
}

install_via_brew() {
    if ! command -v brew >/dev/null 2>&1; then
        die "Homebrew is not installed. Install it first: https://brew.sh"
    fi
    info "brew found: $(brew --version | head -n 1)"

    if ! command -v tesseract >/dev/null 2>&1; then
        info "installing tesseract via Homebrew"
        brew install tesseract || warn "tesseract install failed; --ocr will be disabled"
    fi

    if brew tap | grep -Fxq "$TAP"; then
        info "tap $TAP already present, skipping"
    else
        info "tapping $TAP from $REPO_URL"
        brew tap "$TAP" "$REPO_URL"
    fi

    if brew list pdf-compressor-cli >/dev/null 2>&1; then
        info "pdf-compressor-cli already installed — upgrading"
        brew upgrade pdf-compressor-cli || true
    else
        info "installing pdf-compressor-cli (builds deps from source; can take a while)"
        brew install pdf-compressor-cli
    fi
}

case "$METHOD" in
    pipx) install_via_pipx ;;
    brew) install_via_brew ;;
    *)    die "Unknown METHOD: $METHOD (expected 'pipx' or 'brew')" ;;
esac

echo
bold "Done."
echo
echo "Try it:"
echo "    pdf-compressor-cli --version"
echo "    pdf-compressor-cli /path/to/big.pdf"
echo "    pdf-compressor-cli big.pdf -q low --rasterize   # max compression"
echo "    pdf-compressor-cli                              # interactive shell"
echo

if ! command -v pdf-compressor-cli >/dev/null 2>&1; then
    warn "pdf-compressor-cli is not on PATH yet. You may need to open a new shell,"
    warn "or run: pipx ensurepath  (then restart your terminal)."
fi
