import json
import requests
import time
from pathlib import Path
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print(">>> download_from_metadata (instrumentado) iniciado")

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

# parámetros operacionales
MAX_RETRIES = 3
TIMEOUT = 60
ZERO_BYTE_THRESHOLD = 1024  # Q-log-1 = B

# ===============================
# UTILIDADES
# ===============================

def now_utc():
    return datetime.utcnow().isoformat() + "Z"

def now_local():
    return datetime.now().isoformat()

def log_jsonl(path: Path, obj: dict):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def download_pdf(url, target_path):
    """
    Descarga con retries, backoff suave y timeout.
    Retorna (status, bytes, seconds, attempt, reason)
    """
    start = time.time()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, verify=False, timeout=TIMEOUT)
            r.raise_for_status()
            content = r.content

            # escribir PDF
            target_path.write_bytes(content)
            bytes_len = len(content)

            # verificación de bytes
            if bytes_len < ZERO_BYTE_THRESHOLD:
                reason = "failed_zero_bytes"
                log_jsonl(ERROR_LOG, {
                    "pdf": target_path.name,
                    "reason": reason,
                    "bytes": bytes_len,
                    "attempt": attempt,
                    "utc": now_utc(),
                    "local": now_local()
                })
                # no retornamos success, seguimos en retry
                continue

            # éxito
            sec = time.time() - start
            return ("ok", bytes_len, sec, attempt, None)

        except Exception as e:
            reason = f"failed_network:{repr(e)}"
            log_jsonl(ERROR_LOG, {
                "pdf": target_path.name,
                "reason": reason,
                "attempt": attempt,
                "utc": now_utc(),
                "local": now_local()
            })
            if attempt < MAX_RETRIES:
                time.sleep(1 * attempt)  # backoff suave
                continue
            else:
                sec = time.time() - start
                return ("failed", 0, sec, attempt, reason)

    # si llegamos aquí es fallo
    sec = time.time() - start
    return ("failed", 0, sec, MAX_RETRIES, "unknown")


# ===============================
# PROCESS
# ===============================

def main():
    # cargamos config para fechas
    config_path = Path("logs/corpus_config.json")
    if not config_path.exists():
        print("❌ No existe logs/corpus_config.json, abortando.")
        return

    config = json.loads(config_path.read_text(encoding="utf-8"))
    year_start = int(config["year_start"])
    year_end = int(config["year_end"])

    # cargar metadata ordenada
    metadata_files = sorted(METADATA_DIR.glob("*.json"))

    count_ok = 0
    count_failed = 0
    count_skipped = 0
    count_out_of_range = 0

    bytes_total = 0
    seconds_total = 0.0

    for meta_path in metadata_files:
        with meta_path.open(encoding="utf-8") as f:
            meta = json.load(f)

        status = meta.get("status")
        year = meta.get("year")
        pdf_name = meta.get("pdf_filename")
        url = meta.get("download_url")

        if not pdf_name or not url:
            continue  # metadata incompleta

        # ------------------------
        # aplicar filtro de rango
        # ------------------------
        if year is not None and not (year_start <= int(year) <= year_end):
            meta["status"] = "skipped_out_of_range"
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
            count_out_of_range += 1
            continue

        pdf_path = DATA_DIR / pdf_name

        # ------------------------
        # si ya existía → verificar
        # ------------------------
        if pdf_path.exists():
            size = pdf_path.stat().st_size
            if size >= ZERO_BYTE_THRESHOLD:
                # skip con éxito
                meta["status"] = "downloaded_ok"
                meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
                count_ok += 1
                bytes_total += size
                # log directo
                log_jsonl(DOWNLOAD_LOG, {
                    "pdf": pdf_name,
                    "status": "skip_exists",
                    "bytes": size,
                    "utc": now_utc(),
                    "local": now_local()
                })
                continue
            else:
                # archivo truncado → retry
                pdf_path.unlink(missing_ok=True)

        # ------------------------
        # descargar con retries
        # ------------------------
        dl_status, dl_bytes, dl_sec, dl_attempt, dl_reason = download_pdf(url, pdf_path)

        if dl_status == "ok":
            meta["status"] = "downloaded_ok"
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
            count_ok += 1
            bytes_total += dl_bytes
            seconds_total += dl_sec
            log_jsonl(DOWNLOAD_LOG, {
                "pdf": pdf_name,
                "status": "ok",
                "bytes": dl_bytes,
                "seconds": dl_sec,
                "attempt": dl_attempt,
                "utc": now_utc(),
                "local": now_local()
            })
        else:
            meta["status"] = "failed"
            meta["reason"] = dl_reason
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
            count_failed += 1
            log_jsonl(DOWNLOAD_LOG, {
                "pdf": pdf_name,
                "status": "failed",
                "attempt": dl_attempt,
                "reason": dl_reason,
                "utc": now_utc(),
                "local": now_local()
            })

    # ===========================
    # summary batch
    # ===========================
    summary = {
        "count_ok": count_ok,
        "count_failed": count_failed,
        "count_out_of_range": count_out_of_range,
        "bytes_total": bytes_total,
        "avg_seconds": (seconds_total / count_ok) if count_ok > 0 else None,
        "generated_utc": now_utc(),
        "generated_local": now_local()
    }
    SUMMARY_LOG.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== RESUMEN DESCARGA (instrumentado) ===")
    print(f"✔ OK:           {count_ok}")
    print(f"❌ failed:       {count_failed}")
    print(f"↷ out_of_range: {count_out_of_range}")
    print(f"📦 bytes_total: {bytes_total}")
    if summary["avg_seconds"] is not None:
        print(f"⏱ avg_seconds: {summary['avg_seconds']:.3f}")
    print(f"\n→ logs en: {LOG_DIR}")
    print("✔ done.")


if __name__ == "__main__":
    main()









