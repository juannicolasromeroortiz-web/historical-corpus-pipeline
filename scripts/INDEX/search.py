#!/usr/bin/env python3
import sqlite3, sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DB = BASE / "db" / "documents.db"

q = sys.argv[1]

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

sql = """
SELECT d.year, d.periodico, d.numero, d.ruta_pdf
FROM docs_fts f
JOIN docs d ON f.rowid=d.rowid
WHERE docs_fts MATCH ?
ORDER BY d.year ASC;
"""

for row in conn.execute(sql,(q,)):
    print(row["year"], row["periodico"], row["numero"])


