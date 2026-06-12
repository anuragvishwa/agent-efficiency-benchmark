from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.common.constants import (
    BENCHMARK_DB_PATH,
    DATA_QUALITY_PATH,
    DATASET_ID,
    EARLY_STOP_PATH,
    RAW_SWE_AGENT_PATH,
    RAW_TERMINALBENCH_PATH,
    RUN_SIGNALS_PATH,
    RUNS_PATH,
    RUNS_WITH_RCA_PATH,
    SOURCE_METADATA_PATH,
    STEP_SIGNALS_PATH,
    STEPS_PATH,
    SWE_AGENT_BENCHMARK_DB_PATH,
    SWE_AGENT_DATA_QUALITY_PATH,
    SWE_AGENT_DATASET_ID,
    SWE_AGENT_EARLY_STOP_PATH,
    SWE_AGENT_RUN_SIGNALS_PATH,
    SWE_AGENT_RUNS_PATH,
    SWE_AGENT_RUNS_WITH_RCA_PATH,
    SWE_AGENT_SOURCE_METADATA_PATH,
    SWE_AGENT_STEP_SIGNALS_PATH,
    SWE_AGENT_STEPS_PATH,
)


@dataclass(frozen=True)
class DatasetPaths:
    key: str
    label: str
    dataset_id: str
    source_dataset: str
    raw_path: Path
    source_metadata_path: Path
    runs_path: Path
    steps_path: Path
    step_signals_path: Path
    run_signals_path: Path
    runs_with_rca_path: Path
    benchmark_db_path: Path
    early_stop_path: Path
    data_quality_path: Path
    docs_profile_name: str
    report_prefix: str


DATASETS = {
    "terminalbench": DatasetPaths(
        key="terminalbench",
        label="Terminal-Bench",
        dataset_id=DATASET_ID,
        source_dataset="terminalbench",
        raw_path=RAW_TERMINALBENCH_PATH,
        source_metadata_path=SOURCE_METADATA_PATH,
        runs_path=RUNS_PATH,
        steps_path=STEPS_PATH,
        step_signals_path=STEP_SIGNALS_PATH,
        run_signals_path=RUN_SIGNALS_PATH,
        runs_with_rca_path=RUNS_WITH_RCA_PATH,
        benchmark_db_path=BENCHMARK_DB_PATH,
        early_stop_path=EARLY_STOP_PATH,
        data_quality_path=DATA_QUALITY_PATH,
        docs_profile_name="DATA_PROFILE.md",
        report_prefix="",
    ),
    "swe_agent": DatasetPaths(
        key="swe_agent",
        label="SWE-agent trajectories",
        dataset_id=SWE_AGENT_DATASET_ID,
        source_dataset="swe_agent",
        raw_path=RAW_SWE_AGENT_PATH,
        source_metadata_path=SWE_AGENT_SOURCE_METADATA_PATH,
        runs_path=SWE_AGENT_RUNS_PATH,
        steps_path=SWE_AGENT_STEPS_PATH,
        step_signals_path=SWE_AGENT_STEP_SIGNALS_PATH,
        run_signals_path=SWE_AGENT_RUN_SIGNALS_PATH,
        runs_with_rca_path=SWE_AGENT_RUNS_WITH_RCA_PATH,
        benchmark_db_path=SWE_AGENT_BENCHMARK_DB_PATH,
        early_stop_path=SWE_AGENT_EARLY_STOP_PATH,
        data_quality_path=SWE_AGENT_DATA_QUALITY_PATH,
        docs_profile_name="SWE_AGENT_DATA_PROFILE.md",
        report_prefix="swe_agent_",
    ),
}


def dataset_paths(key: str = "terminalbench") -> DatasetPaths:
    try:
        return DATASETS[key]
    except KeyError as exc:
        allowed = ", ".join(sorted(DATASETS))
        raise ValueError(f"Unknown dataset {key!r}. Expected one of: {allowed}") from exc
