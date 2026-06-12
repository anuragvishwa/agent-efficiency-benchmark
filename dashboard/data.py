from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb
import polars as pl
import streamlit as st


DB_PATH = Path("data/processed/benchmark.duckdb")
SWE_DB_PATH = Path("data/processed/swe_agent_benchmark.duckdb")
RUNS_WITH_RCA = Path("data/processed/runs_with_rca.parquet")
STEP_SIGNALS = Path("data/processed/step_signals.parquet")
SWE_RUNS_WITH_RCA = Path("data/processed/swe_agent_runs_with_rca.parquet")
SWE_STEP_SIGNALS = Path("data/processed/swe_agent_step_signals.parquet")
AFWB_SCENARIOS = Path("data/afwb/scenarios/foundation.json")
AFWB_GOLD = Path("data/afwb/gold/foundation.json")
AFWB_REFERENCE_TRACES = Path("results/afwb/raw/reference_runs.jsonl")
AFWB_MUTATED_TRACES = Path("results/afwb/raw/mutated_runs.jsonl")
TERMINAL_PUBLIC_REPORT = Path("reports/public_benchmark.json")
SWE_PUBLIC_REPORT = Path("reports/swe_agent_public_benchmark.json")


DISCLAIMER = (
    "Results are historical and trajectory-backed. Waste, RCA, and savings values "
    "are rule-based estimates, not ground truth."
)


@st.cache_data(show_spinner=False)
def query(sql: str, dataset: str = "terminalbench") -> pl.DataFrame:
    db_path = SWE_DB_PATH if dataset == "swe_agent" else DB_PATH
    if not db_path.exists():
        return public_query(sql, dataset=dataset)
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return pl.from_arrow(con.execute(sql).fetch_arrow_table())
    finally:
        con.close()


@st.cache_data(show_spinner=False)
def report_json(path: str) -> dict:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    return json.loads(file_path.read_text())


def public_report_path(dataset: str) -> Path:
    return SWE_PUBLIC_REPORT if dataset == "swe_agent" else TERMINAL_PUBLIC_REPORT


@st.cache_data(show_spinner=False)
def public_report(dataset: str = "terminalbench") -> dict:
    path = public_report_path(dataset)
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _table_name(sql: str) -> str:
    match = re.search(r"\bfrom\s+([a-zA-Z0-9_]+)", sql, flags=re.IGNORECASE)
    if match:
        return match.group(1).lower()
    match = re.search(r"select\s+\*\s+from\s+([a-zA-Z0-9_]+)", sql, flags=re.IGNORECASE)
    return match.group(1).lower() if match else ""


