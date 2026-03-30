#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
extract_excel_fields.py

Tabla base historiográfica (1 fila = 1 PDF / número) con palabras clave asistidas.
"""

import json
from pathlib import Path
import pandas as pd
from collections import Counter

# =========================
# RUTAS
# =========================

BASE_DIR = Path("/home/juan_romero/projects/ocr_project")

EXPORTS_DIR = BASE_DIR / "exports_recovered"
METADATA_DIR = BASE_DIR / "recovery_pipeline" / "metadata_recovered_enriched"
DATA_FINAL_DIR = BASE_DIR / "organized_final"

OUTPUT_EXCEL = EXPORTS_DIR / "tabla_base_investigacion.xlsx"

# =========================
# UTILIDADES
# =========================

def placeholder():
    return "ND"

def extract_id_from_numero(numero: str) -> str | None:
    parts = numero.split("_")
    if parts and parts[-1].isdigit():
        return parts[-1]
    return None

def load_metadata(numero: str) -> dict:
    numero_id = extract_id_from_numero(numero)
    if not numero_id:
        return {}

    for metadata_file in METADATA_DIR.glob(f"*_{numero_id}.json"):
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    return {}

def find_ocr_path(periodico: str, numero: str) -> Path | None:
    ocr_path = DATA_FINAL_DIR / periodico / numero / "input" / "ocr.txt"
    return ocr_path if ocr_path.exists() else None

# =========================
# CARGA CSV
# =========================

print("📥 Cargando CSV de exports...")

df_hits = pd.read_csv(EXPORTS_DIR / "keyword_hits_exact.csv")
df_subcorpus = pd.read_csv(EXPORTS_DIR / "keyword_subcorpus_top.csv")
df_snippets = pd.read_csv(EXPORTS_DIR / "snippets_top.csv")
df_episodios = pd.read_csv(EXPORTS_DIR / "episodios_discursivos.csv")

# =========================
# CONSTRUCCIÓN BASE DE DOCUMENTOS
# =========================

base_docs = (
    df_hits[["periodico", "numero", "year"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

print(f"📄 Documentos únicos detectados: {len(base_docs)}")

rows = []

# =========================
# ITERACIÓN PRINCIPAL
# =========================

for _, row in base_docs.iterrows():
    periodico = row["periodico"]
    numero = row["numero"]
    year = row["year"]

    # --- Metadata ---
    metadata = load_metadata(numero)

    # --- OCR ---
    ocr_path = find_ocr_path(periodico, numero)
    ocr_disponible = "Sí" if ocr_path else "No"

    # --- Keywords y snippets ---
    hits_doc = df_hits[df_hits["numero"] == numero]
    subcorpus_doc = df_subcorpus[df_subcorpus["numero"] == numero]
    snippets_doc = df_snippets[
        (df_snippets["numero"] == numero) & (df_snippets["periodico"] == periodico)
    ]

    # Palabras clave asistidas: tomar top 3 keywords por aparición en snippets
    if not snippets_doc.empty:
        counter = Counter(snippets_doc["keyword"].tolist())
        top_keywords = [kw for kw, _ in counter.most_common(3)]
    else:
        top_keywords = []

    # Completar hasta 3 con placeholder si hace falta
    while len(top_keywords) < 3:
        top_keywords.append(placeholder())

    # --- Contexto discursivo ---
    episodios_relacionados = []
    for _, ep in df_episodios.iterrows():
        years_list = str(ep.get("years_list", ""))
        if str(year) in years_list:
            episodios_relacionados.append(ep["concept"])
    episodios_relacionados = sorted(set(episodios_relacionados))

    # --- Fila final ---
    rows.append({
        "Título de la publicación seriada": periodico,
        "Año": year,
        "Vol.": placeholder(),
        "Núm.": numero,
        "Mes": placeholder(),
        "Página inicial del artículo": placeholder(),
        "Página final del artículo": placeholder(),
        "Autor principal": placeholder(),
        "Título del artículo": placeholder(),
        "Resumen": placeholder(),
        "Citas clave": placeholder(),
        "Palabras clave I": top_keywords[0],
        "Palabras clave II": top_keywords[1],
        "Palabras clave III": top_keywords[2],
        "Descripción de la publicación": metadata.get("descripcion_objeto", placeholder()),
        "Fuente digital": metadata.get("download_url", placeholder()),
        "OCR disponible": ocr_disponible,
        "Episodios discursivos relacionados": ", ".join(episodios_relacionados) if episodios_relacionados else placeholder()
    })

# =========================
# EXPORTACIÓN
# =========================

df_final = pd.DataFrame(rows)
df_final.sort_values(by=["Año", "Título de la publicación seriada", "Núm."], inplace=True)

df_final.to_excel(OUTPUT_EXCEL, index=False)

print("✅ Tabla base con palabras clave asistidas generada correctamente:")
print(OUTPUT_EXCEL)







