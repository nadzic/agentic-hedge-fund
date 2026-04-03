import json
from pathlib import Path

DATASET_PATH = Path(__file__).parents[1] / "datasets" / "nodes" / "nodes_golden_v1.json"


def main() -> None:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    print(f"[nodes] loaded_cases={len(cases)}")
    print("[nodes] runner placeholder: wire node invocation + scoring.")


if __name__ == "__main__":
    main()
