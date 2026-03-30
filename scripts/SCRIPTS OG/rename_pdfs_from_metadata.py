import json
import re
from pathlib import Path

METADATA_DIR = Path("metadata")
DATA_DIR = Path("data_normalized")

MONTHS = {
    "enero": "01", "febrero": "02", "marzo": "03",
    "abril": "04", "mayo": "05", "junio": "06",
    "julio": "07", "agosto": "08", "septiembre": "09",
    "octubre": "10", "noviembre": "11", "diciembre": "12"
}

STOP_WORDS = [
    "periódico", "periodico", "político", "politico",
    "literario", "literatura", "noticioso", "noticias",
    "revista", "oficial", "moral", "mercantil",
    "artístico", "artistico", "filosofía", "filosofia",
    "artes", "instrucción", "instruccion", "bibliografía",
    "bibliografia", "medicina", "variedades"
]

def sanitize(text):
    text = text.upper()
    text = text.replace(",", "")
    text = re.sub(r"[ÁÀ]", "A", text)
    text = re.sub(r"[ÉÈ]", "E", text)
    text = re.sub(r"[ÍÌ]", "I", text)
    text = re.sub(r"[ÓÒ]", "O", text)
    text = re.sub(r"[ÚÙ]", "U", text)
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text


def short_periodico_name(text):
    words = re.split(r"\s+", text)
    name_parts = []

    for w in words:
        clean = re.sub(r"[^\wáéíóúñÁÉÍÓÚÑ]", "", w).lower()
        if clean in STOP_WORDS:
            break
        name_parts.append(w)

    return sanitize(" ".join(name_parts))


def extract_date(text):
    if not text:
        return None

    text_l = text.lower()

    # Fecha completa en español
    m = re.search(
        r"(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{1,2})\s+de\s+(18\d{2})",
        text_l
    )
    if m:
        return f"{m.group(3)}{MONTHS[m.group(1)]}{m.group(2).zfill(2)}"

    # Fecha ISO
    m = re.search(r"(18\d{2})[-_/](\d{2})[-_/](\d{2})", text_l)
    if m:
        return f"{m.group(1)}{m.group(2)}{m.group(3)}"

    return None


def extract_issue_number(text):
    if not text:
        return None

    m = re.search(r"(?:N\.?|Nº|NO\.?)\s*(\d+)", text, re.IGNORECASE)
    if m:
        return m.group(1)

    m = re.search(r"\b(\d{2,5})\b", text)
    if m:
        return m.group(1)

    return None


def main():
    metadata_files = sorted(METADATA_DIR.glob("*.json"))
    renamed = 0
    skipped = 0

    for meta_path in metadata_files:
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)

        if meta.get("status") != "downloaded":
            continue

        old_pdf = DATA_DIR / meta["pdf_filename"]
        if not old_pdf.exists():
            continue

        periodico_short = short_periodico_name(meta["periodico"])
        titulo = meta.get("titulo_numero", "")
        child_id = meta.get("child_id")

        # 1️⃣ Fecha
        date = extract_date(titulo)
        if date:
            new_name = f"{periodico_short}{date}.pdf"
        else:
            # 2️⃣ Número
            issue = extract_issue_number(titulo)
            if issue:
                new_name = f"{periodico_short}{issue}.pdf"
            else:
                # 3️⃣ Fallback final
                new_name = f"{periodico_short}{child_id}.pdf"

        new_pdf = DATA_DIR / new_name

        if new_pdf.exists():
            skipped += 1
            continue

        old_pdf.rename(new_pdf)
        meta["pdf_filename"] = new_name

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        renamed += 1

    print(f"✔ PDFs renombrados: {renamed}")
    print(f"↷ PDFs no renombrados (colisión): {skipped}")


if __name__ == "__main__":
    main()




