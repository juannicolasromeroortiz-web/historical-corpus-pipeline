import json
from pathlib import Path
import shutil

METADATA_DIR = Path("metadata")
DATA_DIR = Path("data_normalized")
OCR_DIR = Path("data_final")

def safe(name):
    return "".join(c for c in name if c.isalnum() or c in ("_", "-"))

def get_year(meta):
    y = meta.get("year")
    return int(y) if isinstance(y, int) else None

def main():
    if not DATA_DIR.exists():
        print("✔ No hay data_normalized — nada que organizar.")
        return

    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        print("✔ data_normalized vacío — nada que organizar.")
        return

    moved = 0
    skipped = 0

    for pdf in pdfs:
        # buscar metadata
        stem = pdf.stem  # GACETAOFICIAL1848_25265
        meta_path = METADATA_DIR / f"{stem}.json"
        if not meta_path.exists():
            print(f"⚠ sin metadata: {pdf.name}")
            skipped += 1
            continue

        meta = json.loads(meta_path.read_text(encoding="utf-8"))

        periodico = safe(meta.get("periodico", "UNKNOWN")) or "UNKNOWN"
        year = get_year(meta)
        cid = meta.get("child_id") or stem.split("_")[-1]

        if year:
            # fecha simple sin validar día/mes — correspondencia 19thC
            sub = f"{periodico}_{year}_{cid}"
        else:
            sub = f"{periodico}_{cid}"

        target = OCR_DIR / periodico / sub / "input"
        target.mkdir(parents=True, exist_ok=True)

        dest = target / pdf.name
        if dest.exists():
            print(f"⚠ duplicado: {dest}")
            continue

        shutil.move(str(pdf), str(dest))
        moved += 1

    # si movimos todo → cleanup
    remaining = list(DATA_DIR.glob("*.pdf"))
    if not remaining:
        shutil.rmtree(DATA_DIR)
        print("🧹 data_normalized eliminado (completamente organizado).")

    print("\n=== ORGANIZE REPORT ===")
    print(f"✔ moved: {moved}")
    print(f"⚠ skipped (sin metadata): {skipped}")
    print(f"📁 output: {OCR_DIR}")
    print("✔ done.\n")

    # QC se corre siempre al final
    import subprocess
    subprocess.run(["python", "scripts/qc_corpus.py"])

if __name__ == "__main__":
    main()



