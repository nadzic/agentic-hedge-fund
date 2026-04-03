import json
from pathlib import Path

DATASET_PATH = Path(__file__).parents[1] / "datasets" / "graph" / "graph_golden_v1.json"


def main() -> None:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    print(f"[graph] loaded_cases={len(cases)}")
    print("[graph] runner placeholder: wire route tracing + path assertions.")


if __name__ == "__main__":
    main()
