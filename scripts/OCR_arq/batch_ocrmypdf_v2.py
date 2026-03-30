#!/usr/bin/env python3
import subprocess, time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / "data_final"
LOG  = BASE / "logs" / "ocr.log"

WORKERS = 3          # Optimizado para ThinkPad T440
PAUSE_EVERY = 20     # batch awareness
PAUSE_SECONDS = 1

def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def pdfs_iter(root):
    for pdf in root.rglob("input/*.pdf"):
        yield pdf

def run():
    log("=== OCR BATCH START (MODO B2) ===")
    count = 0

    for pdf in pdfs_iter(ROOT):
        out_pdf = pdf
        txt_file = pdf.parent / "ocr.txt"

        cmd = [
            "ocrmypdf",
            "--force-ocr",
            "--rotate-pages",
            "--deskew",
            "--clean",
            "--optimize", "0",
            f"-j{WORKERS}",
            str(pdf),
            str(out_pdf),
        ]
        log(f"OCR: {pdf}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            log(f"ERR OCR: {pdf} -> {r.stderr.strip()}")
            continue

        r = subprocess.run(["pdftotext", str(out_pdf), str(txt_file)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            log(f"ERR TXT: {pdf} -> {r.stderr.strip()}")
            continue

        count += 1
        if count % PAUSE_EVERY == 0:
            log(f"cooldown {PAUSE_SECONDS}s after {count} docs")
            time.sleep(PAUSE_SECONDS)

    log(f"=== OCR DONE ({count} docs) ===")

if __name__ == "__main__":
    run()

