
#!/usr/bin/env python3
import sys
import subprocess
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]   # /home/.../ocr_project
ROOT = BASE / "data_final"
LOG  = BASE / "logs" / "ocr.log"



# Workers seguros para laptop (P=2)
WORKERS = 2

# Pausa para no freír laptop (cada N docs)
PAUSE_EVERY = 10
PAUSE_SECONDS = 1


def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


def pdfs_iter(root: Path):
    # recorre recursivamente
    for pdf in root.rglob("input/*.pdf"):
        yield pdf


def run():
    log("=== OCR BATCH START ===")

    count = 0

    for pdf in pdfs_iter(ROOT):
        out_pdf = pdf  # overwrite mode
        txt_file = pdf.parent / "ocr.txt"

        # OCRmyPDF overwrite
        cmd = [
            "ocrmypdf",
            "--force-ocr",
			"--rotate-pages",
			"--deskew",
			"--clean",
            f"-j{WORKERS}",
            str(pdf),
            str(out_pdf),
        ]
        log(f"OCR: {pdf}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            log(f"ERR OCR: {pdf} -> {r.stderr.strip()}")
            continue

        # Extraer TXT
        cmd_txt = ["pdftotext", str(out_pdf), str(txt_file)]
        r = subprocess.run(cmd_txt, capture_output=True, text=True)
        if r.returncode != 0:
            log(f"ERR TXT: {pdf} -> {r.stderr.strip()}")
            continue

        count += 1

        if count % PAUSE_EVERY == 0:
            log(f"pause {PAUSE_SECONDS}s after {count} docs")
            time.sleep(PAUSE_SECONDS)

    log(f"=== OCR BATCH DONE ({count} docs) ===")


if __name__ == "__main__":
    run()

