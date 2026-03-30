#!/usr/bin/env python3
import sqlite3
import csv
import re
from collections import defaultdict
from pathlib import Path

# ===============================
# CONFIGURACIÓN
# ===============================
KEYWORD = "estudiante"
WINDOW_SIZE = 20
MIN_FREQ = 2   # umbral mínimo conceptual

# Stopwords ampliadas (históricas + discursivas)
STOPWORDS = {
    "el","la","los","las","de","del","y","o","a","en","un","una",
    "que","por","con","para","se","su","al","como","más","menos",
    "pero","pues","cuando","tal","solo","aun","qué","sin","era",
    "fue","dijo","decía","había","habia","tiene","tener","ser",
    "estar","son","era","eran","uno","otro","dos","tres","cuatro",
    "usted","ustedes","sus","mis","les","ellos","ellas","esto",
    "esa","ese","aquí","alli","ahí","muy","mas","ya","siempre", "más", "hasta", "este", "mismo", "porque"
}

# Verbos frecuentes (forma superficial)
COMMON_VERBS = {
    "dijo","repuso","habló","hablo","respondió","respondio",
    "era","fue","había","habia","estaba","estaban","tiene",
    "tener","ser","estar","puede","puede","hizo","hacer", "hallaba"
}

# ===============================
# PATHS
# ===============================
BASE = Path(__file__).resolve().parents[1]
DB = BASE / "db" / "documents.db"
DATA_BASE = BASE / "data_final"

OUT = BASE / "exports"
OUT.mkdir(exist_ok=True)

OUTPUT = OUT / "constelaciones_por_ano.csv"

# ===============================
# FUNCIONES
# ===============================
def normalize(text: str) -> list:
    text = text.lower()
    text = re.sub(r"[^a-záéíóúñü\s]", " ", text)
    return text.split()

def is_concept_candidate(word: str) -> bool:
    if len(word) < 4:
        return False
    if word in STOPWORDS:
        return False
    if word in COMMON_VERBS:
        return False
    if word.endswith("mente"):
        return False
    return True

# ===============================
# MAIN
# ===============================
def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    sql = """
    SELECT d.year, d.periodico, d.numero
    FROM docs_fts f
    JOIN docs d ON f.rowid = d.rowid
    WHERE docs_fts MATCH ?
    """

    rows = conn.execute(sql, (KEYWORD,)).fetchall()
    conn.close()

    constellations = defaultdict(lambda: defaultdict(int))

    for r in rows:
        year = r["year"]
        if not year:
            continue

        txt_path = (
            DATA_BASE
            / str(r["periodico"])
            / str(r["numero"])
            / "input"
            / "ocr.txt"
        )

        if not txt_path.exists():
            continue

        tokens = normalize(
            txt_path.read_text(encoding="utf-8", errors="ignore")
        )

        for i, token in enumerate(tokens):
            if token != KEYWORD:
                continue

            start = max(0, i - WINDOW_SIZE)
            end = min(len(tokens), i + WINDOW_SIZE + 1)
            window = tokens[start:i] + tokens[i+1:end]

            for w in window:
                if is_concept_candidate(w):
                    constellations[year][w] += 1

    # ===============================
    # EXPORT
    # ===============================
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "year",
            "keyword",
            "concept_candidate",
            "frequency"
        ])

        for year in sorted(constellations.keys()):
            for word, freq in sorted(
                constellations[year].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                if freq >= MIN_FREQ:
                    writer.writerow([
                        year,
                        KEYWORD,
                        word,
                        freq
                    ])

    print("✔ Constelaciones conceptuales por año generadas")
    print(f"→ {OUTPUT}")

# ===============================
if __name__ == "__main__":
    main()


