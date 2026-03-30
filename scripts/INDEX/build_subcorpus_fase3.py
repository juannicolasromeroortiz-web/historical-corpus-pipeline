#!/usr/bin/env python3
"""
FASE 3+ — build_subcorpus_fase3_multi_keyword.py

Construye subcorpus temáticos agrupando números de periódico
por combinaciones de palabras clave (1 o más),
SIN modificar identidad documental.
"""

import csv
import shutil
from pathlib import Path
from collections import defaultdict

# =========================================================
# BASE DEL PROYECTO
# =========================================================

BASE = Path(__file__).resolve().parents[2]

DATA_FINAL = BASE / "data_final"
EXPORTS = BASE / "exports"
OUTPUT_BASE = BASE / "subcorpus_fase3"

CSV_PATH = EXPORTS / "keyword_subcorpus_top.csv"

# =========================================================
# UTILIDADES
# =========================================================

def load_csv(path: Path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        sample = f.read(2048)
        f.seek(0)
        dialect = csv.Sniffer().sniff(sample)
        reader = csv.DictReader(f, dialect=dialect)
        reader.fieldnames = [h.strip() for h in reader.fieldnames]
        return list(reader)


def find_periodico_dir(periodico: str) -> Path | None:
    for d in DATA_FINAL.iterdir():
        if d.is_dir() and d.name == periodico:
            return d
    return None


def find_numero_dir(periodico_dir: Path, numero: str) -> Path | None:
    candidate = periodico_dir / numero
    if candidate.exists() and candidate.is_dir():
        return candidate
    return None


def find_pdf(numero_dir: Path) -> Path | None:
    for pdf in numero_dir.rglob("*.pdf"):
        return pdf
    return None


# =========================================================
# MAIN
# =========================================================

def main():
    rows = load_csv(CSV_PATH)

    # -----------------------------------------------------
    # Agrupar por numero
    # -----------------------------------------------------

    grouped = defaultdict(lambda: {
        "periodico": None,
        "keywords": set()
    })

    for row in rows:
        numero = row["numero"]
        grouped[numero]["periodico"] = row["periodico"]
        grouped[numero]["keywords"].add(row["keyword"])

    # -----------------------------------------------------
    # Procesar cada numero una sola vez
    # -----------------------------------------------------

    for numero, data in grouped.items():
        periodico = data["periodico"]
        keywords = sorted(data["keywords"])

        keyword_folder = "__".join(keywords)

        periodico_dir = find_periodico_dir(periodico)
        if periodico_dir is None:
            print(f"[WARN] Periódico no encontrado: {periodico}")
            continue

        numero_dir = find_numero_dir(periodico_dir, numero)
        if numero_dir is None:
            print(f"[WARN] Número no encontrado: {numero}")
            continue

        pdf_path = find_pdf(numero_dir)
        if pdf_path is None:
            print(f"[WARN] PDF no encontrado en: {numero}")
            continue

        target_input = (
            OUTPUT_BASE /
            keyword_folder /
            numero /
            "input"
        )
        target_input.mkdir(parents=True, exist_ok=True)

        shutil.copy2(pdf_path, target_input / pdf_path.name)
        print(f"[OK] Copiado: {keyword_folder} / {numero}")

    print("\nFASE 3+ — subcorpus multi-keyword construido correctamente.")


if __name__ == "__main__":
    main()





