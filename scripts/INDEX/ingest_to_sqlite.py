#!/usr/bin/env python3
import sqlite3, json
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
ROOT = BASE / "data_final"
METADATA = BASE / "metadata"
DB = BASE / "db" / "documentsfase2.db"

DB.parent.mkdir(exist_ok=True)

def ensure_schema(conn):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS docs (
        id TEXT PRIMARY KEY,
        periodico TEXT,
        numero TEXT,
        year INTEGER,
        titulo TEXT,
        child_id TEXT,
        ruta_pdf TEXT,
        ruta_txt TEXT
    );
    """)
    conn.execute("""
    CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
        id,
        texto,
        content='docs',
        content_rowid='rowid'
    );
    """)

def main():
    conn = sqlite3.connect(DB)
    ensure_schema(conn)

    for periodico in ROOT.iterdir():
        if not periodico.is_dir():
            continue
        for numero in periodico.iterdir():
            txt = numero / "input" / "ocr.txt"
            if not txt.exists():
                continue

            pdfs = list((numero/"input").glob("*.pdf"))
            if not pdfs:
                continue
            pdf = pdfs[0]
            pdf_stem = pdf.stem

            # localizar JSON
            json_path = METADATA / f"{pdf_stem}.json"
            if not json_path.exists():
                # fallback via child_id
                cid = pdf_stem.split("_")[-1]
                cand = list(METADATA.glob(f"*{cid}.json"))
                if not cand:
                    continue
                json_path = cand[0]

            meta = json.loads(json_path.read_text(encoding="utf-8"))
            year = meta.get("year")
            try: year = int(year) if year else None
            except: year = None

            child_id = str(meta.get("child_id") or pdf_stem)
            titulo = meta.get("titulo_numero","")
            doc_id = child_id

            conn.execute("""
                INSERT OR REPLACE INTO docs
                (id, periodico, numero, year, titulo, child_id, ruta_pdf, ruta_txt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (doc_id, periodico.name, numero.name, year, titulo, child_id, str(pdf), str(txt)))

            texto = txt.read_text(encoding="utf-8", errors="ignore")
            conn.execute("""
                INSERT OR REPLACE INTO docs_fts(rowid, id, texto)
                SELECT rowid, id, ? FROM docs WHERE id=?
            """, (texto, doc_id))

            conn.commit()

    conn.close()
    print("✔ ingest completo")

if __name__ == "__main__":
    main()


