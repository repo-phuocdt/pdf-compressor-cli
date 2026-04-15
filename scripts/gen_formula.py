#!/usr/bin/env python3
"""
gen_formula.py - Regenerate the Homebrew formula at Formula/pdf-compressor.rb.

Pulls the project's declared Python dependencies from pyproject.toml, resolves
the exact installed versions in the current environment, fetches each sdist's
URL + sha256 from PyPI, and writes a `Language::Python::Virtualenv` formula.

Usage:
    # First install the package + deps so we resolve the exact versions:
    python3 -m pip install .
    python3 scripts/gen_formula.py \
        --source-url https://github.com/repo-phuocdt/pdf-compressor-cli/archive/refs/tags/v0.1.0.tar.gz \
        --source-sha256 <SHA>

If --source-sha256 is omitted, placeholder will be left in the formula.
"""
import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

# Packages to include as `resource` blocks. These are runtime deps of the tool.
RUNTIME_DEPS = ["pymupdf", "Pillow", "click", "rich", "pytesseract",
                "markdown-it-py", "mdurl", "Pygments"]


def installed_version(pkg: str) -> str:
    """Return the version installed in the current env via importlib.metadata."""
    try:
        from importlib.metadata import version, PackageNotFoundError
    except ImportError:  # pragma: no cover
        from importlib_metadata import version, PackageNotFoundError  # type: ignore
    try:
        return version(pkg)
    except PackageNotFoundError:
        print(f"  [warn] {pkg} not installed; please `pip install {pkg}` first.")
        sys.exit(1)


def pypi_sdist(pkg: str, ver: str) -> tuple[str, str, str]:
    """Return (canonical_name, url, sha256) for the sdist of `pkg==ver`."""
    url = f"https://pypi.org/pypi/{pkg}/{ver}/json"
    with urllib.request.urlopen(url, timeout=10) as r:
        data = json.load(r)
    canonical = data["info"]["name"]
    for item in data["urls"]:
        if item.get("packagetype") == "sdist":
            return canonical, item["url"], item["digests"]["sha256"]
    for item in data["urls"]:
        return canonical, item["url"], item["digests"]["sha256"]
    raise RuntimeError(f"No distribution found for {pkg}=={ver}")


def fmt_resource(name: str, url: str, sha256: str) -> str:
    return (
        f'  resource "{name}" do\n'
        f'    url "{url}"\n'
        f'    sha256 "{sha256}"\n'
        f"  end\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--source-url",
        default="https://github.com/repo-phuocdt/pdf-compressor-cli/archive/refs/tags/v0.1.0.tar.gz",
        help="Release tarball URL for the project itself.",
    )
    ap.add_argument(
        "--source-sha256",
        default="REPLACE_WITH_RELEASE_TARBALL_SHA256",
        help="SHA256 of the release tarball.",
    )
    ap.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parent.parent / "Formula" / "pdf-compressor.rb"),
        help="Output path for the formula.",
    )
    args = ap.parse_args()

    print("==> Resolving resources from PyPI")
    resources = []
    for pkg in RUNTIME_DEPS:
        ver = installed_version(pkg)
        canonical, url, sha = pypi_sdist(pkg, ver)
        print(f"  {canonical}=={ver}")
        resources.append(fmt_resource(canonical, url, sha))

    formula = f"""class PdfCompressor < Formula
  include Language::Python::Virtualenv

  desc "Compress large PDFs to an AI-friendly size (page-by-page, memory efficient)"
  homepage "https://github.com/repo-phuocdt/pdf-compressor-cli"
  url "{args.source_url}"
  sha256 "{args.source_sha256}"
  license "MIT"
  head "https://github.com/repo-phuocdt/pdf-compressor-cli.git", branch: "master"

  depends_on "python@3.12"
  depends_on "tesseract" => :recommended # needed only for --ocr

{''.join(resources)}
  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "pdf-compressor, version", shell_output("#{{bin}}/pdf-compressor --version")
  end
end
"""

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(formula)
    print(f"\n==> Wrote {out_path}")
    print("If you pinned --source-url to a commit tarball, no tag needed.")
    print("Otherwise remember to tag the release and update --source-sha256.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
