#!/usr/bin/env python3
import os
from pathlib import Path

OCR4ALL_DATA = Path("/home/juan_romero/ocr4all/data")
EXTENSIONS = {".tif", ".tiff"}

def is_valid_project(project_path: Path) -> bool:
    input_dir = project_path / "input"
    if not input_dir.exists():
        return False

    images = [p for p in input_dir.iterdir() if p.suffix.lower() in EXTENSIONS]
    return len(images) > 0

def main():
    print("\n=== OCR4all FASE 1 — Preparación batch masivo ===\n")

    if not OCR4ALL_DATA.exists():
        raise RuntimeError(f"No existe el directorio OCR4all data: {OCR4ALL_DATA}")

    projects = []
    skipped = []

    for item in sorted(OCR4ALL_DATA.iterdir()):
        if not item.is_dir():
            continue

        if is_valid_project(item):
            projects.append(item.name)
        else:
            skipped.append(item.name)

    print(f"✔ Proyectos válidos encontrados: {len(projects)}")
    for p in projects:
        print(f"  - {p}")

    if skipped:
        print(f"\n⚠ Proyectos ignorados (estructura incompleta): {len(skipped)}")
        for s in skipped:
            print(f"  - {s}")

    # Archivo marcador (útil para trazabilidad)
    marker = OCR4ALL_DATA / "READY_FOR_OCR4ALL.txt"
    with marker.open("w", encoding="utf-8") as f:
        for p in projects:
            f.write(p + "\n")

    print(f"\n📄 Archivo generado: {marker}")
    print("\nFASE 1 completada. Los proyectos están listos para OCR4all.\n")
    print("👉 Ahora ejecuta OCR desde la GUI o vía batch controlado.\n")

if __name__ == "__main__":
    main()



