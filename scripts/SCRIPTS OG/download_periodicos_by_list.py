import requests
import re
import json
from pathlib import Path
import urllib3
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================
# CONFIGURACIÓN
# =========================

PERIODICOS_LIST_FILE = "scripts/periodicos_unicos.txt"
METADATA_DIR = Path("metadata")

STATE_FILE = Path("logs/metadata_state.json")
MAX_PERIODICOS_POR_TANDA = 5

BASE_URL = "https://babel.banrepcultural.org"

METADATA_DIR.mkdir(exist_ok=True)

# =========================
# UTILIDADES
# =========================

def load_state():
    if not STATE_FILE.exists():
        return {"last_index": 0}
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_state(index):
    STATE_FILE.parent.mkdir(exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_index": index}, f, indent=2)


def load_periodicos_from_txt(path):
    with open(path, encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]


def extract_initial_state(html):
    match = re.search(
        r'window\.__INITIAL_STATE__\s*=\s*JSON\.parse\("(.+?)"\)',
        html,
        re.DOTALL
    )
    if not match:
        raise RuntimeError("No se encontró window.__INITIAL_STATE__")

    raw = match.group(1)
    decoded = json.loads(f'"{raw}"')
    return json.loads(decoded)


def normalize_name(text):
    text = text.upper()
    text = re.sub(r"[ÁÀ]", "A", text)
    text = re.sub(r"[ÉÈ]", "E", text)
    text = re.sub(r"[ÍÌ]", "I", text)
    text = re.sub(r"[ÓÒ]", "O", text)
    text = re.sub(r"[ÚÙ]", "U", text)
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text


def extract_year(text):
    if not text:
        return None
    m = re.search(r"\b(18\d{2})\b", text)
    return m.group(1) if m else None


def extract_descripcion_material(child):
    """
    Extrae la descripción de material (donde suele aparecer la fecha real)
    """
    for f in child.get("fields", []):
        if f.get("key") in {"descri", "description", "material"}:
            return f.get("value")
    return None

# =========================
# PROCESO METADATA
# =========================

def process_periodico(url):
    print(f"\nProcesando: {url}")

    r = requests.get(url, verify=False, timeout=60)
    r.raise_for_status()

    state = extract_initial_state(r.text)
    item = state["item"]["item"]
    parent = item["parent"]

    titulo_periodico = parent["fields"][0]["value"]
    collection_alias = item["collectionAlias"]

    # --- Descripción del objeto ---
    descripcion_objeto = None
    for f in parent.get("fields", []):
        if f.get("key") == "descri":
            descripcion_objeto = f.get("value")
            break

    children = parent.get("children", [])

    for child in children:
        child_id = child.get("id")
        child_title = child.get("title")

        descripcion_material = extract_descripcion_material(child)
        year = extract_year(descripcion_material)

        normalized = normalize_name(titulo_periodico)
        json_path = METADATA_DIR / f"{normalized}_{child_id}.json"

        if json_path.exists():
            continue

        pdf_url = (
            f"{BASE_URL}/digital/api/collection/"
            f"{collection_alias}/id/{child_id}/download"
        )

        metadata = {
            "periodico": titulo_periodico,
            "descripcion_objeto": descripcion_objeto,
            "collection": collection_alias,
            "source_url": url,

            "child_id": child_id,
            "titulo_numero": child_title,
            "descripcion_material": descripcion_material,
            "date_raw": descripcion_material,
            "year": year,

            "download_url": pdf_url,
            "status": "pending",

            "pdf_filename": f"{normalized}_{child_id}.pdf",
            "created_by": "download_periodicos_by_list.py",
            "created_at": datetime.utcnow().isoformat()
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        print(f"  ✔ Metadata creada: {json_path.name}")

# =========================
# MAIN
# =========================

def main():
    urls = load_periodicos_from_txt(PERIODICOS_LIST_FILE)
    state = load_state()

    start = state["last_index"]
    end = min(start + MAX_PERIODICOS_POR_TANDA, len(urls))

    print(f"Procesando periódicos {start} → {end - 1} (total {len(urls)})")

    for i in range(start, end):
        process_periodico(urls[i])
        save_state(i + 1)

    print("\n✔ Tanda completada. Metadata completa generada (sin descargas).")


if __name__ == "__main__":
    main()




