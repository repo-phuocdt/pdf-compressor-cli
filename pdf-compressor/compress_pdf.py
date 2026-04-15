#!/usr/bin/env python3
"""
compress_pdf.py - CLI tool to compress large PDF files for AI consumption.

Processes PDFs page-by-page (memory efficient) to downscale embedded images,
re-encode them as JPEG at a chosen quality, strip metadata, and rewrite the
PDF with cleanup/garbage collection. Supports target-size binary search,
page range selection, splitting into chunks, and optional OCR on scanned
pages.
"""

import io
import os
import re
import shutil
import signal
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Tuple

import click
import fitz  # pymupdf
from PIL import Image
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

# Optional OCR dependency
try:
    import pytesseract  # type: ignore

    HAS_TESSERACT = True
except Exception:
    HAS_TESSERACT = False


# Quality presets: (DPI, JPEG quality)
QUALITY_PRESETS = {
    "low": (72, 30),
    "medium": (150, 50),
    "high": (200, 70),
}

# Track temp files for signal cleanup
_TEMP_FILES: List[str] = []
console = Console()


# ---------- Helpers ----------


def human_size(num_bytes: int) -> str:
    """Convert bytes to human-readable string."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def cleanup_temp_files(paths: Optional[List[str]] = None) -> None:
    """Remove any tracked temp files. Safe to call multiple times."""
    targets = paths if paths is not None else _TEMP_FILES
    for p in list(targets):
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except OSError:
            pass
        if paths is None and p in _TEMP_FILES:
            _TEMP_FILES.remove(p)


def _signal_handler(signum, frame):
    """Cleanup temp files on SIGINT/SIGTERM then exit 130."""
    console.print("\n[yellow]Interrupted. Cleaning up temporary files...[/yellow]")
    cleanup_temp_files()
    sys.exit(130)


signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)


def parse_page_range(spec: str, total_pages: int) -> List[int]:
    """Parse a page range string like '1-50' or '1,3,5-10' into 0-indexed list.

    Pages in the spec are 1-indexed for the user. Returns sorted unique list.
    Raises click.BadParameter on invalid input or out-of-range pages.
    """
    if not spec or not spec.strip():
        raise click.BadParameter("Page range cannot be empty")

    result = set()
    parts = [p.strip() for p in spec.split(",") if p.strip()]
    if not parts:
        raise click.BadParameter(f"Invalid page range: {spec!r}")

    for part in parts:
        if "-" in part:
            m = re.match(r"^(\d+)-(\d+)$", part)
            if not m:
                raise click.BadParameter(f"Invalid range segment: {part!r}")
            start = int(m.group(1))
            end = int(m.group(2))
            if start < 1 or end < 1 or start > end:
                raise click.BadParameter(f"Invalid range: {part!r}")
            for n in range(start, end + 1):
                if n > total_pages:
                    raise click.BadParameter(
                        f"Page {n} out of range (document has {total_pages} pages)"
                    )
                result.add(n - 1)
        else:
            if not part.isdigit():
                raise click.BadParameter(f"Invalid page number: {part!r}")
            n = int(part)
            if n < 1 or n > total_pages:
                raise click.BadParameter(
                    f"Page {n} out of range (document has {total_pages} pages)"
                )
            result.add(n - 1)

    return sorted(result)


# ---------- Core compression ----------


def _recompress_image_bytes(
    img_bytes: bytes, target_dpi: int, jpeg_quality: int, src_dpi_hint: int = 300
) -> Optional[bytes]:
    """Downscale + re-encode one image as JPEG. Returns new bytes or None on failure."""
    try:
        with Image.open(io.BytesIO(img_bytes)) as im:
            # Convert anything with alpha or palette to RGB for JPEG
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGB")
            elif im.mode not in ("RGB", "L"):
                im = im.convert("RGB")

            # Scale down if source DPI seems higher than target DPI
            if src_dpi_hint > target_dpi and src_dpi_hint > 0:
                scale = target_dpi / float(src_dpi_hint)
                if scale < 1.0:
                    new_w = max(1, int(im.width * scale))
                    new_h = max(1, int(im.height * scale))
                    im = im.resize((new_w, new_h), Image.LANCZOS)

            out = io.BytesIO()
            im.save(out, format="JPEG", quality=jpeg_quality, optimize=True)
            return out.getvalue()
    except Exception:
        return None


def compress_page(
    doc: "fitz.Document",
    page_index: int,
    dpi: int,
    jpeg_quality: int,
    verbose: bool = False,
) -> Tuple[int, int]:
    """Compress all images on a single page in-place.

    Returns a tuple (images_seen, images_replaced).
    """
    page = doc[page_index]
    images = page.get_images(full=True)
    seen = 0
    replaced = 0

    for info in images:
        xref = info[0]
        seen += 1
        try:
            extracted = doc.extract_image(xref)
        except Exception:
            continue
        if not extracted or "image" not in extracted:
            continue

        orig_bytes = extracted["image"]
        # Heuristic: guess source DPI by comparing pixel dims to page size at 72dpi
        # We just pass a generous hint so rescale fires when image is obviously high-res.
        src_dpi_hint = 300
        try:
            width = extracted.get("width", 0)
            if width and page.rect.width > 0:
                page_width_in = page.rect.width / 72.0
                if page_width_in > 0:
                    src_dpi_hint = int(width / page_width_in)
        except Exception:
            pass

        new_bytes = _recompress_image_bytes(
            orig_bytes, target_dpi=dpi, jpeg_quality=jpeg_quality, src_dpi_hint=src_dpi_hint
        )
        if not new_bytes or len(new_bytes) >= len(orig_bytes):
            # No gain, keep original
            continue

        try:
            # pymupdf 1.23+: replace_image on the Page
            page.replace_image(xref, stream=new_bytes)
            replaced += 1
        except Exception as exc:
            if verbose:
                console.print(
                    f"[dim]  page {page_index + 1}: failed to replace image xref={xref}: {exc}[/dim]"
                )
            continue

    return seen, replaced


def _run_ocr_on_scanned_pages(
    doc: "fitz.Document", page_indices: List[int], verbose: bool = False
) -> int:
    """Add a text layer to scanned (text-free) pages using tesseract.

    Returns the number of pages where OCR text was inserted.
    """
    if not HAS_TESSERACT:
        console.print(
            "[yellow]Warning: pytesseract not available, skipping OCR.[/yellow]"
        )
        return 0

    ocr_count = 0
    for idx in page_indices:
        page = doc[idx]
        existing_text = page.get_text().strip()
        if existing_text:
            continue  # Page already has text
        try:
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            data = pytesseract.image_to_data(
                img, output_type=pytesseract.Output.DICT
            )
            # Scale factor from pixmap pixels back to PDF points
            scale_x = page.rect.width / pix.width if pix.width else 1.0
            scale_y = page.rect.height / pix.height if pix.height else 1.0
            n = len(data.get("text", []))
            for i in range(n):
                word = (data["text"][i] or "").strip()
                if not word:
                    continue
                x = data["left"][i] * scale_x
                y = data["top"][i] * scale_y
                w = data["width"][i] * scale_x
                h = data["height"][i] * scale_y
                # Insert invisible text via textbox; fontsize ~ h in points
                fontsize = max(1.0, h * 0.9)
                try:
                    page.insert_text(
                        (x, y + fontsize),
                        word,
                        fontsize=fontsize,
                        render_mode=3,  # 3 = invisible (neither fill nor stroke)
                        overlay=True,
                    )
                except Exception:
                    continue
            ocr_count += 1
            if verbose:
                console.print(f"[dim]  OCR applied to page {idx + 1}[/dim]")
        except Exception as exc:
            if verbose:
                console.print(
                    f"[dim]  OCR failed on page {idx + 1}: {exc}[/dim]"
                )
            continue
    return ocr_count


def compress_pdf(
    input_path: str,
    output_path: str,
    dpi: int,
    jpeg_quality: int,
    pages: Optional[List[int]] = None,
    do_ocr: bool = False,
    verbose: bool = False,
) -> dict:
    """Compress a PDF and write to output_path. Returns stats dict."""
    start = time.time()
    original_size = os.path.getsize(input_path)

    doc = fitz.open(input_path)
    try:
        if doc.is_encrypted:
            doc.close()
            raise click.ClickException(
                "PDF is encrypted. Please decrypt the file before compressing."
            )

        total_pages = doc.page_count
        if pages is None:
            target_pages = list(range(total_pages))
        else:
            target_pages = pages

        # If a subset was requested, produce a new doc containing only those pages.
        if pages is not None and len(pages) != total_pages:
            sub = fitz.open()
            for idx in target_pages:
                sub.insert_pdf(doc, from_page=idx, to_page=idx)
            doc.close()
            doc = sub
            target_pages = list(range(doc.page_count))

        total_imgs = 0
        replaced_imgs = 0
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            task = progress.add_task(
                "Compressing pages", total=len(target_pages)
            )
            for i, page_idx in enumerate(target_pages):
                seen, replaced = compress_page(
                    doc, page_idx, dpi=dpi, jpeg_quality=jpeg_quality, verbose=verbose
                )
                total_imgs += seen
                replaced_imgs += replaced
                progress.update(task, advance=1)

        if do_ocr:
            console.print("[cyan]Running OCR on scanned pages...[/cyan]")
            ocr_pages = _run_ocr_on_scanned_pages(doc, target_pages, verbose=verbose)
            if verbose:
                console.print(f"[dim]OCR added text layer to {ocr_pages} page(s)[/dim]")

        # Strip metadata
        try:
            doc.set_metadata({})
        except Exception:
            pass

        # Save with garbage collection and deflation
        doc.save(
            output_path,
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            clean=True,
            pretty=False,
        )
    finally:
        try:
            doc.close()
        except Exception:
            pass

    compressed_size = os.path.getsize(output_path)
    elapsed = time.time() - start

    return {
        "original_size": original_size,
        "compressed_size": compressed_size,
        "pages": len(target_pages),
        "total_images": total_imgs,
        "replaced_images": replaced_imgs,
        "elapsed": elapsed,
        "dpi": dpi,
        "jpeg_quality": jpeg_quality,
    }


# ---------- Target-size binary search ----------


def compress_to_target(
    input_path: str,
    output_path: str,
    target_mb: int,
    dpi: int,
    pages: Optional[List[int]],
    do_ocr: bool,
    verbose: bool,
) -> dict:
    """Binary-search JPEG quality to hit target_mb ±10%.

    Keeps the best (<= target or smallest >target) candidate.
    """
    target_bytes = target_mb * 1024 * 1024
    tolerance = 0.10
    low, high = 10, 85
    best_path: Optional[str] = None
    best_stats: Optional[dict] = None
    max_iters = 6

    tmp_dir = tempfile.mkdtemp(prefix="pdfcomp_")
    _TEMP_FILES.append(tmp_dir)  # tracking the dir for cleanup too

    try:
        for iteration in range(max_iters):
            q = (low + high) // 2
            tmp_out = os.path.join(tmp_dir, f"try_q{q}.pdf")
            _TEMP_FILES.append(tmp_out)

            if verbose:
                console.print(
                    f"[cyan]Iteration {iteration + 1}/{max_iters}: trying JPEG quality={q}[/cyan]"
                )
            stats = compress_pdf(
                input_path=input_path,
                output_path=tmp_out,
                dpi=dpi,
                jpeg_quality=q,
                pages=pages,
                do_ocr=do_ocr,
                verbose=verbose,
            )
            size = stats["compressed_size"]
            if verbose:
                console.print(
                    f"[dim]  got {human_size(size)} (target {human_size(target_bytes)})[/dim]"
                )

            # Track best candidate: prefer <= target; otherwise smallest overall
            def score(s):
                return (0 if s <= target_bytes else 1, abs(s - target_bytes))

            if best_stats is None or score(size) < score(best_stats["compressed_size"]):
                if best_path and os.path.exists(best_path) and best_path != tmp_out:
                    try:
                        os.remove(best_path)
                    except OSError:
                        pass
                best_path = tmp_out
                best_stats = stats

            # Within tolerance -> stop
            if abs(size - target_bytes) <= target_bytes * tolerance:
                break

            if size > target_bytes:
                # Too big, lower quality
                high = q - 1
            else:
                # Under target, try higher quality for better fidelity
                low = q + 1

            if low > high:
                break

        if best_path is None or best_stats is None:
            raise click.ClickException("Target-size search failed to produce output")

        # Move best candidate to final output
        shutil.move(best_path, output_path)
        best_stats["compressed_size"] = os.path.getsize(output_path)
        return best_stats
    finally:
        # Cleanup temp dir
        if os.path.isdir(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)
        if tmp_dir in _TEMP_FILES:
            _TEMP_FILES.remove(tmp_dir)


# ---------- Split output ----------


def split_pdf(input_path: str, max_mb: int, verbose: bool = False) -> List[str]:
    """Split a PDF into chunks no larger than max_mb. Returns list of output paths.

    Strategy: grow chunks one page at a time; if saving a chunk exceeds max_mb, back off
    one page and start a new chunk (unless a single page already exceeds limit).
    """
    max_bytes = max_mb * 1024 * 1024
    src = fitz.open(input_path)
    try:
        total = src.page_count
        base = Path(input_path)
        stem = base.stem
        parent = base.parent

        outputs: List[str] = []
        part_num = 1
        page_idx = 0
        tmp_dir = tempfile.mkdtemp(prefix="pdfsplit_")

        try:
            while page_idx < total:
                chunk = fitz.open()
                start_page = page_idx
                last_good_path: Optional[str] = None
                last_good_end = start_page - 1

                while page_idx < total:
                    chunk.insert_pdf(src, from_page=page_idx, to_page=page_idx)
                    tmp_path = os.path.join(tmp_dir, f"probe_{part_num}_{page_idx}.pdf")
                    chunk.save(tmp_path, garbage=4, deflate=True, clean=True)
                    size = os.path.getsize(tmp_path)

                    if size <= max_bytes:
                        if last_good_path and os.path.exists(last_good_path):
                            try:
                                os.remove(last_good_path)
                            except OSError:
                                pass
                        last_good_path = tmp_path
                        last_good_end = page_idx
                        page_idx += 1
                    else:
                        # This page pushed us over the limit
                        if last_good_path is None:
                            # Single page exceeds max_bytes; keep it anyway
                            last_good_path = tmp_path
                            last_good_end = page_idx
                            page_idx += 1
                        else:
                            try:
                                os.remove(tmp_path)
                            except OSError:
                                pass
                        break

                if last_good_path is None:
                    break

                out_name = f"{stem}_part{part_num}.pdf"
                out_path = str(parent / out_name)
                shutil.move(last_good_path, out_path)
                outputs.append(out_path)
                if verbose:
                    console.print(
                        f"[dim]  part {part_num}: pages {start_page + 1}-{last_good_end + 1}, "
                        f"{human_size(os.path.getsize(out_path))}[/dim]"
                    )
                part_num += 1
                chunk.close()

            return outputs
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
    finally:
        src.close()


# ---------- CLI ----------


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Compress large PDF files down to an AI-friendly size.",
)
@click.option(
    "-i",
    "--input",
    "input_path",
    required=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Input PDF file (required).",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help="Output file (default: {name}_compressed.pdf).",
)
@click.option(
    "-q",
    "--quality",
    type=click.Choice(["low", "medium", "high"], case_sensitive=False),
    default="medium",
    show_default=True,
    help="Preset: low | medium | high.",
)
@click.option(
    "-t",
    "--target-size",
    type=int,
    default=None,
    help="Target size in MB. Binary-searches JPEG quality to match target within ~10 percent.",
)
@click.option(
    "--dpi",
    type=int,
    default=None,
    help="Override preset DPI (low=72, medium=150, high=200).",
)
@click.option(
    "--pages",
    default=None,
    help='Page range like "1-50" or "1,3,5-10".',
)
@click.option(
    "--split",
    "split_mb",
    type=int,
    default=None,
    help="Split output into chunks of at most N MB each.",
)
@click.option(
    "--ocr",
    is_flag=True,
    default=False,
    help="Run OCR on scanned pages to add an invisible text layer.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Verbose logging.",
)
def main(
    input_path: str,
    output_path: Optional[str],
    quality: str,
    target_size: Optional[int],
    dpi: Optional[int],
    pages: Optional[str],
    split_mb: Optional[int],
    ocr: bool,
    verbose: bool,
) -> None:
    """Entry point."""
    in_path = Path(input_path)
    if output_path is None:
        output_path = str(in_path.with_name(f"{in_path.stem}_compressed.pdf"))

    preset_dpi, preset_q = QUALITY_PRESETS[quality.lower()]
    effective_dpi = dpi if dpi is not None else preset_dpi
    effective_q = preset_q

    # Parse page range if provided (need total pages first)
    selected_pages: Optional[List[int]] = None
    if pages:
        probe = fitz.open(input_path)
        try:
            if probe.is_encrypted:
                raise click.ClickException(
                    "PDF is encrypted. Please decrypt the file before compressing."
                )
            selected_pages = parse_page_range(pages, probe.page_count)
            if not selected_pages:
                raise click.ClickException("Page range produced no pages")
        finally:
            probe.close()

    if ocr and not HAS_TESSERACT:
        console.print(
            "[yellow]Note: --ocr requested but pytesseract/tesseract not available. "
            "OCR will be skipped.[/yellow]"
        )

    console.print(f"[bold cyan]Input:[/bold cyan] {input_path}")
    console.print(f"[bold cyan]Output:[/bold cyan] {output_path}")
    console.print(
        f"[bold cyan]Preset:[/bold cyan] {quality}  "
        f"[bold cyan]DPI:[/bold cyan] {effective_dpi}  "
        f"[bold cyan]JPEG q:[/bold cyan] {effective_q}"
    )
    if target_size:
        console.print(f"[bold cyan]Target size:[/bold cyan] {target_size} MB")

    try:
        if target_size:
            stats = compress_to_target(
                input_path=input_path,
                output_path=output_path,
                target_mb=target_size,
                dpi=effective_dpi,
                pages=selected_pages,
                do_ocr=ocr,
                verbose=verbose,
            )
        else:
            stats = compress_pdf(
                input_path=input_path,
                output_path=output_path,
                dpi=effective_dpi,
                jpeg_quality=effective_q,
                pages=selected_pages,
                do_ocr=ocr,
                verbose=verbose,
            )
    except click.ClickException:
        raise
    except Exception as exc:
        cleanup_temp_files()
        raise click.ClickException(f"Compression failed: {exc}")

    # Optional split
    split_outputs: List[str] = []
    if split_mb:
        console.print(f"[cyan]Splitting output into {split_mb} MB chunks...[/cyan]")
        split_outputs = split_pdf(output_path, max_mb=split_mb, verbose=verbose)
        # Remove the monolithic output since we produced parts
        try:
            os.remove(output_path)
        except OSError:
            pass

    # Summary
    original = stats["original_size"]
    compressed = stats["compressed_size"]
    reduction = (1 - compressed / original) * 100 if original else 0.0

    table = Table(title="Compression Summary", show_header=True, header_style="bold")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Original size", human_size(original))
    table.add_row("Compressed size", human_size(compressed))
    table.add_row("Reduction", f"{reduction:.1f}%")
    table.add_row("Pages processed", str(stats["pages"]))
    table.add_row(
        "Images replaced",
        f"{stats['replaced_images']}/{stats['total_images']}",
    )
    table.add_row("DPI", str(stats["dpi"]))
    table.add_row("JPEG quality", str(stats["jpeg_quality"]))
    table.add_row("Elapsed", f"{stats['elapsed']:.1f}s")
    console.print(table)

    if split_outputs:
        console.print("[bold green]Split output files:[/bold green]")
        for p in split_outputs:
            console.print(f"  - {p}  ({human_size(os.path.getsize(p))})")
    else:
        console.print(f"[bold green]Done:[/bold green] {output_path}")


if __name__ == "__main__":
    main()
