#!/usr/bin/env python3
import sqlite3
import csv
import re
from pathlib import Path
import os

# ===============================
# PATHS DEL PROYECTO
# ===============================
BASE = Path(__file__).resolve().parents[2]
DB = BASE / "db" / "documents_recover.db"
DATA_BASE = BASE / "organized_final"

OUT = BASE / "exports_recovered"
OUT.mkdir(exist_ok=True)

# ===============================
# CONFIGURACIÓN
# ===============================
KEYWORDS = os.environ.get(
    "KEYWORDS",
    "estudiante,estudiantil,juventud,joven,colegio,colejio,universidad"
).split(",")
KEYWORDS = [kw.strip().lower() for kw in KEYWORDS if kw.strip()]


HITS_FILE = OUT / "keyword_hits_exact.csv"
SUBCORPUS_FILE = OUT / "keyword_subcorpus_top.csv"
FIRST_HITS_FILE = OUT / "keyword_first_hits.csv"

# ===============================
# FUNCIONES
# ===============================
def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def count_exact(keyword: str, text: str) -> int:
    pattern = re.compile(rf"\b{re.escape(keyword)}\b", re.IGNORECASE)
    return len(pattern.findall(text))


def build_semantic_pattern(keyword: str) -> re.Pattern:
    variants = {
        "estudiante": [
            r"estudiante",
            r"estu[dcl]iante",
            r"e\s*s\s*t\s*u\s*d\s*i\s*a\s*n\s*t\s*e",
        ],
        "estudiantil": [
            r"estudiantil",
            r"estu[dcl]iantil",
            r"e\s*s\s*t\s*u\s*d\s*i\s*a\s*n\s*t\s*i\s*l",
        ],
        "joven": [
            r"joven",
            r"jóven",
        ],
        "juventud": [
            r"juventud",
            r"juuentud",
            r"juventvd",
        ],
        "colegio": [
            r"colegio",
            r"colejio",
            r"colegi[o0]",
        ],
        "colejio": [
            r"colejio",
            r"colegio",
        ],
        "universidad": [
            r"universidad",
            r"vniuersidad",
            r"uniuersidad",
        ],
    }

    patterns = variants.get(keyword, [re.escape(keyword)])
    combined = "|".join(patterns)
    return re.compile(rf"\b({combined})\b", re.IGNORECASE)


def count_semantic(keyword: str, text: str) -> int:
    return len(build_semantic_pattern(keyword).findall(text))


def noise_ratio(text: str) -> float:
    if not text:
        return 1.0
    non_alpha = sum(1 for c in text if not c.isalpha() and not c.isspace())
    return non_alpha / len(text)


def attention_flag(score: float) -> str:
    if score >= 0.66:
        return "HIGH"
    elif score >= 0.40:
        return "MEDIUM"
    else:
        return "LOW"


def lexical_role(hits: int) -> str:
    if hits >= 5:
        return "CENTRAL"
    elif hits >= 2:
        return "SECONDARY"
    elif hits == 1:
        return "MENTION"
    else:
        return "NONE"


def ocr_action(hits: int) -> str:
    if hits >= 2:
        return "REPROCESS_PRIORITY"
    elif hits == 1:
        return "KEEP_AS_CONTEXT"
    else:
        return "OK"

# ===============================
# MAIN
# ===============================
def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    hits_rows = []
    subcorpus_rows = []
    first_hits_rows = []

    for kw in KEYWORDS:
        print(f"→ Procesando keyword: '{kw}'")

        sql = """
        SELECT d.rowid, d.year, d.periodico, d.numero
        FROM docs_fts f
        JOIN docs d ON f.rowid = d.rowid
        WHERE docs_fts MATCH ?
        """
        rows = conn.execute(sql, (kw,)).fetchall()
        records = []

        for r in rows:
            txt_path = (
                DATA_BASE
                / str(r["periodico"])
                / str(r["numero"])
                / "input"
                / "ocr.txt"
            )

            if not txt_path.exists():
                continue

            text = normalize(
                txt_path.read_text(encoding="utf-8", errors="ignore")
            )

            text_length = len(text)
            hits_exact = count_exact(kw, text)
            hits_semantic = count_semantic(kw, text)
            noise = noise_ratio(text)

            record = {
                "keyword": kw,
                "year": r["year"],
                "periodico": r["periodico"],
                "numero": r["numero"],
                "hits_exact": hits_exact,
                "hits_semantic": hits_semantic,
                "text_length": text_length,
                "density_exact": hits_exact / text_length if text_length else 0,
                "density_semantic": hits_semantic / text_length if text_length else 0,
                "noise_ratio": round(noise, 4),
            }
            records.append(record)

        hits_rows.extend(records)

        ranked = sorted(records, key=lambda r: r["hits_semantic"], reverse=True)
        subcorpus_rows.extend(records)

        chronological = sorted(
            [r for r in records if r["year"] is not None],
            key=lambda r: r["year"]
        )

        if chronological:
            first = chronological[0]
            first_hits_rows.append({
                "keyword": kw,
                "first_year": first["year"],
                "periodico": first["periodico"],
                "numero": first["numero"],
                "hits_semantic": first["hits_semantic"]
            })

    conn.close()

    # ===============================
    # NORMALIZACIÓN + SCORE
    # ===============================
    if hits_rows:
        max_len = max(r["text_length"] for r in hits_rows if r["text_length"] > 0)
        max_hits = max(r["hits_semantic"] for r in hits_rows if r["hits_semantic"] > 0)

        for r in hits_rows:
            norm_len = r["text_length"] / max_len if max_len else 0
            norm_hits = r["hits_semantic"] / max_hits if max_hits else 0

            score = (
                0.4 * norm_len +
                0.4 * norm_hits +
                0.2 * (1 - r["noise_ratio"])
            )

            r["confidence_score"] = round(score, 4)
            r["confidence_pct"] = round(score * 100, 1)
            r["ocr_attention_flag"] = attention_flag(score)
            r["lexical_role"] = lexical_role(r["hits_semantic"])
            r["ocr_action"] = ocr_action(r["hits_semantic"])

    # ===============================
    # EXPORT CSVs
    # ===============================
    fieldnames = [
        "keyword", "year", "periodico", "numero",
        "hits_exact", "hits_semantic",
        "text_length",
        "density_exact", "density_semantic",
        "noise_ratio",
        "confidence_score", "confidence_pct",
        "ocr_attention_flag", "lexical_role", "ocr_action"
    ]

    with open(HITS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(hits_rows)

    with open(SUBCORPUS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(subcorpus_rows)

    with open(FIRST_HITS_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["keyword", "first_year", "periodico", "numero", "hits_semantic"]
        )
        writer.writeheader()
        writer.writerows(first_hits_rows)

    print("✔ Extracción OCRmyPDF con matching semántico completada")

if __name__ == "__main__":
    main()












