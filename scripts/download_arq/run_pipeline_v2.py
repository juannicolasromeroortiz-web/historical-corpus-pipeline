import json
import subprocess
from pathlib import Path
from datetime import datetime

URLS_FILE = Path("scripts/download_arq/periodicos_unicos_fase_3.txt")
STATE_FILE = Path("logs/metadata_state.json")

METADATA_SCRIPT = "scripts/download_arq/download_metadata_by_periodicos_v2.py"
DOWNLOAD_SCRIPT = "scripts/download_arq/download_from_metadata_v3.py"
ORGANIZE_SCRIPT = "scripts/download_arq/rename_and_organize.py"
QC_SCRIPT = "scripts/download_arq/qc_corpus.py"

def count_total_urls():
    with open(URLS_FILE, encoding="utf-8") as f:
        return len([l for l in f if l.strip()])

def load_state():
    if not STATE_FILE.exists():
        return {"last_index": 0}
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)

def run(cmd):
    print(f"\n▶ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

def main():
    print("\n=== PIPELINE OCR HISTÓRICO ===")

    total = count_total_urls()
    state = load_state()
    last = state.get("last_index", 0)

    print(f"📄 total URLs: {total}")
    print(f"✔ procesados: {last}")
    print(f"⏳ pendientes: {total - last}")

    if last >= total:
        print("\n🎉 Corpus completo.")
        return

    try:
        n = int(input("\n¿Cuántos periódicos procesar? "))
        if n <= 0: raise ValueError
    except ValueError:
        print("❌ número inválido")
        return

    try:
        year_start = int(input("Año inicio (YYYY): "))
        year_end = int(input("Año fin (YYYY): "))
    except ValueError:
        print("❌ años inválidos")
        return

    if year_start > year_end:
        print("❌ inicio > fin")
        return

    config = {
        "year_start": year_start,
        "year_end": year_end,
        "generated_at": datetime.utcnow().isoformat(),
        "source": str(URLS_FILE)
    }
    Path("logs").mkdir(exist_ok=True)
    Path("logs/corpus_config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")

    if last + n > total:
        n = total - last
        print(f"⚠ ajustado a {n}")

    print("\n🧱 metadata…")
    run(["python", METADATA_SCRIPT, "--batch-size", str(n)])

    print("\n⬇ download…")
    run(["python", DOWNLOAD_SCRIPT])

    print("\n📂 organizing OCR4all…")
    run(["python", ORGANIZE_SCRIPT])

    if input("\n¿QC? (s/n): ").lower() == "s":
        run(["python", QC_SCRIPT])

    print("\n✔ done.\n")

if __name__ == "__main__":
    main()


