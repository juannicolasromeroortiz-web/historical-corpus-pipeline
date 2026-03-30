import subprocess
import cv2
import numpy as np
import pytesseract
import pandas as pd
from PIL import Image
from pathlib import Path
import json
import time
import logging
from datetime import datetime
import statistics
import unicodedata

def normalize_name(name: str) -> str:
    return (
        unicodedata.normalize("NFKD", name)
        .encode("ascii", "ignore")
        .decode("ascii")
    )

# =====================
# CONFIG
# =====================
SUBCORPUS_ROOT = Path("/home/juan_romero/projects/ocr_project/subcorpus_fase3")
OUT_BASE = Path("/home/juan_romero/projects/ocr_project/subcorpus_fase3_v5_8_3")
PNG_BASE = OUT_BASE / "png"
LOG_DIR = OUT_BASE / "logs"

LANGS = "spa_old+spa+eng"
DPI = 300
PSM_PRIMARY = 3
PSM_FALLBACK = 4

GOOD_CONF = 70
BAD_CONF = 55
MAX_BAD_PAGE_RATIO = 0.25
MAX_GARBAGE_RATIO = 0.45
MIN_DENSITY_THRESHOLD = 1e-5  # --- NUEVO CRITERIO ---
HITS_ZERO_THRESHOLD = 0       # --- NUEVO CRITERIO ---
PREPROCESS_GARBAGE_RATIO = 0.35  # --- NUEVO CRITERIO ---

