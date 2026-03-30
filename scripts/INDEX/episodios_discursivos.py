#!/usr/bin/env python3
import csv
from pathlib import Path
from collections import defaultdict, Counter
import itertools

# ===============================
# PATHS
# ===============================
BASE = Path(__file__).resolve().parents[2]
IN_FILE = BASE / "exports_recovered" / "constelaciones_spacy_por_ano.csv"
OUT_FILE = BASE / "exports_recovered" / "episodios_discursivos.csv"

# ===============================
# CONFIGURACIÓN
# ===============================
MIN_YEARS_CORE = 3       # aparece en al menos N años
MIN_COOC_CORE = 3        # coaparece con al menos N conceptos

MIN_YEARS_SUPPORT = 2
MIN_COOC_SUPPORT = 2

# ===============================
# MAIN
# ===============================
def main():
    data = []

    with open(IN_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["year"] = int(row["year"])
            data.append(row)

    # ===============================
    # ORGANIZAR POR AÑO
    # ===============================
    concepts_by_year = defaultdict(set)

    for r in data:
        concepts_by_year[r["year"]].add(r["concept_candidate"])

    # ===============================
    # MÉTRICAS POR CONCEPTO
    # ===============================
    years_per_concept = defaultdict(set)
    coocurrence_counter = defaultdict(set)

    for year, concepts in concepts_by_year.items():
        for c in concepts:
            years_per_concept[c].add(year)

        for a, b in itertools.combinations(concepts, 2):
            coocurrence_counter[a].add(b)
            coocurrence_counter[b].add(a)

    # ===============================
    # CLASIFICACIÓN DISCURSIVA
    # ===============================
    results = []

    for concept in years_per_concept:
        years_count = len(years_per_concept[concept])
        cooc_count = len(coocurrence_counter.get(concept, []))

        if years_count >= MIN_YEARS_CORE and cooc_count >= MIN_COOC_CORE:
            role = "CORE"
        elif years_count >= MIN_YEARS_SUPPORT and cooc_count >= MIN_COOC_SUPPORT:
            role = "SUPPORT"
        else:
            role = "CONTEXT"

        results.append({
            "concept": concept,
            "years_present": years_count,
            "cooccurring_concepts": cooc_count,
            "discursive_role": role,
            "years_list": ";".join(str(y) for y in sorted(years_per_concept[concept]))
        })

    # ===============================
    # EXPORT
    # ===============================
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "concept",
                "years_present",
                "cooccurring_concepts",
                "discursive_role",
                "years_list"
            ]
        )
        writer.writeheader()
        writer.writerows(
            sorted(
                results,
                key=lambda r: (r["discursive_role"], -r["years_present"]),
                reverse=True
            )
        )

    print("✔ Episodios discursivos detectados")
    print(f"  - {OUT_FILE}")

# ===============================
if __name__ == "__main__":
    main()

