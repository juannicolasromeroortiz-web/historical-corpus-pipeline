#!/usr/bin/env python3
import sqlite3
import csv
import re
from pathlib import Path
from collections import Counter

import spacy

# ===============================
# CARGA MODELO spaCy
# ===============================
nlp = spacy.load("es_core_news_md")

# ===============================
# PATHS DEL PROYECTO
# ===============================
BASE = Path(__file__).resolve().parents[2]
DB = BASE / "db" / "documents_recover.db"
DATA_BASE = BASE / "organized_final"

OUT = BASE / "exports_recovered"
OUT.mkdir(exist_ok=True)

OUT_FILE = OUT / "constelaciones_spacy_por_ano.csv"

# ===============================
# CONFIGURACIÓN
# ===============================
KEYWORDS = ["estudiante"]
WINDOW_SIZE = 40        # palabras antes y después
MIN_FREQ = 2            # frecuencia mínima por año

# ===============================
# FUNCIONES
# ===============================
def normalize(text: str) -> str:
    return text.lower()

def extract_windows(text: str, keyword: str, window: int):
    words = text.split()
    windows = []

    for i, w in enumerate(words):
        if w == keyword:
            start = max(0, i - window)
            end = min(len(words), i + window + 1)
            windows.append(" ".join(words[start:end]))

    return windows

def is_valid_token(token, keyword):
    if token.is_stop:
        return False
    if token.is_punct or token.is_space:
        return False
    if token.pos_ not in ("NOUN", "ADJ"):
        return False
    if len(token.lemma_) < 4:
        return False
    if token.lemma_ == keyword:
        return False
    return True

# ===============================
# MAIN
# ===============================
def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    results = []

    for kw in KEYWORDS:
        print(f"→ Procesando constelaciones para '{kw}'")

        sql = """
        SELECT d.year, d.periodico, d.numero
        FROM docs_fts f
        JOIN docs d ON f.rowid = d.rowid
        WHERE docs_fts MATCH ?
        """
        rows = conn.execute(sql, (kw,)).fetchall()

        yearly_counter = {}

        for r in rows:
            year = r["year"]

            txt_path = (
                DATA_BASE
                / str(r["periodico"])
                / str(r["numero"])
                / "input"
                / "ocr.txt"
            )

            if not txt_path.exists() or year is None:
                continue

            text = normalize(
                txt_path.read_text(encoding="utf-8", errors="ignore")
            )

            windows = extract_windows(text, kw, WINDOW_SIZE)

            if year not in yearly_counter:
                yearly_counter[year] = Counter()

            for w in windows:
                doc = nlp(w)

                for token in doc:
                    if is_valid_token(token, kw):
                        yearly_counter[year][token.lemma_] += 1

        # ===============================
        # EXPORT POR AÑO
        # ===============================
        for year, counter in sorted(yearly_counter.items()):
            for concept, freq in counter.items():
                if freq >= MIN_FREQ:
                    results.append({
                        "year": year,
                        "keyword": kw,
                        "concept_candidate": concept,
                        "frequency": freq
                    })

    conn.close()

    # ===============================
    # EXPORT CSV
    # ===============================
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "year",
                "keyword",
                "concept_candidate",
                "frequency"
            ]
        )
        writer.writeheader()
        writer.writerows(results)

    print("✔ Constelaciones semánticas (spaCy) generadas")
    print(f"  - {OUT_FILE}")

# ===============================
if __name__ == "__main__":
    main()

