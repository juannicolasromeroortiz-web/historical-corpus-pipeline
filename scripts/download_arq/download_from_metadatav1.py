import json
import requests
from pathlib import Path
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print(">>> download_from_metadata.py iniciado")

METADATA_DIR = Path("metadata")
DATA_DIR = Path("data_normalized")

DATA_DIR.mkdir(exist_ok=True)

DELAY_SECONDS = 2
MAX_RETRIES = 3
TIMEOUT = 60


def load_metadata_files():
    return sorted(METADATA_DIR.glob("*.json"))


def download_pdf(url, target_path):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, verify=False, timeout=TIMEOUT)
            r.raise_for_status()
            target_path.write_bytes(r.content)
            return True
        except Exception as e:
            if attempt == MAX_RETRIES:
                print(f"  ❌ Error definitivo al descargar: {e}")
                return False
            time.sleep(DELAY_SECONDS * attempt)


def main():
    config = json.loads(Path("logs/corpus_config.json").read_text(encoding="utf-8"))
    year_start = int(config["year_start"])
    year_end = int(config["year_end"])

    downloaded = 0
    skipped = 0

    for meta_path in load_metadata_files():
        print(f"\nProcesando metadata: {meta_path.name}")

        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        if meta.get("status") == "downloaded":
            print("  ↪ Ya descargado, se omite")
            continue

        year = meta.get("year")

        if year is not None:
            if not (year_start <= int(year) <= year_end):
                meta["status"] = "skipped_out_of_range"
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
                print(f"  ↷ Excluido por fecha: year={year}")
                skipped += 1
                continue

        pdf_path = DATA_DIR / meta["pdf_filename"]

        if pdf_path.exists():
            meta["status"] = "downloaded"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            print("  ↪ PDF ya existe, marcado como descargado")
            continue

        print(f"  → Descargando PDF desde: {meta['download_url']}")

        ok = download_pdf(meta["download_url"], pdf_path)
        meta["status"] = "downloaded" if ok else "failed"

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        if ok:
            downloaded += 1
            print("  ✔ Descarga exitosa")
        else:
            print("  ❌ Falló la descarga")

        time.sleep(DELAY_SECONDS)

    print("\n=== RESUMEN DESCARGA ===")
    print(f"✔ Descargados: {downloaded}")
    print(f"↷ Excluidos por fecha: {skipped}")


if __name__ == "__main__":
    main()








