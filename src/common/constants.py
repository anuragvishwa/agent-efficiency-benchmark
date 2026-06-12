from pathlib import Path


DATASET_ID = "yoonholee/terminalbench-trajectories"
TERMINALBENCH_DATASET_ID = DATASET_ID
SWE_AGENT_DATASET_ID = "nebius/SWE-agent-trajectories"
BENCHMARK_VERSION = "0.1.0"
METHODOLOGY_VERSION = "0.1.0"
SOURCE_DATASET = "terminalbench"
SWE_AGENT_SOURCE_DATASET = "swe_agent"

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LABELS_DIR = DATA_DIR / "labels"
REPORTS_DIR = Path("reports")
DOCS_DIR = Path("docs")

RAW_TERMINALBENCH_PATH = RAW_DIR / "terminalbench.parquet"
SOURCE_METADATA_PATH = RAW_DIR / "terminalbench_source.json"
RAW_SWE_AGENT_PATH = RAW_DIR / "swe_agent_trajectories.parquet"
SWE_AGENT_SOURCE_METADATA_PATH = RAW_DIR / "swe_agent_source.json"
RUNS_PATH = PROCESSED_DIR / "runs.parquet"
STEPS_PATH = PROCESSED_DIR / "steps.parquet"
STEP_SIGNALS_PATH = PROCESSED_DIR / "step_signals.parquet"
RUN_SIGNALS_PATH = PROCESSED_DIR / "run_signals.parquet"
RUNS_WITH_RCA_PATH = PROCESSED_DIR / "runs_with_rca.parquet"
BENCHMARK_DB_PATH = PROCESSED_DIR / "benchmark.duckdb"
EARLY_STOP_PATH = PROCESSED_DIR / "early_stop_simulation.parquet"
DATA_QUALITY_PATH = REPORTS_DIR / "data_quality.json"

SWE_AGENT_RUNS_PATH = PROCESSED_DIR / "swe_agent_runs.parquet"
SWE_AGENT_STEPS_PATH = PROCESSED_DIR / "swe_agent_steps.parquet"
SWE_AGENT_STEP_SIGNALS_PATH = PROCESSED_DIR / "swe_agent_step_signals.parquet"
SWE_AGENT_RUN_SIGNALS_PATH = PROCESSED_DIR / "swe_agent_run_signals.parquet"
SWE_AGENT_RUNS_WITH_RCA_PATH = PROCESSED_DIR / "swe_agent_runs_with_rca.parquet"
SWE_AGENT_BENCHMARK_DB_PATH = PROCESSED_DIR / "swe_agent_benchmark.duckdb"
SWE_AGENT_EARLY_STOP_PATH = PROCESSED_DIR / "swe_agent_early_stop_simulation.parquet"
SWE_AGENT_DATA_QUALITY_PATH = REPORTS_DIR / "swe_agent_data_quality.json"
