import subprocess
from pathlib import Path
import unicodedata

# =====================
# CONFIG
# =====================

DATA_PDF = Path("data_normalized")
DATA_PNG = Path("data_png")

DPI = 300

DATA_PNG.mkdir(exist_ok=True)

# =====================
# UTILIDADES
# =====================

def normalize_name(name: str) -> str:
    return (
        unicodedata.normalize("NFKD", name)
        .encode("ascii", "ignore")
        .decode("ascii")
    )

def pdf_to_png(pdf_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "mutool", "draw",
        "-r", str(DPI),
        "-o", str(out_dir / "%04d.png"),
        str(pdf_path)
    ]

    subprocess.run(cmd, check=True)

# =====================
# MAIN
# =====================

def main():
    pdfs = sorted(DATA_PDF.glob("*.pdf"))

    if not pdfs:
        print("❌ No se encontraron PDFs en data_normalized/")
        return

    print(f"📄 PDFs detectados: {len(pdfs)}")

    for pdf in pdfs:
        pdf_name = normalize_name(pdf.stem)

        project_dir = DATA_PNG / pdf_name
        input_dir = project_dir / "input"

        if input_dir.exists() and any(input_dir.glob("*.png")):
            print(f"↪ Ya rasterizado: {pdf_name}")
            continue

        print(f"🖼 Rasterizando: {pdf.name}")
        pdf_to_png(pdf, input_dir)

    print("\n✔ Rasterización completa. Proyectos listos para OCR4all.")

if __name__ == "__main__":
    main()

