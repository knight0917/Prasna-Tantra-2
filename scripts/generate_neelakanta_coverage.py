from pathlib import Path
from generate_book_coverage import generate_coverage


ROOT = Path(__file__).resolve().parents[1]
TXT_PATH = ROOT / "Sri_Neelakanta_-_Prasna_Tantra.txt"
OUT_PATH = ROOT / "neelakanta_coverage_matrix.json"


def main():
    payload = generate_coverage(TXT_PATH, OUT_PATH)
    print(f"Wrote: {OUT_PATH}")
    print(f"Detected blocks: {payload['total_blocks_detected']}")
    print(f"Unclassified blocks: {payload['unclassified_blocks']}")


if __name__ == "__main__":
    main()

