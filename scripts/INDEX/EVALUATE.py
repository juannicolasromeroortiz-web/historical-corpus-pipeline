import re
import json
import pandas as pd
from pathlib import Path

# =====================
# CONFIGURACIÓN
# =====================
V5_BASE = Path("/home/juan_romero/projects/ocr_project/subcorpus_fase3_v5_8_3")
OCRMYPDF_CSV = Path("/home/juan_romero/projects/ocr_project/exports/keyword_hits_exact.csv")
OUTPUT_CSV = Path("/home/juan_romero/projects/ocr_project/exports/comparativa_v5_vs_baseline.csv")

# =====================
# FUNCIONES
# =====================
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
        ],
        "joven": [r"joven", r"jóven"],
        "juventud": [r"juventud", r"juuentud", r"juventvd"],
        "colegio": [r"colegio", r"colejio"],
        "colejio": [r"colejio", r"colegio"],
        "universidad": [r"universidad", r"vniuersidad", r"uniuersidad"],
    }

    patterns = variants.get(keyword, [re.escape(keyword)])
    combined = "|".join(patterns)
    return re.compile(rf"\b({combined})\b", re.IGNORECASE)


def count_semantic(keyword: str, text: str) -> int:
    return len(build_semantic_pattern(keyword).findall(text))


def read_v5_metrics(pdf_dir: Path):
    metrics_path = pdf_dir / "metrics_summary.json"
    merged_path = pdf_dir / "merged.txt"

    if not metrics_path.exists() or not merged_path.exists():
        return None

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    text = normalize(merged_path.read_text(encoding="utf-8"))

    return {
        "mean_conf_pdf": metrics.get("mean_conf_pdf", 0.0),
        "pages_total": metrics.get("pages_total", 0),
        "pages_bad": metrics.get("pages_bad", 0),
        "mean_garbage_ratio": metrics.get("mean_garbage_ratio", 0.0),
        "hits_total_v5": metrics.get("hits_total", 0),
        "text_length": len(text),
        "merged_text": text
    }

# =====================
# MAIN
# =====================
def main():
    df_baseline = pd.read_csv(OCRMYPDF_CSV)
    rows = []

    for keyword_dir in V5_BASE.iterdir():
        if not keyword_dir.is_dir():
            continue

        kw = keyword_dir.name.lower()

        for numero_dir in keyword_dir.iterdir():
            if not numero_dir.is_dir():
                continue

            pdf_name = numero_dir.name
            v5 = read_v5_metrics(numero_dir)
            if v5 is None:
                continue

            text = v5.pop("merged_text")

            hits_v5_exact = count_exact(kw, text)
            hits_v5_semantic = count_semantic(kw, text)

            density_v5_semantic = (
                hits_v5_semantic / v5["text_length"]
                if v5["text_length"] else 0
            )

            bad_page_ratio = (
                v5["pages_bad"] / v5["pages_total"]
                if v5["pages_total"] else 0
            )

            df_base = df_baseline[
                (df_baseline["keyword"] == kw) &
                (df_baseline["numero"].astype(str) == pdf_name)
            ]

            if not df_base.empty:
                hits_base = int(df_base["hits_semantic"].sum())
                density_base = float(df_base["density_semantic"].mean())
                conf_base = float(df_base["confidence_score"].mean())
            else:
                hits_base = density_base = conf_base = 0

            rows.append({
                "keyword": kw,
                "pdf_name": pdf_name,

                "hits_v5_exact": hits_v5_exact,
                "hits_v5_semantic": hits_v5_semantic,
                "hits_total_v5": v5["hits_total_v5"],
                "density_v5_semantic": density_v5_semantic,
                "mean_conf_v5": v5["mean_conf_pdf"],
                "pages_total_v5": v5["pages_total"],
                "pages_bad_v5": v5["pages_bad"],
                "bad_page_ratio_v5": bad_page_ratio,
                "mean_garbage_ratio_v5": v5["mean_garbage_ratio"],

                "hits_ocrmyPDF_semantic": hits_base,
                "density_ocrmyPDF_semantic": density_base,
                "conf_ocrmyPDF": conf_base
            })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")
    print(f"[OK] Comparativa guardada en: {OUTPUT_CSV}")

if __name__ == "__main__":
    main()


