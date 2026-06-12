from __future__ import annotations

import json

from src.common.constants import REPORTS_DIR
from src.common.datasets import DATASETS
from src.reports.schemas import PublicBenchmark


REQUIRED_REPORTS = [
    "manifest.json",
    "public_benchmark.json",
    "overview.json",
    "leaderboard_agent_model.csv",
    "leaderboard_agent.csv",
    "leaderboard_model_uncontrolled.csv",
    "outcome_comparison.csv",
    "task_difficulty.csv",
    "failure_patterns.csv",
    "early_stop_simulation.csv",
    "data_quality.json",
    "examples/selected_trajectories.json",
]

SWE_REQUIRED_REPORTS = [
    "swe_agent_overview.json",
    "swe_agent_model_leaderboard.csv",
    "swe_agent_outcome_comparison.csv",
    "swe_agent_failure_patterns.csv",
    "swe_agent_early_stop_simulation.csv",
    "swe_agent_public_benchmark.json",
]


def main() -> None:
    required = list(REQUIRED_REPORTS)
    if DATASETS["swe_agent"].benchmark_db_path.exists():
        required.extend(SWE_REQUIRED_REPORTS)
    missing = [name for name in required if not (REPORTS_DIR / name).exists()]
    if missing:
        print("Missing reports:")
        for name in missing:
            print(f"- {name}")
        raise SystemExit(1)

    payload = json.loads((REPORTS_DIR / "public_benchmark.json").read_text())
    PublicBenchmark.model_validate(payload)
    if DATASETS["swe_agent"].benchmark_db_path.exists():
        swe_payload = json.loads(
            (REPORTS_DIR / "swe_agent_public_benchmark.json").read_text()
        )
        PublicBenchmark.model_validate(swe_payload)
        if "datasets" not in payload:
            print("public_benchmark.json missing datasets array")
            raise SystemExit(1)
    print("Report validation passed")
    print(f"Reports directory: {REPORTS_DIR}")


if __name__ == "__main__":
    main()
