#!/usr/bin/env python3
import subprocess, datetime
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
ROOT = BASE / "data_final"
LOG  = BASE / "logs" / "ocr.log"

WORKERS = 2   # laptop-safe


def log(msg):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


def iter_periodicos():
    for per in sorted(ROOT.iterdir()):
        if per.is_dir():
            yield per


def iter_pdfs(periodico):
    return sorted(periodico.rglob("input/*.pdf"))


def count_pdfs():
    return len(list(ROOT.rglob("input/*.pdf")))


def count_txt():
    return len(list(ROOT.rglob("input/ocr.txt")))


def report(periodico_name, processed_in_tanda, start_time):
    total = count_pdfs()
    done = count_txt()
    pending = total - done
    pct = (done / total * 100) if total > 0 else 0

    elapsed = (datetime.datetime.now() - start_time).total_seconds()
    elapsed_h = elapsed / 3600 if elapsed > 0 else 0
    rate = done / elapsed_h if elapsed_h > 0 else 0

    eta = (pending / rate) if rate > 0 else -1
    eta_h = eta
    eta_d = eta_h / 24 if eta_h > 0 else -1

    msg = (
        f"=== OCR REPORT (tanda: {periodico_name}) ===\n"
        f"Procesados en tanda: {processed_in_tanda}\n"
        f"PDFs totales:  {total}\n"
        f"TXT generados: {done}\n"
        f"Faltantes:     {pending}\n"
        f"Completado:    {pct:.2f}%\n"
        f"Tiempo:        {elapsed_h:.2f} h\n"
        f"Velocidad:     {rate:.2f} PDF/h\n"
        f"ETA:           {eta_h:.2f} h (~{eta_d:.2f} días)\n"
        f"===============================\n"
    )

    log(msg)


def run():
    log("=== OCR BATCH START (B3-LITE PROGRESO) ===")
    start_time = datetime.datetime.now()

    for per in iter_periodicos():

        per_name = per.name
        pdfs = iter_pdfs(per)

        if not pdfs:
            continue

        total = len(pdfs)
        log(f"=== TANDA: {per_name} ({total} PDFs) ===")

        tanda_count = 0
        idx = 0

        for pdf in pdfs:

            idx += 1
            print(f"[{idx}/{total}] {pdf.name}")

            out_pdf = pdf
            txt_file = pdf.parent / "ocr.txt"

            # -----------------------------
            # CONTROL DE OCR EXISTENTE
            # -----------------------------

            if txt_file.exists():

                size = txt_file.stat().st_size

                # TXT corrupto o demasiado pequeño
                if size < 100:
                    log(f"TXT pequeño detectado -> eliminando: {txt_file}")
                    txt_file.unlink()

                else:
                    # TXT válido -> saltar
                    continue

            # -----------------------------
            # OCR
            # -----------------------------

            cmd = [
                "ocrmypdf",
                "--force-ocr",
                "--rotate-pages",
                "--deskew",
                "--optimize", "0",
                f"-j{WORKERS}",
                str(pdf),
                str(out_pdf),
            ]

            r = subprocess.run(cmd, capture_output=True, text=True)

            if r.returncode != 0:
                log(f"ERR OCR: {pdf} -> {r.stderr.strip()}")
                continue

            # -----------------------------
            # EXTRACCIÓN TEXTO
            # -----------------------------

            r = subprocess.run(
                ["pdftotext", str(out_pdf), str(txt_file)],
                capture_output=True,
                text=True
            )

            if r.returncode != 0:
                log(f"ERR TXT: {pdf} -> {r.stderr.strip()}")
                continue

            tanda_count += 1

        report(per_name, tanda_count, start_time)

    log("=== OCR BATCH COMPLETE ===")


if __name__ == "__main__":
    run()



