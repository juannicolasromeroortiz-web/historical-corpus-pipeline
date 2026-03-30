#!/usr/bin/env python3
import os
import shutil
from pathlib import Path

# === CONFIGURACIÓN ===
BASE_RASTER = Path("/home/juan_romero/projects/ocr_project/subcorpus_fase3")
BASE_REOCR  = Path("/home/juan_romero/projects/ocr_project/subcorpus_por_reOCR")

VALID_EXT = {".tif", ".tiff"}


def log(msg):
    print(f"[prepare_reOCR] {msg}")


def collect_tiffs(raster_dir: Path):
    return sorted(
        p for p in raster_dir.iterdir()
        if p.is_file() and p.suffix.lower() in VALID_EXT
    )


def prepare_batch():
    if not BASE_RASTER.exists():
        raise RuntimeError(f"No existe {BASE_RASTER}")

    BASE_REOCR.mkdir(parents=True, exist_ok=True)

    total_moved = 0
    total_skipped = 0

    for keyword_dir in sorted(BASE_RASTER.iterdir()):
        if not keyword_dir.is_dir():
            continue

        keyword = keyword_dir.name
        log(f"Keyword: {keyword}")

        for periodico_dir in sorted(keyword_dir.iterdir()):
            raster_dir = periodico_dir / "raster"

            if not raster_dir.exists():
                continue

            tiffs = collect_tiffs(raster_dir)

            if not tiffs:
                log(f"  [WARN] Raster vacío → {periodico_dir}")
                continue

            out_dir = BASE_REOCR / keyword / periodico_dir.name / "input"
            out_dir.mkdir(parents=True, exist_ok=True)

            # Si ya hay imágenes, no tocamos nada
            if any(out_dir.iterdir()):
                log(f"  [SKIP] input no vacío → {out_dir}")
                total_skipped += len(tiffs)
                continue

            log(f"  Moviendo {len(tiffs)} páginas → {out_dir}")

            for idx, tif in enumerate(tiffs, start=1):
                new_name = f"image_{idx:04d}.tif"
                shutil.move(str(tif), out_dir / new_name)
                total_moved += 1

    log(f"FINAL → movidas: {total_moved} | omitidas: {total_skipped}")


if __name__ == "__main__":
    prepare_batch()


