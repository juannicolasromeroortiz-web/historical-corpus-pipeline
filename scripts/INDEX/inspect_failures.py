import json
from pathlib import Path
from collections import defaultdict

ERROR_LOG = Path("logs/metadata_errors.log")

def main():
    if not ERROR_LOG.exists():
        print("no error log")
        return

    bucket = defaultdict(list)

    for line in ERROR_LOG.read_text(encoding="utf-8").splitlines():
        try:
            _, u, r = line.split(" | ", 2)
            bucket[r].append(u)
        except:
            pass

    for reason, urls in bucket.items():
        print(f"\n### {reason} ({len(urls)})")
        for u in urls:
            print(" -", u)

if __name__ == "__main__":
    main()


