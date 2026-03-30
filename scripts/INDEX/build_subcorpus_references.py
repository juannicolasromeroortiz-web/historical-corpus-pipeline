#!/usr/bin/env python3
"""
FASE 3+ — build_subcorpus_fase3_refs.py

Construye subcorpus REFERENCIADOS (sin copiar PDFs),
agrupando números de periódico por combinaciones de palabras clave
y organizando la salida por periódico.
"""

import csv
import json
from pathlib import Path
from collections import defaultdict

# =========================================================
# BASE DEL PROYECTO
# =========================================================

BASE = Path(__file__).resolve().parents[2]

EXPORTS = BASE / "exports_recovered"
METADATA = BASE / "recovery_pipeline" / "metadata_recovered_enriched"
OUTPUT_BASE = BASE / "subcorpus_recovered_refs"

CSV_PATH = EXPORTS / "keyword_subcorpus_top.csv"

# =========================================================
# UTILIDADES
# =========================================================

def load_csv(path: Path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=",")
        reader.fieldnames = [h.strip() for h in reader.fieldnames]
        return list(reader)



def extract_id_from_numero(numero: str) -> str | None:
    """
    Espera algo tipo: ElMosaico_1860_2704
    """
    if "_" not in numero:
        return None
    return numero.rsplit("_", 1)[-1]


def load_metadata_by_id(doc_id: str) -> dict | None:
    """
    Busca en metadata/*_<ID>.json
    """
    for meta_path in METADATA.glob(f"*_{doc_id}.json"):
        try:
            with open(meta_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def safe_filename(name: str) -> str:
    """
    Normaliza nombres de periódico para archivo.
    """
    return (
        name.replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "")
            .replace(";", "")
            .replace(",", "")
    )


# =========================================================
# MAIN
# =========================================================

def main():
    rows = load_csv(CSV_PATH)
    # -----------------------------------------------------
    # Agrupar por número (procesar una sola vez cada número)
    # -----------------------------------------------------

    grouped = defaultdict(lambda: {
        "keywords": set()
    })

    for row in rows:
        numero = row["numero"]
        grouped[numero]["keywords"].add(row["keyword"])

    # -----------------------------------------------------
    # Acumulador final:
    # (keyword_combo, periodico) -> [metadata, ...]
    # -----------------------------------------------------

    grouped_refs = defaultdict(list)

    for numero, data in grouped.items():
        keywords = sorted(data["keywords"])
        keyword_folder = "__".join(keywords)

        doc_id = extract_id_from_numero(numero)
        if not doc_id:
            print(f"[WARN] No se pudo extraer ID de {numero}")
            continue

        meta = load_metadata_by_id(doc_id)
        if not meta:
            print(f"[WARN] Metadata no encontrada para ID {doc_id}")
            continue

        periodico = meta.get("periodico")
        if not periodico:
            print(f"[WARN] Metadata sin periódico para ID {doc_id}")
            continue

        key = (keyword_folder, periodico)
        grouped_refs[key].append(meta)

    # -----------------------------------------------------
    # Escritura de archivos por keyword + periódico
    # -----------------------------------------------------

    for (keyword_folder, periodico), metas in grouped_refs.items():
        out_dir = OUTPUT_BASE / keyword_folder
        out_dir.mkdir(parents=True, exist_ok=True)

        periodico_safe = safe_filename(periodico)

        txt_path = out_dir / f"{periodico_safe}.txt"
        csv_path = out_dir / f"{periodico_safe}.csv"

        # -----------------------------
        # TXT (humano)
        # -----------------------------

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"PALABRA(S) CLAVE: {keyword_folder.replace('__', ', ')}\n")
            f.write(f"PERIÓDICO: {periodico}\n")
            f.write("=" * 70 + "\n\n")

            for meta in metas:
                f.write(
                    f"""TÍTULO / NÚMERO: {meta.get("titulo_numero")}
AÑO: {meta.get("year")}
DESCRIPCIÓN:
{meta.get("descripcion_objeto", "").strip()}

LINK DE DESCARGA:
{meta.get("download_url")}

-----------------------------------------------

"""
                )

        # -----------------------------
        # CSV (estructurado)
        # -----------------------------

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "keywords",
                    "periodico",
                    "titulo_numero",
                    "year",
                    "descripcion_objeto",
                    "download_url",
                    "collection",
                    "child_id",
                    "pdf_filename",
                    "created_at"
                ]
            )
            writer.writeheader()

            for meta in metas:
                writer.writerow({
                    "keywords": keyword_folder.replace("__", ","),
                    "periodico": periodico,
                    "titulo_numero": meta.get("titulo_numero"),
                    "year": meta.get("year"),
                    "descripcion_objeto": meta.get("descripcion_objeto"),
                    "download_url": meta.get("download_url"),
                    "collection": meta.get("collection"),
                    "child_id": meta.get("child_id"),
                    "pdf_filename": meta.get("pdf_filename"),
                    "created_at": meta.get("created_at")
                })

        print(f"[OK] Referencias creadas: {keyword_folder} / {periodico}")

    print("\nFASE 3+ — subcorpus REFERENCIADO construido correctamente.")


if __name__ == "__main__":
    main()


