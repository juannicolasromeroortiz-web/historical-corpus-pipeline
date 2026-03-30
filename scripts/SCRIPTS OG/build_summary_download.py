import json
from pathlib import Path
import re

ROOT = Path("banrep_corpus/estudiante_1847_1871")
SUMMARY_FILE = Path("summary_download.json")


def extract_year_from_filename(name):
    """
    Extrae AAAA desde un nombre tipo Periodico_1870-12-31.pdf
    """
    m = re.search(r"(18\d{2})-\d{2}-\d{2}", name)
    if m:
        return int(m.group(1))
    return None


def build_summary():
    summary = {
        "corpus": "estudiante_1847_1871",
        "fuente": "Biblioteca Digital Banco de la República",
        "estructura": str(ROOT),
        "periodicos": [],
        "totales": {
            "periodicos": 0,
            "pdfs": 0,
            "pdfs_con_error": 0,
            "tamano_mb": 0
        }
    }

    total_pdfs = 0
    total_failed = 0
    total_size = 0

    for periodico_dir in sorted(ROOT.iterdir()):
        if not periodico_dir.is_dir():
            continue

        meta_path = periodico_dir / "metadata.json"
        if not meta_path.exists():
            continue

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        pdfs = list(periodico_dir.glob("*.pdf"))

        fechas = []
        size_mb = 0

        for pdf in pdfs:
            total_pdfs += 1
            size_mb += pdf.stat().st_size / (1024 * 1024)

            year = extract_year_from_filename(pdf.name)
            if year:
                fechas.append(year)

        errores = [
            n for n in meta.get("numeros_descargados", [])
            if n.get("error") == "download_failed"
        ]

        total_failed += len(errores)
        total_size += size_mb

        resumen_periodico = {
            "nombre": meta.get("periodico"),
            "carpeta": periodico_dir.name,
            "source_url": meta.get("source_url"),
            "descripcion_objeto": meta.get("descripcion_objeto", ""),
            "criterio_fechas": meta.get("criterio_fechas", {}),
            "pdfs_existentes": len(pdfs),
            "pdfs_fallidos": len(errores),
            "tamano_mb": round(size_mb, 2),
            "rango_fechas_detectado": {
                "min": min(fechas) if fechas else None,
                "max": max(fechas) if fechas else None
            }
        }

        summary["periodicos"].append(resumen_periodico)

    summary["totales"]["periodicos"] = len(summary["periodicos"])
    summary["totales"]["pdfs"] = total_pdfs
    summary["totales"]["pdfs_con_error"] = total_failed
    summary["totales"]["tamano_mb"] = round(total_size, 2)

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("✔ summary_download.json generado")
    print(f"Periódicos: {summary['totales']['periodicos']}")
    print(f"PDFs: {summary['totales']['pdfs']}")
    print(f"Tamaño total: {summary['totales']['tamano_mb']} MB")


if __name__ == "__main__":
    build_summary()

