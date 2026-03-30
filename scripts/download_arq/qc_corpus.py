import json
from pathlib import Path
import re
from collections import defaultdict

URLS = Path("scripts/download_arq/periodicos_unicos_segunda_fase.txt")
STATE = Path("logs/metadata_state.json")
METADATA = Path("metadata")
DATA = Path("data_normalized")
ERROR_LOG = Path("logs/metadata_errors.log")

QC_JSON = Path("logs/qc_report.json")
QC_TXT = Path("logs/qc_report.txt")
MANUAL = Path("logs/manual_download_urls.txt")


def parse_errors():
    if not ERROR_LOG.exists():
        return []

    out = []
    for line in ERROR_LOG.read_text(encoding="utf-8").splitlines():
        try:
            ts, url, reason = line.split(" | ", 2)
            out.append((url, reason))
        except:
            pass
    return out


def main():
    urls = [u.strip() for u in URLS.read_text().splitlines() if u.strip()]
    state = json.loads(STATE.read_text()) if STATE.exists() else {"last_index": 0}
    processed = urls[:state["last_index"]]

    # PDFs
    pdfs = {p.name for p in DATA.glob("*.pdf")}

    # metadata
    metas = list(METADATA.glob("*.json"))
    by_pdf = {}
    by_url = defaultdict(int)
    status_count = defaultdict(int)

    urls_with_metadata = set()

    for m in metas:
        meta = json.loads(m.read_text(encoding="utf-8"))
        status_count[meta.get("status", "unknown")] += 1
        fn = meta.get("pdf_filename")
        if fn:
            by_pdf[fn] = meta
        su = meta.get("source_url")
        if su:
            urls_with_metadata.add(su)

    # faltantes
    metadata_without_pdf = [
        fn for fn, meta in by_pdf.items()
        if fn not in pdfs
    ]

    pdf_without_metadata = [
        p for p in pdfs if p not in by_pdf
    ]

    # urls sin metadata
    urls_sin_metadata = [u for u in processed if u not in urls_with_metadata]

    # errores
    errors = parse_errors()
    errors_by_reason = defaultdict(list)
    for u, r in errors:
        errors_by_reason[r].append(u)

    # MANUAL ACTION (C)
    manual_urls = set(u for u, _ in errors) | set(urls_sin_metadata)

    QC_JSON.write_text(json.dumps({
        "urls_total": len(urls),
        "urls_procesados": len(processed),
        "metadata_json": len(metas),
        "pdfs": len(pdfs),
        "faltantes_pdf": len(metadata_without_pdf),
        "pdf_sin_metadata": len(pdf_without_metadata),
        "urls_sin_metadata": len(urls_sin_metadata),
        "status_metadata": dict(status_count),
        "errores": dict(errors_by_reason),
        "manual_action": sorted(manual_urls),
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    QC_TXT.write_text(
        "=== QC CORPUS ===\n\n"
        f"urls procesados: {len(processed)} / {len(urls)}\n"
        f"metadata_json: {len(metas)}\n"
        f"pdfs: {len(pdfs)}\n"
        f"faltantes_pdf: {len(metadata_without_pdf)}\n"
        f"urls_sin_metadata: {len(urls_sin_metadata)}\n\n"
        "=== Manual Action ===\n" +
        "\n".join(sorted(manual_urls)),
        encoding="utf-8"
    )

    MANUAL.write_text("\n".join(sorted(manual_urls)), encoding="utf-8")

    print("✔ QC listo")
    print(f"→ {QC_JSON}")
    print(f"→ {QC_TXT}")
    print(f"→ {MANUAL}")


if __name__ == "__main__":
    main()




