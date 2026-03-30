#!/usr/bin/env python3
"""
FASE 3 — Rasterización OCR-aware
PDF → TIFF (8bit grayscale, 400 DPI, sin binarizar)
"""

import subprocess
from pathlib import Path
import tempfile

# =========================================================
# BASE
# =========================================================

BASE = Path(__file__).resolve().parents[2]
SUBCORPUS = BASE / "subcorpus_fase3"

# =========================================================
# CONFIG
# =========================================================

DPI = 400
UNSHARP = "1.0x1.0+0.8+0"

# =========================================================
# RASTER
# =========================================================

def rasterize_pdf(pdf_path: Path, raster_dir: Path):
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        # ---------------------------------------------
        # PDF → PGM (grayscale, OCR-aware)
        # ---------------------------------------------
        subprocess.run([
            "pdftoppm",
            "-r", str(DPI),
            "-gray",
            str(pdf_path),
            str(tmpdir / "page")
        ], check=True)

        images = sorted(tmpdir.glob("page-*.pgm"))
        if not images:
            print(f"[WARN] pdftoppm no produjo imágenes: {pdf_path}")
            return

        raster_dir.mkdir(exist_ok=True)

        # ---------------------------------------------
        # PGM → TIFF (8bit, LZW, sharpen)
        # ---------------------------------------------
        for i, img in enumerate(images, start=1):
            out = raster_dir / f"page_{i:03d}.tif"

            subprocess.run([
                "convert",
                str(img),
                "-depth", "8",
                "-unsharp", UNSHARP,
                "-compress", "LZW",
                str(out)
            ], check=True)

# =========================================================
# MAIN
# =========================================================

def main():
    for keyword_dir in SUBCORPUS.iterdir():
        if not keyword_dir.is_dir():
            continue

        for numero_dir in keyword_dir.iterdir():
            input_dir = numero_dir / "input"
            raster_dir = numero_dir / "raster"

            if raster_dir.exists() and any(raster_dir.glob("*.tif")):
                print(f"[SKIP] Raster ya existe: {numero_dir.name}")
                continue

            pdfs = list(input_dir.glob("*.pdf"))
            if not pdfs:
                print(f"[WARN] Sin PDF: {numero_dir}")
                continue

            print(f"[RASTER] {numero_dir.name}")
            rasterize_pdf(pdfs[0], raster_dir)

    print("\nFASE 3 — rasterización completada.")

if __name__ == "__main__":
    main()


