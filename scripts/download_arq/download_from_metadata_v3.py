#!/usr/bin/env python3
import json
import requests
import time
from pathlib import Path
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===============================
# CONFIG
# ===============================

METADATA_DIR = Path("metadata")
DATA_DIR = Path("data_normalized")
DATA_DIR.mkdir(exist_ok=True)

LOG_DIR = Path("logs/download")
LOG_DIR.mkdir(parents=True, exist_ok=True)

DOWNLOAD_LOG = LOG_DIR / "download.jsonl"
ERROR_LOG = LOG_DIR / "errors.jsonl"
SUMMARY_LOG = LOG_DIR / "summary.json"

MAX_RETRIES = 3
TIMEOUT = 60
ZERO_BYTE_THRESHOLD = 1024   # min bytes to consider valid

# ===============================
# UTILIDADES
# ===============================

def now_utc():
    return datetime.utcnow().isoformat() + "Z"

def now_local():
    return datetime.now().isoformat()

def log_jsonl(path, obj):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def download_pdf(url, pdf_path):
    """
    Retorna: (status, bytes, seconds, attempt, reason)
    """
    start = time.time()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, timeout=TIMEOUT, verify=False)
            r.raise_for_status()
            content = r.content

            pdf_path.write_bytes(content)
            size = len(content)

            if size < ZERO_BYTE_THRESHOLD:
                log_jsonl(ERROR_LOG, {
                    "pdf": pdf_path.name,
                    "reason": "zero_bytes",
                    "bytes": size,
                    "attempt": attempt,
                    "utc": now_utc(),
                    "local": now_local()
                })
                continue

            sec = time.time() - start
            return ("ok", size, sec, attempt, None)

        except Exception as e:
            reason = f"network:{repr(e)}"
            log_jsonl(ERROR_LOG, {
                "pdf": pdf_path.name,
                "reason": reason,
                "attempt": attempt,
                "utc": now_utc(),
                "local": now_local()
            })

            if attempt < MAX_RETRIES:
                time.sleep(attempt * 1)
                continue
            sec = time.time() - start
            return ("failed", 0, sec, attempt, reason)

    sec = time.time() - start
    return ("failed", 0, sec, MAX_RETRIES, "unknown")

# ===============================
# PROCESS
# ===============================

def main():
    config_path = Path("logs/corpus_config.json")
    if not config_path.exists():
        print("❌ No existe logs/corpus_config.json (ejecuta pipeline primero)")
        return

    config = json.loads(config_path.read_text(encoding="utf-8"))
    year_start = int(config["year_start"])
    year_end = int(config["year_end"])

    metadata_files = sorted(METADATA_DIR.glob("*.json"))

    count_ok = 0
    count_failed = 0
    count_out = 0
    count_none_year = 0

    total_bytes = 0
    total_sec = 0.0

    for idx, meta_path in enumerate(metadata_files, start=1):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        pdf_name = meta.get("pdf_filename")
        url = meta.get("download_url")
        year = meta.get("year")

        if not pdf_name or not url:
            continue

        print(f"[{idx}/{len(metadata_files)}] → {pdf_name}", end=" ")

        # ===== FILTRO DE RANGO =====
        if year is not None:
            if not (year_start <= year <= year_end):
                meta["status"] = "skipped_out_of_range"
                meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
                count_out += 1
                print(f"↷ out_range ({year})")
                continue
        else:
            # no detectable → lo marcamos y NO lo descargamos
            meta["status"] = "skipped_no_year"
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
            count_none_year += 1
            print(f"↷ no_year")
            continue

        pdf_path = DATA_DIR / pdf_name

        # ===== YA EXISTÍA =====
        if pdf_path.exists():
            size = pdf_path.stat().st_size
            if size >= ZERO_BYTE_THRESHOLD:
                meta["status"] = "downloaded_ok"
                meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
                count_ok += 1
                total_bytes += size
                print("✓ exists")
                continue
            else:
                pdf_path.unlink(missing_ok=True)

        # ===== DESCARGA =====
        status, bytes_len, sec, attempt, reason = download_pdf(url, pdf_path)

        if status == "ok":
            meta["status"] = "downloaded_ok"
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
            count_ok += 1
            total_bytes += bytes_len
            total_sec += sec
            print(f"✓ ok ({bytes_len}B {sec:.2f}s)")
        else:
            meta["status"] = "failed"
            meta["reason"] = reason
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
            count_failed += 1
            print(f"❌ failed ({attempt}x)")

    # ===== SUMMARY =====
    summary = {
        "ok": count_ok,
        "failed": count_failed,
        "out_of_range": count_out,
        "no_year": count_none_year,
        "bytes_total": total_bytes,
        "avg_sec": (total_sec/count_ok if count_ok else None),
        "utc": now_utc(),
        "local": now_local()
    }
    SUMMARY_LOG.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== SUMMARY ===")
    print(f"✔ ok           : {count_ok}")
    print(f"❌ failed       : {count_failed}")
    print(f"↷ out_of_range : {count_out}")
    print(f"↷ no_year      : {count_none_year}")
    print(f"📦 bytes_total : {total_bytes}")
    if summary["avg_sec"]:
        print(f"⏱ avg_sec      : {summary['avg_sec']:.2f}")
    print(f"→ logs          : {LOG_DIR}")
    print("done.")
    
if __name__ == "__main__":
    main()










