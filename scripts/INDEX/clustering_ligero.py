#!/usr/bin/env python3
"""
constelaciones_semanticas.py

Construye constelaciones semánticas (episodios discursivos estructurados)
a partir de:
- episodios_discursivos.csv
- keyword_timeline.csv

No interpreta semánticamente: organiza evidencia empírica.
"""

import csv
from pathlib import Path

# ===============================
# PATHS
# ===============================
BASE = Path(__file__).resolve().parents[2]
DATA = BASE / "exports_recovered"

EPISODIOS_FILE = DATA / "episodios_discursivos.csv"
TIMELINE_FILE = DATA / "keyword_timeline.csv"

OUT_CLUSTERS = DATA / "constelaciones_semanticas.csv"
OUT_SUMMARY = DATA / "constelaciones_resumen.txt"

# ===============================
# CONFIGURACIÓN
# ===============================
DOC_JUMP_THRESHOLD = 5      # cambio fuerte en docs_with_term
CENTRAL_TRIGGER = 1         # aparición de centrales
OCR_TRIGGER = 1             # reprocess_priority_docs >= 1

# ===============================
# UTILIDADES
# ===============================
def parse_years_list(value):
    return set(int(y) for y in value.split(";") if y.strip())

def load_csv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ===============================
# STEP 1 — DETECTAR VENTANAS TEMPORALES
# ===============================
def detect_time_windows(timeline_rows):
    windows = []
    current = None

    prev_docs = None

    for row in timeline_rows:
        year = int(row["year"])
        docs = int(row["docs_with_term"])
        central = int(row["central_docs"])
        ocr = int(row["reprocess_priority_docs"])

        trigger = False

        if prev_docs is not None and abs(docs - prev_docs) >= DOC_JUMP_THRESHOLD:
            trigger = True
        if central >= CENTRAL_TRIGGER:
            trigger = True
        if ocr >= OCR_TRIGGER:
            trigger = True

        if current is None or trigger:
            if current:
                current["end"] = year - 1
                windows.append(current)
            current = {
                "start": year,
                "end": year,
                "years": set([year])
            }
        else:
            current["end"] = year
            current["years"].add(year)

        prev_docs = docs

    if current:
        windows.append(current)

    return windows

# ===============================
# STEP 2 — CONSTELACIONES
# ===============================
def build_constellations(episodios, windows):
    constellations = []

    for i, w in enumerate(windows, start=1):
        core = []
        support = []
        context = []

        for ep in episodios:
            years = parse_years_list(ep["years_list"])
            if years & w["years"]:
                role = ep["discursive_role"]
                concept = ep["concept"]

                if role == "CORE":
                    core.append(concept)
                elif role == "SUPPORT":
                    support.append(concept)
                else:
                    context.append(concept)

        constellations.append({
            "window_id": i,
            "year_start": w["start"],
            "year_end": w["end"],
            "core": "; ".join(sorted(set(core))),
            "support": "; ".join(sorted(set(support))),
            "context": "; ".join(sorted(set(context))),
        })

    return constellations

# ===============================
# MAIN
# ===============================
def main():
    episodios = load_csv(EPISODIOS_FILE)
    timeline = load_csv(TIMELINE_FILE)

    windows = detect_time_windows(timeline)
    constellations = build_constellations(episodios, windows)

    # CSV
    with open(OUT_CLUSTERS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "window_id",
                "year_start",
                "year_end",
                "core",
                "support",
                "context"
            ]
        )
        writer.writeheader()
        writer.writerows(constellations)

    # TXT resumen
    with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
        for c in constellations:
            f.write(f"Constelación {c['window_id']} ({c['year_start']}–{c['year_end']})\n")
            f.write(f"  CORE: {c['core']}\n")
            f.write(f"  SUPPORT: {c['support']}\n")
            f.write(f"  CONTEXT: {c['context']}\n\n")

    print("✔ Constelaciones semánticas generadas")
    print(f"  - {OUT_CLUSTERS}")
    print(f"  - {OUT_SUMMARY}")

# ===============================
if __name__ == "__main__":
    main()

