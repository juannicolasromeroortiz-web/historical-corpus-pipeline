#!/usr/bin/env python3
import csv
from pathlib import Path
import re
import os

# ===============================
# CONFIGURACIÓN
# ===============================
KEYWORDS = os.environ.get("KEYWORDS", "estudiante").split(",")
KEYWORDS = [kw.strip() for kw in KEYWORDS if kw.strip()]
WINDOW_WORDS = 40       # ±40 palabras alrededor de la keyword
TOP_SNIPPETS = 3        # número máximo de snippets por documento

# Paths
BASE = Path(__file__).resolve().parents[2]  # subimos un nivel más
CONSTELACIONES_FILE = BASE / "exports_recovered" / "constelaciones_semanticas.csv"
SUBCORPUS_FILE = BASE / "exports_recovered" / "keyword_subcorpus_top.csv"
DATA_FINAL_DIR = BASE / "organized_final"  # raíz de periódicos con la jerarquía
OUTPUT_FILE = BASE / "exports_recovered" / "snippets_top.csv"


# ===============================
# FUNCIONES
# ===============================

def load_constelaciones(file_path):
    """
    Carga las constelaciones semánticas organizadas por tramos temporales.
    """
    constelaciones = []
    with open(file_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=',')
        reader.fieldnames = [c.strip().lower() for c in reader.fieldnames]
        for row in reader:
            row = {k.strip().lower(): v for k, v in row.items()}
            year_start = int(row["year_start"])
            year_end = int(row["year_end"])
            core = [w.strip() for w in row.get("core", "").split(";") if w.strip()]
            support = [w.strip() for w in row.get("support", "").split(";") if w.strip()]
            constelaciones.append({
                "year_start": year_start,
                "year_end": year_end,
                "CORE": core,
                "SUPPORT": support
            })
    return constelaciones

def get_constellation_for_year(constelaciones, year):
    for c in constelaciones:
        if c["year_start"] <= year <= c["year_end"]:
            return c
    return {"CORE": [], "SUPPORT": []}

def extract_snippets(text, keyword, window_words=40):
    words = text.split()
    snippets = []
    for i, w in enumerate(words):
        if w.lower() == keyword.lower():
            start = max(i - window_words, 0)
            end = min(i + window_words + 1, len(words))
            snippet = " ".join(words[start:end])
            snippets.append(snippet)
    return snippets

def score_snippet(snippet, constellation, keyword):
    words = re.findall(r"\w+", snippet.lower())
    core_hits = sum(1 for w in words if w in [c.lower() for c in constellation["CORE"]])
    support_hits = sum(1 for w in words if w in [s.lower() for s in constellation["SUPPORT"]])
    keyword_hits = sum(1 for w in words if w == keyword.lower())
    
    score = core_hits * 10 + support_hits * 5
    if core_hits + support_hits == 0 and keyword_hits > 0:
        score = 1
    return score, core_hits, support_hits, keyword_hits

# ===============================
# MAIN
# ===============================

def main():
    # Cargar constelaciones
    constelaciones = load_constelaciones(CONSTELACIONES_FILE)
    
    # Leer subcorpus con hits_exact >= 2
    documents = []
    with open(SUBCORPUS_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row.get("hits_exact", 0)) >= 2:
                documents.append({
                    "periodico": row["periodico"],
                    "numero": row["numero"],
                    "year": int(row["year"])
                })

    output_rows = []

    # Procesar cada documento
    for doc in documents:
        txt_path = DATA_FINAL_DIR / doc["periodico"] / doc["numero"] / "input" / "ocr.txt"
        if not txt_path.exists():
            print(f"⚠️ No se encontró ocr.txt para {doc['periodico']}/{doc['numero']}")
            continue

        text = txt_path.read_text(encoding="utf-8", errors="ignore")
        constellation = get_constellation_for_year(constelaciones, doc["year"])
        
        # Iterar por cada keyword
        for KEYWORD in KEYWORDS:
            snippets = extract_snippets(text, KEYWORD, WINDOW_WORDS)
            
            scored_snippets = []
            for s in snippets:
                score, core_hits, support_hits, keyword_hits = score_snippet(s, constellation, KEYWORD)
                scored_snippets.append({
                    "periodico": doc["periodico"],
                    "numero": doc["numero"],
                    "year": doc["year"],
                    "keyword": KEYWORD,
                    "snippet": s,
                    "score": score,
                    "core_hits": core_hits,
                    "support_hits": support_hits,
                    "keyword_hits": keyword_hits
                })
            
            top_snippets = sorted(scored_snippets, key=lambda x: x["score"], reverse=True)[:TOP_SNIPPETS]
            output_rows.extend(top_snippets)
    
    # Guardar CSV final
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["periodico", "numero", "year", "keyword", "snippet", "score", "core_hits", "support_hits", "keyword_hits"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)
    
    print(f"✔ Extracción de snippets completada. Output: {OUTPUT_FILE}")

# ===============================
if __name__ == "__main__":
    main()






