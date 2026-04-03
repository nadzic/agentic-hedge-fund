import json
from pathlib import Path

DATASET_PATH = Path(__file__).parents[1] / "datasets" / "e2e" / "e2e_scenarios_v1.json"


def main() -> None:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    print(f"[e2e] loaded_cases={len(cases)}")
    print("[e2e] runner placeholder: wire full graph execution + rubric scoring.")


if __name__ == "__main__":
    main()
