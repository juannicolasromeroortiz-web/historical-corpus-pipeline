#!/usr/bin/env python3
import csv
from collections import defaultdict
from pathlib import Path

# ===============================
# PATHS
# ===============================
BASE = Path(__file__).resolve().parents[2]
INPUT = BASE / "exports_recovered" / "keyword_hits_exact.csv"
OUTPUT = BASE / "exports_recovered" / "keyword_timeline.csv"

# ===============================
# MAIN
# ===============================
def main():
    timeline = defaultdict(lambda: {
        "docs_with_term": 0,
        "total_hits": 0,
        "central_docs": 0,
        "secondary_docs": 0,
        "mention_docs": 0,
        "reprocess_priority_docs": 0
    })

    with open(INPUT, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = row["year"]
            if not year:
                continue

            hits = int(row["hits_exact"])
            role = row["lexical_role"]
            ocr_action = row["ocr_action"]

            timeline[year]["docs_with_term"] += 1
            timeline[year]["total_hits"] += hits

            if role == "CENTRAL":
                timeline[year]["central_docs"] += 1
            elif role == "SECONDARY":
                timeline[year]["secondary_docs"] += 1
            elif role == "MENTION":
                timeline[year]["mention_docs"] += 1

            if ocr_action == "REPROCESS_PRIORITY":
                timeline[year]["reprocess_priority_docs"] += 1

    # ===============================
    # EXPORT
    # ===============================
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "year",
            "docs_with_term",
            "total_hits",
            "avg_hits_per_doc",
            "central_docs",
            "secondary_docs",
            "mention_docs",
            "reprocess_priority_docs"
        ])

        for year in sorted(timeline.keys()):
            data = timeline[year]
            avg_hits = (
                data["total_hits"] / data["docs_with_term"]
                if data["docs_with_term"] > 0 else 0
            )

            writer.writerow([
                year,
                data["docs_with_term"],
                data["total_hits"],
                round(avg_hits, 2),
                data["central_docs"],
                data["secondary_docs"],
                data["mention_docs"],
                data["reprocess_priority_docs"]
            ])

    print("✔ Timeline temática generada")
    print(f"→ {OUTPUT}")

# ===============================
if __name__ == "__main__":
    main()

