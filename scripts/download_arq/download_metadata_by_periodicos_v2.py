#!/usr/bin/env python3
import requests
import re
import json
from pathlib import Path
from datetime import datetime
import argparse
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =========================
# CONFIG
# =========================

PERIODICOS_LIST_FILE = Path("scripts/download_arq/periodicos_unicos_segunda_fase.txt")
METADATA_DIR = Path("metadata")
STATE_FILE = Path("logs/metadata_state.json")
ERROR_LOG = Path("logs/metadata_errors.log")

BASE_URL = "https://babel.banrepcultural.org"
MAX_RETRIES = 3

METADATA_DIR.mkdir(exist_ok=True)
ERROR_LOG.parent.mkdir(exist_ok=True)

# =========================
# UTILIDADES
# =========================

def load_state():
    if not STATE_FILE.exists():
        return {"last_index": 0}
    return json.loads(STATE_FILE.read_text(encoding="utf-8"))

def save_state(i):
    STATE_FILE.write_text(json.dumps({"last_index": i}, indent=2, ensure_ascii=False), encoding="utf-8")

def load_urls():
    return [l.strip() for l in PERIODICOS_LIST_FILE.read_text(encoding="utf-8").splitlines() if l.strip()]

def log_error(url, reason):
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.utcnow().isoformat()} | {url} | {reason}\n")

def extract_initial_state(html):
    match = re.search(
        r'window\.__INITIAL_STATE__\s*=\s*JSON\.parse\("(.+?)"\)',
        html,
        re.DOTALL
    )
    if not match:
        raise RuntimeError("no_initial_state")
    raw = match.group(1)
    decoded = json.loads(f'"{raw}"')
    return json.loads(decoded)

def normalize(text):
    text = text.upper()
    text = re.sub(r"[ÁÀ]", "A", text)
    text = re.sub(r"[ÉÈ]", "E", text)
    text = re.sub(r"[ÍÌ]", "I", text)
    text = re.sub(r"[ÓÒ]", "O", text)
    text = re.sub(r"[ÚÙ]", "U", text)
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text

def extract_year(text):
    m = re.search(r"\b(18\d{2})\b", text or "")
    return int(m.group(1)) if m else None

# =========================
# PROCESS
# =========================

RETRYABLE = {"request_failed", "initial_state_error", "parent_is_none"}

def process_periodico(url, idx, total):
    print(f"[{idx}/{total}] metadata → {url}")

    try:
        r = requests.get(url, verify=False, timeout=60)
        r.raise_for_status()
    except Exception as e:
        print("   ❌ request_failed")
        log_error(url, f"request_failed:{repr(e)}")
        return

    try:
        state = extract_initial_state(r.text)
        item = state["item"]["item"]
    except Exception as e:
        print("   ❌ initial_state_error")
        log_error(url, f"initial_state_error:{repr(e)}")
        return

    parent = item.get("parent")
    if not parent:
        print("   ❌ parent_is_none")
        log_error(url, "parent_is_none")
        return

    fields = parent.get("fields")
    if not fields or not isinstance(fields, list):
        print("   ❌ parent_fields_invalid")
        log_error(url, "parent_fields_invalid")
        return

    titulo = fields[0].get("value", "SIN_TITULO")
    alias = item.get("collectionAlias")
    if not alias:
        print("   ❌ collection_alias_missing")
        log_error(url, "collection_alias_missing")
        return

    children = parent.get("children", [])
    if not children:
        print("   ❌ no_children")
        log_error(url, "no_children")
        return

    descripcion = None
    for f in fields:
        if f.get("key") == "descri":
            descripcion = f.get("value")
            break

    norm = normalize(titulo)
    new = 0

    for child in children:
        cid = child.get("id")
        title = child.get("title", "")
        year = extract_year(title)  # estricto

        json_path = METADATA_DIR / f"{norm}_{cid}.json"
        if json_path.exists():
            continue

        pdf_url = f"{BASE_URL}/digital/api/collection/{alias}/id/{cid}/download"

        meta = {
            "periodico": titulo,
            "descripcion_objeto": descripcion,
            "collection": alias,
            "source_url": url,
            "child_id": cid,
            "titulo_numero": title,
            "year": year,  # None si no detectable
            "download_url": pdf_url,
            "status": "pending",
            "pdf_filename": f"{norm}_{cid}.pdf",
            "created_at": datetime.utcnow().isoformat()
        }

        json_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        new += 1
        print(f"   → {json_path.name} (year={year if year else 'NONE'})")

    if new == 0:
        print("   (sin nuevos items)")
    else:
        print(f"   ✔ {new} metadata nuevos")

def parse_error_log():
    if not ERROR_LOG.exists():
        return []
    out = []
    for line in ERROR_LOG.read_text(encoding="utf-8").splitlines():
        try:
            _, url, reason = line.split(" | ", 2)
            reason = reason.split(":", 1)[0]
            out.append((url, reason))
        except:
            pass
    return out

def process_with_retry(url, idx, total):
    for attempt in range(1, MAX_RETRIES + 1):
        before = set(parse_error_log())
        process_periodico(url, idx, total)
        after = set(parse_error_log())
        new = after - before

        if not new:
            return

        reasons = {r for (u, r) in new if u == url}
        if not reasons.issubset(RETRYABLE):
            return

        print(f"↻ retry {attempt}/{MAX_RETRIES} → {url}")

    print(f"⛔ agotado retry para {url}")

# =========================
# MAIN
# =========================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=1)
    args = parser.parse_args()

    urls = load_urls()
    state = load_state()

    start = state["last_index"]
    end = min(start + args.batch_size, len(urls))
    total = len(urls)

    for i in range(start, end):
        process_with_retry(urls[i], i + 1, total)
        save_state(i + 1)

    print(f"✔ metadata batch [{end-start}]")

if __name__ == "__main__":
    main()











