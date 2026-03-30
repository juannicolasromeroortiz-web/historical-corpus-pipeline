from pathlib import Path
import shutil
import json

def rm(p):
    if p.exists():
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()

def main():
    print("⚠ RESET TOTAL DEL CORPUS")
    ans = input("¿Seguro? (si/no): ").lower()
    if ans not in ("si", "sí"):
        print("Abortado.")
        return

    rm(Path("metadata"))
    rm(Path("data_normalized"))
    rm(Path("data_final"))
    rm(Path("logs"))

    Path("metadata").mkdir(exist_ok=True)
    Path("data_normalized").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    # reset state
    state = Path("logs/metadata_state.json")
    state.write_text(json.dumps({"last_index": 0}, indent=2), encoding="utf-8")

    print("✔ Corpus reseteado. Listo para primera tanda.\n")

if __name__ == "__main__":
    main()

