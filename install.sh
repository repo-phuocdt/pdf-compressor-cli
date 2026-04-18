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
# If true, the brew path installs from master instead of the pinned tarball.
# Defaults to true because the pinned tarball can lag several commits behind
# and users hitting the brew path usually want "latest."
BREW_HEAD="${BREW_HEAD:-true}"

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

    # `brew tap` is case-insensitive in its listings. Compare in lowercase to
    # avoid the "already tapped but we can't see it" failure mode.
    local existing_taps
    existing_taps="$(brew tap 2>/dev/null | tr '[:upper:]' '[:lower:]' || true)"
    if echo "$existing_taps" | grep -Fxq "$(echo "$TAP" | tr '[:upper:]' '[:lower:]')"; then
        info "tap $TAP already present, skipping"
    else
        info "tapping $TAP from $REPO_URL"
        # Always pass the explicit URL. Without it, brew guesses
        # homebrew-<short> and fails for repos without that prefix — the
        # classic "Error: Invalid tap name" / "No available formula" story.
        if ! brew tap "$TAP" "$REPO_URL"; then
            die "Failed to tap $TAP. Check network access to $REPO_URL."
        fi
    fi

    # Fully-qualified formula reference — bypasses any core-formula lookup
    # ambiguity that produces the "No available formula or cask" error.
    local formula_ref="${TAP}/pdf-compressor-cli"
    local head_flag=()
    if [ "$BREW_HEAD" = "true" ] || [ "$BREW_HEAD" = "1" ]; then
        head_flag=("--HEAD")
        info "installing from master HEAD (set BREW_HEAD=false to pin to release)"
    fi

    if brew list pdf-compressor-cli >/dev/null 2>&1; then
        info "pdf-compressor-cli already installed — upgrading"
        brew upgrade "$formula_ref" || brew upgrade pdf-compressor-cli || true
    else
        info "installing $formula_ref (builds PyMuPDF from source; can take a while)"
        if ! brew install "${head_flag[@]}" "$formula_ref"; then
            warn "brew install failed. Common causes:"
            warn "  - PyMuPDF compile errors (missing Xcode CLI tools: 'xcode-select --install')"
            warn "  - stale tap: try 'brew untap $TAP && rerun this installer'"
            warn "  - formula not found: run 'brew update' then try again"
            warn "Falling back to pipx, which uses prebuilt wheels and is much faster."
            install_via_pipx
        fi
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