def _limit(sql: str) -> int | None:
    match = re.search(r"\blimit\s+(\d+)", sql, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _frame(rows: list[dict] | dict | None, limit: int | None = None) -> pl.DataFrame:
    if rows is None:
        return pl.DataFrame()
    if isinstance(rows, dict):
        rows = [rows]
    if limit is not None:
        rows = rows[:limit]
    return pl.DataFrame(rows, strict=False) if rows else pl.DataFrame()


@st.cache_data(show_spinner=False)
def public_query(sql: str, dataset: str = "terminalbench") -> pl.DataFrame:
    report = public_report(dataset)
    table = _table_name(sql)
    limit = _limit(sql)
    if not report:
        return pl.DataFrame()

    if table == "overview":
        return _frame(report.get("overview"), limit)
    if table == "outcome_comparison":
        path = (
            Path("reports/swe_agent_outcome_comparison.csv")
            if dataset == "swe_agent"
            else Path("reports/outcome_comparison.csv")
        )
        return pl.read_csv(path) if path.exists() else pl.DataFrame()
    if table == "agent_model_leaderboard":
        return _frame(report.get("systems"), limit)
    if table == "agent_leaderboard":
        return _frame(report.get("agents"), limit)
    if table == "model_uncontrolled_leaderboard":
        return _frame(report.get("models_uncontrolled"), limit)
    if table == "failure_patterns":
        return _frame(report.get("failure_patterns"), limit)
    if table == "early_stop_simulation":
        return _frame(report.get("early_stopping"), limit)
    if table == "trajectory_coverage_by_system":
        rows = [
            {
                "agent": row.get("agent"),
                "model": row.get("model"),
                "runs": row.get("runs"),
                "trajectory_coverage": row.get("trajectory_coverage"),
            }
            for row in report.get("systems", [])
        ]
        return _frame(rows, limit)
    if table == "cost_coverage_by_system":
        rows = [
            {
                "agent": row.get("agent"),
                "model": row.get("model"),
                "runs": row.get("runs"),
                "cost_field_coverage": row.get("cost_field_coverage"),
                "positive_cost_coverage": row.get("positive_cost_coverage"),
                "cost_metrics_eligible": row.get("cost_metrics_eligible"),
            }
            for row in report.get("systems", [])
        ]
        return _frame(rows, limit)
    return pl.DataFrame()


@st.cache_data(show_spinner=False)
def afwb_scenarios() -> pl.DataFrame:
    if not AFWB_SCENARIOS.exists():
        return pl.DataFrame()
    rows = []
    for scenario in json.loads(AFWB_SCENARIOS.read_text()):
        remediation = scenario.get("remediation") or {}
        rows.append(
            {
                "scenario_id": scenario.get("scenario_id"),
                "name": scenario.get("name"),
                "family": scenario.get("family"),
                "root_cause_category": scenario.get("root_cause_category"),
                "remediation_type": remediation.get("remediation_type"),
                "remediation_id": remediation.get("remediation_id"),
                "memory_test": scenario.get("memory_test"),
            }
        )
    return pl.DataFrame(rows, strict=False)


@st.cache_data(show_spinner=False)
def afwb_gold() -> pl.DataFrame:
    if not AFWB_GOLD.exists():
        return pl.DataFrame()
    rows = []
    for label in json.loads(AFWB_GOLD.read_text()):
        remediation = label.get("remediation") or {}
        rows.append(
            {
                "scenario_id": label.get("scenario_id"),
                "failed": label.get("failed"),
                "root_cause_category": label.get("root_cause_category"),
                "root_cause_span_id": label.get("root_cause_span_id"),
                "first_observable_failure_span_id": label.get(
                    "first_observable_failure_span_id"
                ),
                "remediation_id": remediation.get("remediation_id"),
            }
        )
    return pl.DataFrame(rows, strict=False)


@st.cache_data(show_spinner=False)
def afwb_trace_summary() -> pl.DataFrame:
    rows = []
    for variant, path in (
        ("reference", AFWB_REFERENCE_TRACES),
        ("mutated", AFWB_MUTATED_TRACES),
    ):
        if not path.exists():
            rows.append(
                {
                    "variant": variant,
                    "traces": 0,
                    "passed": 0,
                    "failed": 0,
                    "total_tool_calls": 0,
                    "total_input_tokens": 0,
                    "total_output_tokens": 0,
                    "generated": False,
                }
            )
            continue
        traces = [
            json.loads(line)
            for line in path.read_text().splitlines()
            if line.strip()
        ]
        rows.append(
            {
                "variant": variant,
                "traces": len(traces),
                "passed": sum(trace.get("status") == "passed" for trace in traces),
                "failed": sum(trace.get("status") == "failed" for trace in traces),
                "total_tool_calls": sum(trace.get("total_tool_calls") or 0 for trace in traces),
                "total_input_tokens": sum(
                    trace.get("total_input_tokens") or 0 for trace in traces
                ),
                "total_output_tokens": sum(
                    trace.get("total_output_tokens") or 0 for trace in traces
                ),
                "generated": True,
            }
        )
    return pl.DataFrame(rows, strict=False)


@st.cache_data(show_spinner=False)
def available_datasets() -> list[tuple[str, str]]:
    datasets = [("terminalbench", "Terminal-Bench")]
    if SWE_DB_PATH.exists() or SWE_PUBLIC_REPORT.exists():
        datasets.append(("swe_agent", "SWE-agent"))
    return datasets


def _runs_path(dataset: str) -> Path:
    return SWE_RUNS_WITH_RCA if dataset == "swe_agent" else RUNS_WITH_RCA


def _steps_path(dataset: str) -> Path:
    return SWE_STEP_SIGNALS if dataset == "swe_agent" else STEP_SIGNALS


@st.cache_data(show_spinner=False)
def run_options(limit: int = 1_000, dataset: str = "terminalbench") -> list[str]:
    path = _runs_path(dataset)
    if not path.exists():
        return [
            example.get("run_id")
            for example in public_report(dataset).get("examples", [])[:limit]
            if example.get("run_id")
        ]
    return (
        pl.scan_parquet(path)
        .filter(pl.col("has_steps"))
        .select("run_id")
        .limit(limit)
        .collect()
        .get_column("run_id")
        .to_list()
    )


@st.cache_data(show_spinner=False)
def run_summary(run_id: str, dataset: str = "terminalbench") -> pl.DataFrame:
    if not _runs_path(dataset).exists():
        examples = public_report(dataset).get("examples", [])
        rows = [
            {
                key: value
                for key, value in example.items()
                if key != "steps"
            }
            for example in examples
            if example.get("run_id") == run_id
        ]
        return _frame(rows)
    return (
        pl.scan_parquet(_runs_path(dataset))
        .filter(pl.col("run_id") == run_id)
        .collect()
    )


@st.cache_data(show_spinner=False)
def run_steps(
    run_id: str,
    limit: int = 300,
    dataset: str = "terminalbench",
) -> pl.DataFrame:
    if not _steps_path(dataset).exists():
        examples = public_report(dataset).get("examples", [])
        for example in examples:
            if example.get("run_id") == run_id:
                return _frame(example.get("steps", []), limit)
        return pl.DataFrame()
    return (
        pl.scan_parquet(_steps_path(dataset))
        .filter(pl.col("run_id") == run_id)
        .select(
            [
                "step_index",
                "tool_index",
                "source",
                "tool_name",
                "command",
                "observation",
                "is_error",
                "suspected_waste",
                "repeated_failed_attempt",
            ]
        )
        .sort(["step_index", "tool_index"])
        .limit(limit)
        .collect()
    )
