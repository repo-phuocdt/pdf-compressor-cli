#!/usr/bin/env python3
"""
gen_formula.py - Regenerate the Homebrew formula at Formula/pdf-compressor-cli.rb.

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
import re
import sys
import urllib.request
from pathlib import Path
from typing import Optional

# Direct runtime deps from pyproject.toml. Transitive deps are resolved
# automatically from importlib.metadata so we never miss one (see issue #12).
DIRECT_DEPS = ["pymupdf", "Pillow", "click", "rich", "pytesseract"]


def _normalize(name: str) -> str:
    """PyPI-normalized package name (lowercase, hyphens)."""
    return re.sub(r"[-_.]+", "-", name).lower()


def _get_version(pkg: str) -> Optional[str]:
    """Return installed version, or None if not installed."""
    try:
        from importlib.metadata import version, PackageNotFoundError
    except ImportError:  # pragma: no cover
        from importlib_metadata import version, PackageNotFoundError  # type: ignore
    try:
        return version(pkg)
    except PackageNotFoundError:
        return None


def installed_version(pkg: str) -> str:
    """Return the version installed in the current env, or exit if missing."""
    v = _get_version(pkg)
    if v is None:
        print(f"  [warn] {pkg} not installed; please `pip install {pkg}` first.")
        sys.exit(1)
    return v


def _marker_applies_on_macos(marker_str: str) -> bool:
    """Evaluate a PEP 508 marker as if we were on macOS (Darwin).

    We always generate the formula for macOS consumers - so Windows- or
    Linux-only deps should be skipped. Extras-only markers are always
    skipped. If the marker can't be parsed, default to True (conservative).
    """
    if not marker_str.strip():
        return True
    # Fast path: extras-only markers are never satisfied in this context
    if "extra ==" in marker_str and not any(
        k in marker_str for k in ("platform_", "sys_platform", "os_name", "python_")
    ):
        return False
    try:
        from packaging.markers import Marker
    except ImportError:
        return True  # conservative
    env = {
        "os_name": "posix",
        "sys_platform": "darwin",
        "platform_system": "Darwin",
        "platform_machine": "arm64",
        "platform_release": "24.0.0",
        "python_version": "3.12",
        "python_full_version": "3.12.0",
        "implementation_name": "cpython",
        "platform_python_implementation": "CPython",
        "extra": "",
    }
    try:
        return Marker(marker_str).evaluate(env)
    except Exception:
        return True


def resolve_all_runtime_deps(direct: list[str]) -> list[str]:
    """Walk `importlib.metadata.requires()` transitively from direct deps and
    return a de-duplicated list of all runtime packages that need resource
    blocks in the Homebrew formula, as evaluated for macOS.

    Skips extras-only deps and platform-conditional deps that don't apply
    to macOS.
    """
    try:
        from importlib.metadata import requires as md_requires
    except ImportError:  # pragma: no cover
        from importlib_metadata import requires as md_requires  # type: ignore

    seen: dict[str, str] = {}  # normalized name -> original casing

    def visit(pkg: str) -> None:
        norm = _normalize(pkg)
        if norm in seen:
            return
        if _get_version(pkg) is None:
            return
        seen[norm] = pkg
        try:
            reqs = md_requires(pkg) or []
        except Exception:
            reqs = []
        for req in reqs:
            marker = req.split(";", 1)[1] if ";" in req else ""
            if not _marker_applies_on_macos(marker):
                continue
            name = re.split(r"[\s;<>=!~\[]", req, 1)[0].strip()
            if not name:
                continue
            visit(name)

    for d in direct:
        visit(d)
    return list(seen.values())


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
        default=str(Path(__file__).resolve().parent.parent / "Formula" / "pdf-compressor-cli.rb"),
        help="Output path for the formula.",
    )
    args = ap.parse_args()

    print("==> Walking transitive deps from direct runtime deps")
    runtime_deps = resolve_all_runtime_deps(DIRECT_DEPS)
    print(f"  direct: {DIRECT_DEPS}")
    print(f"  all runtime (incl. transitive): {runtime_deps}")

    print("==> Resolving resources from PyPI")
    resources = []
    for pkg in runtime_deps:
        ver = installed_version(pkg)
        canonical, url, sha = pypi_sdist(pkg, ver)
        print(f"  {canonical}=={ver}")
        resources.append(fmt_resource(canonical, url, sha))

    formula = f"""class PdfCompressorCli < Formula
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