# =====================
# LOGGING
# =====================
LOG_DIR.mkdir(parents=True, exist_ok=True)
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
logging.basicConfig(
    filename=LOG_DIR / f"v5_8_3_{run_id}.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# =====================
# PDF → PNG
# =====================
def pdf_to_png(pdf, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "mutool", "draw",
        "-r", str(DPI),
        "-o", str(out_dir / "page_%03d.png"),
        str(pdf)
    ]
    subprocess.run(cmd, check=True)

# =====================
# IMAGE ANALYSIS
# =====================
def is_illustrated(gray):
    edges = cv2.Canny(gray, 80, 160)
    return (edges > 0).mean() > 0.08

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    if is_illustrated(gray):
        return cv2.GaussianBlur(gray, (3, 3), 0), "illustrated"
    clahe = cv2.createCLAHE(2.0, (8, 8))
    return clahe.apply(gray), "text"

# =====================
# OCR
# =====================
def ocr_page(img_path, psm):
    img = Image.open(img_path)
    df = pytesseract.image_to_data(
        img,
        lang=LANGS,
        config=f"--psm {psm}",
        output_type=pytesseract.Output.DATAFRAME
    )
    df = df[df.text.notna()]
    df["text"] = df["text"].astype(str)
    return df

# =====================
# OCR LINES EXTRACTION
# =====================
def extract_ocr_lines(df, page_id):
    lines = []
    if df.empty:
        return lines
    grouped = df.groupby(["block_num", "par_num", "line_num"])
    for i, (_, g) in enumerate(grouped, start=1):
        text = " ".join(g.text.tolist()).strip()
        if not text:
            continue
        x0 = int(g.left.min())
        y0 = int(g.top.min())
        x1 = int((g.left + g.width).max())
        y1 = int((g.top + g.height).max())
        lines.append({
            "line_id": f"p{page_id}_l{i}",
            "bbox": [x0, y0, x1, y1],
            "text": text,
            "char_count": len(text)
        })
    return lines

# =====================
# METRICS
# =====================
def compute_metrics(df):
    return {
        "mean_conf": float(df.conf.mean()) if not df.empty else 0.0,
        "median_conf": float(df.conf.median()) if not df.empty else 0.0,
        "std_conf": float(df.conf.std()) if not df.empty else 0.0,
        "num_words": int(len(df)),
        "alpha_ratio": float(
            df.text.str.contains(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]", regex=True).mean()
        ) if not df.empty else 0.0,
        "garbage_ratio": float(
            df.text.str.contains(r"[^A-Za-zÁÉÍÓÚáéíóúñÑ]", regex=True).mean()
        ) if not df.empty else 1.0,
        "density": float(len(df)/max(1, df.shape[0]))  # --- NUEVO CRITERIO (dummy para density) ---
    }

# =====================
# DECISION
# =====================
def decide_pdf(summary):
    bad_ratio = summary["pages_bad"] / summary["pages_total"]
    # --- NUEVO CRITERIO AUTOMÁTICO ---
    if summary["hits_total"] <= HITS_ZERO_THRESHOLD:
        return "REVIEW"
    if summary["mean_conf_pdf"] >= GOOD_CONF and bad_ratio <= MAX_BAD_PAGE_RATIO:
        return "INDEXABLE"
    if summary["mean_conf_pdf"] >= BAD_CONF:
        return "REVIEW"
    return "REJECT"

# =====================
# MAIN
# =====================
def main():
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    start_all = time.time()

    for keyword_dir in SUBCORPUS_ROOT.iterdir():
        if not keyword_dir.is_dir():
            continue
        logging.info(f"Procesando keyword: {keyword_dir.name}")

        for numero_dir in keyword_dir.iterdir():
            input_dir = numero_dir / "input"
            if not input_dir.exists():
                logging.warning(f"No existe carpeta input: {input_dir}")
                continue

            out_dir = OUT_BASE / keyword_dir.name / numero_dir.name
            png_dir = PNG_BASE / keyword_dir.name / numero_dir.name
            out_dir.mkdir(parents=True, exist_ok=True)
            png_dir.mkdir(parents=True, exist_ok=True)

            pdf_files = sorted(input_dir.glob("*.pdf"))
            if not pdf_files:
                logging.warning(f"No hay PDFs en {input_dir}")
                continue

            for pdf in pdf_files:
                pdf_name = normalize_name(pdf.stem)
                logging.info(f"Procesando {pdf_name}")
                pdf_to_png(pdf, png_dir)

                merged_text = []
                metrics_pages = []
                hits_total = 0  # --- NUEVO CRITERIO: contar hits por PDF ---

                for img_path in sorted(png_dir.glob("*.png")):
                    page_id = int(img_path.stem.split("_")[-1])
                    img = cv2.imread(str(img_path))
                    if img is None:
                        logging.error(f"No se pudo leer imagen: {img_path}")
                        continue

                    proc, mode = preprocess(img)
                    # --- NUEVO CRITERIO: preprocesamiento adicional por garbage_ratio alto ---
                    proc_path = img_path.with_suffix(".proc.png")
                    cv2.imwrite(str(proc_path), proc)

                    df = ocr_page(proc_path, PSM_PRIMARY)
                    metrics = compute_metrics(df)

                    retry = False
                    if metrics["mean_conf"] < GOOD_CONF or metrics["garbage_ratio"] > MAX_GARBAGE_RATIO:
                        df = ocr_page(proc_path, PSM_FALLBACK)
                        metrics = compute_metrics(df)
                        retry = True

                    # --- NUEVO CRITERIO: contar hits como palabras > 3 letras (simplificación) ---
                    hits_total += df[df.text.str.len() > 3].shape[0]

                    ocr_lines = extract_ocr_lines(df, page_id)
                    with open(out_dir / f"ocr_lines_page_{page_id:03d}.json", "w", encoding="utf-8") as f:
                        json.dump(ocr_lines, f, indent=2, ensure_ascii=False)

                    merged_text.append(" ".join(df.text.tolist()))
                    metrics.update({"page": img_path.name, "mode": mode, "retry": retry})
                    metrics_pages.append(metrics)

                (out_dir / "merged.txt").write_text("\n\n".join(merged_text), encoding="utf-8")
                with open(out_dir / "metrics_pages.json", "w", encoding="utf-8") as f:
                    json.dump(metrics_pages, f, indent=2, ensure_ascii=False)

                summary = {
                    "pdf_name": pdf_name,
                    "pages_total": len(metrics_pages),
                    "pages_bad": sum(
                        1 for p in metrics_pages
                        if p["mean_conf"] < BAD_CONF or p["garbage_ratio"] > MAX_GARBAGE_RATIO
                    ),
                    "mean_conf_pdf": statistics.mean(p["mean_conf"] for p in metrics_pages),
                    "median_conf_pdf": statistics.median(p["median_conf"] for p in metrics_pages),
                    "mean_garbage_ratio": statistics.mean(p["garbage_ratio"] for p in metrics_pages),
                    "processing_time_sec": round(time.time() - start_all, 2),
                    "hits_total": hits_total  # --- NUEVO CRITERIO ---
                }

                with open(out_dir / "metrics_summary.json", "w", encoding="utf-8") as f:
                    json.dump(summary, f, indent=2, ensure_ascii=False)

                decision = {
                    "pdf_name": pdf_name,
                    "status": decide_pdf(summary),
                    "summary": summary
                }

                with open(out_dir / "decision.json", "w", encoding="utf-8") as f:
                    json.dump(decision, f, indent=2, ensure_ascii=False)

                logging.info(
                    f"{pdf_name} → status={decision['status']} "
                    f"mean_conf={summary['mean_conf_pdf']:.2f} "
                    f"hits_total={hits_total} "
                    f"time={summary['processing_time_sec']}s"
                )

    logging.info(f"Tiempo total: {round(time.time() - start_all, 2)} s")

if __name__ == "__main__":
    main()


