import json
import subprocess
from pathlib import Path
from datetime import datetime

URLS_FILE = Path("scripts/periodicos_unicos.txt")
STATE_FILE = Path("logs/metadata_state.json")

METADATA_SCRIPT = "scripts/download_metadata_by_periodicos_v2.py"
DOWNLOAD_SCRIPT = "scripts/download_from_metadata_v3.py"
ORGANIZE_SCRIPT = "scripts/rename_and_organize.py"
QC_SCRIPT = "scripts/qc_corpus.py"

def count_total_urls():
    with open(URLS_FILE, encoding="utf-8") as f:
        return len([l for l in f if l.strip()])

def load_state():
    if not STATE_FILE.exists():
        return {"last_index": 0}
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)

def run(cmd):
    print(f"\n▶ Ejecutando: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main():
    print("\n=== PIPELINE OCR HISTÓRICO — EJECUCIÓN AUTOMÁTICA ===\n")

    total = count_total_urls()
    state = load_state()
    last = state.get("last_index", 0)

    print(f"📄 Periódicos en lista total : {total}")
    print(f"✅ Periódicos ya procesados  : {last}")
    print(f"⏳ Periódicos pendientes     : {total - last}")

    if last >= total:
        print("\n🎉 Todo el corpus ya fue procesado.")
        print("→ Ejecutando QC final…")
        run(["python", QC_SCRIPT])
        return

    try:
        n = int(input("\n¿Cuántos periódicos quieres procesar en esta tanda? "))
    except ValueError:
        print("❌ Número inválido.")
        return

    if n <= 0:
        print("❌ El número debe ser mayor que cero.")
        return

    # --- corpus config ---
    try:
        year_start = int(input("Año inicial del corpus (YYYY): "))
        year_end = int(input("Año final del corpus (YYYY): "))
    except ValueError:
        print("❌ Los años deben ser números.")
        return

    if year_start > year_end:
        print("❌ Año inicial > año final.")
        return

    config = {
        "corpus_name": "prensa_colombiana_siglo_xix",
        "year_start": year_start,
        "year_end": year_end,
        "date_policy": "download_even_if_no_year",
        "generated_at": datetime.utcnow().isoformat(),
        "source_urls_file": str(URLS_FILE),
    }

    Path("logs").mkdir(exist_ok=True)
    Path("logs/corpus_config.json").write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    if last + n > total:
        n = total - last
        print(f"⚠ Ajustando tanda a {n} periódicos restantes.")

    print(f"\n🚀 Se procesarán {n} periódicos en esta tanda.\n")

    # --- ejecución por fases ---
    print("🧱 [1/3] Generando metadata…")
    run(["python", METADATA_SCRIPT, "--batch-size", str(n)])

    print("\n⬇️  [2/3] Descargando PDFs…")
    run(["python", DOWNLOAD_SCRIPT])

    print("\n📁 [3/3] Organizando para OCR4all…")
    run(["python", ORGANIZE_SCRIPT])

    # --- resumen ---
    state = load_state()
    new_last = state.get("last_index", last)

    print("\n=== REPORTE DE TANDA ===")
    print(f"✔ Procesados en esta tanda : {new_last - last}")
    print(f"📍 Total procesados        : {new_last}")
    print(f"⏳ Restantes               : {total - new_last}")

    # --- QC automático ---
    print("\n🧪 Ejecutando QC automático…")
    run(["python", QC_SCRIPT])

    print("\n✔ Pipeline ejecutado correctamente.\n")

if __name__ == "__main__":
    main()


