from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures" / "lumniverse_agent_efficiency"
OUT_JSON = REPORTS / "lumniverse_agent_efficiency_benchmark_data.json"

TERMINAL_RUNS = ROOT / "data" / "processed" / "runs_with_rca.parquet"
SWE_RUNS = ROOT / "data" / "processed" / "swe_agent_runs_with_rca.parquet"
TERMINAL_EARLY_STOP = ROOT / "data" / "processed" / "early_stop_simulation.parquet"
SWE_EARLY_STOP = ROOT / "data" / "processed" / "swe_agent_early_stop_simulation.parquet"


COLORS = {
    "navy": "#0B2545",
    "blue": "#2E74B5",
    "teal": "#2A9D8F",
    "gold": "#C8912B",
    "red": "#B23A48",
    "purple": "#6D5BD0",
    "gray": "#687381",
    "light": "#F2F4F7",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return clean_value(value.item())
    if isinstance(value, float):
        return round(value, 10)
    return value


def records(df: pd.DataFrame) -> list[dict[str, Any]]:
    return [{k: clean_value(v) for k, v in row.items()} for row in df.to_dict("records")]


def query_df(con: duckdb.DuckDBPyConnection, sql: str) -> pd.DataFrame:
    return con.execute(sql).fetchdf()


def pct(value: float) -> float:
    return 100.0 * value


def money_label(value: float) -> str:
    if value >= 1000:
        return f"${value:,.0f}"
    return f"${value:,.2f}"


def save_fig(fig: plt.Figure, name: str) -> str:
    FIGURES.mkdir(parents=True, exist_ok=True)
    path = FIGURES / f"{name}.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(path.relative_to(ROOT))


def style_axes(ax: plt.Axes, title: str, xlabel: str | None = None) -> None:
    ax.set_title(title, loc="left", fontsize=12, fontweight="bold", color=COLORS["navy"], pad=12)
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=9, color=COLORS["gray"])
    ax.tick_params(axis="both", labelsize=8, colors="#263238")
    ax.grid(axis="y", color="#DDE3EA", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")


def chart_benchmark_coverage(data: dict[str, Any]) -> str:
    labels = ["Terminal-Bench", "SWE-agent"]
    pass_rates = [
        pct(data["terminal_overview"]["pass_rate"]),
        pct(data["swe_overview_direct"]["pass_rate"]),
    ]
    coverage = [
        pct(data["terminal_overview"]["trajectory_coverage"]),
        pct(data["swe_overview_direct"]["trajectory_coverage"]),
    ]
    x = range(len(labels))
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    width = 0.34
    ax.bar([i - width / 2 for i in x], pass_rates, width, label="Pass rate", color=COLORS["blue"])
    ax.bar([i + width / 2 for i in x], coverage, width, label="Trajectory coverage", color=COLORS["teal"])
    for i, value in enumerate(pass_rates):
        ax.text(i - width / 2, value + 2, f"{value:.1f}%", ha="center", fontsize=8)
    for i, value in enumerate(coverage):
        ax.text(i + width / 2, value + 2, f"{value:.1f}%", ha="center", fontsize=8)
    ax.set_xticks(list(x), labels)
    ax.set_ylim(0, 110)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    style_axes(ax, "Pass rate and trajectory coverage are different questions", "Percent")
    return save_fig(fig, "01_benchmark_coverage")


def chart_cost_outcome(data: dict[str, Any]) -> str:
    rows = data["terminal_outcome_cost"]
    failed = next(row for row in rows if row["success"] is False)
    passed = next(row for row in rows if row["success"] is True)
    labels = ["Failed", "Successful"]
    total_cost = [failed["total_cost_usd"], passed["total_cost_usd"]]
    avg_cost = [failed["avg_cost_usd"], passed["avg_cost_usd"]]

    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.6))
    axes[0].bar(labels, total_cost, color=[COLORS["red"], COLORS["teal"]])
    axes[0].set_ylabel("Observed cost, USD", fontsize=9)
    for i, value in enumerate(total_cost):
        axes[0].text(i, value * 1.02, money_label(value), ha="center", fontsize=8)
    style_axes(axes[0], "Total observed cost")

    axes[1].bar(labels, avg_cost, color=[COLORS["red"], COLORS["teal"]])
    axes[1].set_ylabel("Average cost per run, USD", fontsize=9)
    for i, value in enumerate(avg_cost):
        axes[1].text(i, value * 1.05, f"${value:.3f}", ha="center", fontsize=8)
    style_axes(axes[1], "Average cost per run")
    fig.suptitle("Failed runs consume most observed Terminal-Bench spend", fontsize=13, fontweight="bold", color=COLORS["navy"], x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    return save_fig(fig, "02_cost_by_outcome")


def chart_success_waste(data: dict[str, Any]) -> str:
    row = data["terminal_success_waste"]
    labels = ["Adjacent repeats", "Error events", "Suspected wasted actions"]
    values = [row["adjacent_repeats"], row["error_events"], row["suspected_wasted_actions"]]
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    bars = ax.barh(labels, values, color=[COLORS["purple"], COLORS["gold"], COLORS["blue"]])
    for bar, value in zip(bars, values):
        ax.text(value * 1.01, bar.get_y() + bar.get_height() / 2, f"{value:,.0f}", va="center", fontsize=8)
    style_axes(ax, "Successful Terminal-Bench trajectory runs still contain waste signals", "Event count")
    ax.grid(axis="x", color="#DDE3EA", linewidth=0.8)
    ax.grid(axis="y", visible=False)
    return save_fig(fig, "03_successful_runs_waste")


def chart_repeated_actions(data: dict[str, Any]) -> str:
    rows = data["terminal_repeated_failed_agents"][:6]
    rows = sorted(rows, key=lambda row: row["repeated_failed_rca_rate_pct"])
    labels = [row["agent"] for row in rows]
    values = [row["repeated_failed_rca_rate_pct"] for row in rows]
    counts = [row["repeated_failed_rca_runs"] for row in rows]
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    bars = ax.barh(labels, values, color=COLORS["red"])
    for bar, rate, count in zip(bars, values, counts):
        ax.text(rate + 0.12, bar.get_y() + bar.get_height() / 2, f"{rate:.2f}% ({count} runs)", va="center", fontsize=8)
    style_axes(ax, "Strict repeated-failed-approach rate by agent", "Percent of trajectory runs")
    ax.grid(axis="x", color="#DDE3EA", linewidth=0.8)
    ax.grid(axis="y", visible=False)
    return save_fig(fig, "04_repeated_failed_actions")


def chart_divergence(data: dict[str, Any]) -> str:
    terminal = {row["success"]: row for row in data["terminal_trajectory_outcome"]}
    swe = {row["success"]: row for row in data["swe_outcome_direct"]}
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.8))

    labels = ["Duration sec", "Steps", "Tool calls"]
    failed = [
        terminal[False]["median_duration_seconds"],
        terminal[False]["median_steps"],
        terminal[False]["median_tool_calls"],
    ]
    passed = [
        terminal[True]["median_duration_seconds"],
        terminal[True]["median_steps"],
        terminal[True]["median_tool_calls"],
    ]
    x = range(len(labels))
    width = 0.35
    axes[0].bar([i - width / 2 for i in x], failed, width, label="Failed", color=COLORS["red"])
    axes[0].bar([i + width / 2 for i in x], passed, width, label="Successful", color=COLORS["teal"])
    axes[0].set_xticks(list(x), labels, rotation=12, ha="right")
    axes[0].legend(frameon=False, fontsize=8)
    style_axes(axes[0], "Terminal-Bench medians")

    labels = ["Steps", "Tool calls", "Repeat rate %"]
    failed = [
        swe[False]["median_steps"],
        swe[False]["median_tool_calls"],
        pct(swe[False]["mean_repeat_rate"]),
    ]
    passed = [
        swe[True]["median_steps"],
        swe[True]["median_tool_calls"],
        pct(swe[True]["mean_repeat_rate"]),
    ]
    x = range(len(labels))
    axes[1].bar([i - width / 2 for i in x], failed, width, label="Failed", color=COLORS["red"])
    axes[1].bar([i + width / 2 for i in x], passed, width, label="Successful", color=COLORS["teal"])
    axes[1].set_xticks(list(x), labels, rotation=12, ha="right")
    axes[1].legend(frameon=False, fontsize=8)
    style_axes(axes[1], "SWE-agent medians and repeat rate")
    fig.suptitle("Failed trajectories diverge before the final outcome", fontsize=13, fontweight="bold", color=COLORS["navy"], x=0.02, ha="left")
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    return save_fig(fig, "05_trajectory_divergence")


def chart_early_stop(data: dict[str, Any]) -> str:
    rows = sorted(data["terminal_early_stop_policy"], key=lambda row: row["estimated_cost_saved_usd"])
    labels = [row["policy"].replace("_", " ") for row in rows]
    values = [row["estimated_cost_saved_usd"] for row in rows]
    fig, ax = plt.subplots(figsize=(7.3, 3.7))
    bars = ax.barh(labels, values, color=[COLORS["gold"], COLORS["blue"], COLORS["teal"]])
    for bar, value in zip(bars, values):
        ax.text(value * 1.01 + 5, bar.get_y() + bar.get_height() / 2, money_label(value), va="center", fontsize=8)
    style_axes(ax, "Conservative early-stop savings by policy", "Estimated saved cost, USD")
    ax.grid(axis="x", color="#DDE3EA", linewidth=0.8)
    ax.grid(axis="y", visible=False)
    return save_fig(fig, "06_early_stop_savings")


def chart_scaffold(data: dict[str, Any]) -> str:
    rows = data["terminal_gpt5_scaffolds"]
    labels = [row["agent"] for row in rows]
    pass_rates = [pct(row["pass_rate"]) for row in rows]
    durations = [row["median_duration_seconds"] for row in rows]
    fig, ax = plt.subplots(figsize=(7.2, 3.7))
    bars = ax.bar(labels, pass_rates, color=[COLORS["teal"], COLORS["blue"], COLORS["gold"], COLORS["purple"]])
    for bar, rate, dur in zip(bars, pass_rates, durations):
        ax.text(bar.get_x() + bar.get_width() / 2, rate + 1.5, f"{rate:.1f}%\n{dur:.0f}s", ha="center", fontsize=8)
    ax.set_ylim(0, max(pass_rates) + 14)
    style_axes(ax, "Same model, different scaffold: gpt-5@openai", "Pass rate; label includes median duration")
    return save_fig(fig, "07_same_model_scaffold")


def chart_failure_patterns(data: dict[str, Any]) -> str:
    rows = [
        row
        for row in data["terminal_failure_patterns"]
        if row["rule_based_rca"] != "MISSING_TRAJECTORY"
        and row["estimated_wasted_cost_usd"] is not None
    ]
    rows = sorted(rows, key=lambda row: row["estimated_wasted_cost_usd"])
    labels = [row["rule_based_rca"].replace("_", " ").title() for row in rows]
    values = [row["estimated_wasted_cost_usd"] for row in rows]
    fig, ax = plt.subplots(figsize=(7.3, 4.1))
    bars = ax.barh(labels, values, color=COLORS["red"])
    for bar, value in zip(bars, values):
        ax.text(value + 1.0, bar.get_y() + bar.get_height() / 2, money_label(value), va="center", fontsize=8)
    style_axes(ax, "Estimated avoidable Terminal-Bench cost by failure pattern", "Estimated wasted cost, USD")
    ax.grid(axis="x", color="#DDE3EA", linewidth=0.8)
    ax.grid(axis="y", visible=False)
    return save_fig(fig, "08_failure_pattern_cost")


def build_data() -> dict[str, Any]:
    con = duckdb.connect()
    terminal_overview = read_json(REPORTS / "overview.json")
    terminal_quality = read_json(REPORTS / "data_quality.json")
    swe_quality = read_json(REPORTS / "swe_agent_data_quality.json")
    afwb_gold = json.loads((ROOT / "data" / "afwb" / "gold" / "foundation.json").read_text())

    terminal_outcome_cost = query_df(
        con,
        f"""
        select success,
          count(*) runs,
          sum(case when has_steps then 1 else 0 end) trajectory_runs,
          sum(cost_usd) total_cost_usd,
          avg(cost_usd) avg_cost_usd,
          median(cost_usd) median_cost_usd,
          sum(case when has_positive_cost then 1 else 0 end) positive_cost_runs,
          median(case when has_positive_cost then cost_usd end) median_positive_cost_usd,
          sum(duration_seconds) total_duration_seconds,
          median(duration_seconds) median_duration_seconds,
          median(step_count) median_steps,
          median(tool_call_count) median_tool_calls,
          avg(suspected_waste_rate) mean_waste_rate,
          sum(estimated_wasted_cost_usd) estimated_wasted_cost_usd,
          sum(estimated_wasted_duration_seconds) estimated_wasted_duration_seconds,
          avg(error_event_rate) mean_error_rate,
          avg(repeat_rate) mean_repeat_rate
        from read_parquet('{TERMINAL_RUNS}')
        group by success
        order by success;
        """,
    )

    terminal_trajectory_outcome = query_df(
        con,
        f"""
        select success,
          count(*) runs,
          median(cost_usd) median_cost_usd,
          avg(cost_usd) avg_cost_usd,
          median(duration_seconds) median_duration_seconds,
          median(step_count) median_steps,
          median(tool_call_count) median_tool_calls,
          avg(error_event_rate) mean_error_event_rate,
          avg(repeat_rate) mean_repeat_rate,
          avg(suspected_waste_rate) mean_waste_rate,
          sum(estimated_wasted_cost_usd) estimated_wasted_cost_usd,
          sum(estimated_wasted_duration_seconds) estimated_wasted_duration_seconds,
          sum(suspected_wasted_actions) suspected_wasted_actions,
          sum(error_events) error_events,
          sum(adjacent_repeats) adjacent_repeats,
          sum(same_result_repeats) same_result_repeats
        from read_parquet('{TERMINAL_RUNS}')
        where has_steps
        group by success
        order by success;
        """,
    )

    terminal_failure_patterns = query_df(
        con,
        f"""
        select rule_based_rca,
          count(*) runs,
          sum(case when success=false then 1 else 0 end) failed_runs,
          sum(cost_usd) total_observed_cost_usd,
          median(cost_usd) median_cost_usd,
          sum(estimated_wasted_cost_usd) estimated_wasted_cost_usd,
          sum(estimated_wasted_duration_seconds) estimated_wasted_duration_seconds,
          avg(suspected_waste_rate) mean_waste_rate,
          avg(error_event_rate) mean_error_rate,
          avg(repeat_rate) mean_repeat_rate
        from read_parquet('{TERMINAL_RUNS}')
        group by 1
        order by estimated_wasted_cost_usd desc nulls last;
        """,
    )

    terminal_repeated_failed_agents = query_df(
        con,
        f"""
        select agent,
          count(*) runs,
          sum(case when rule_based_rca='REPEATED_FAILED_APPROACH' then 1 else 0 end) repeated_failed_rca_runs,
          100.0 * sum(case when rule_based_rca='REPEATED_FAILED_APPROACH' then 1 else 0 end) / count(*) repeated_failed_rca_rate_pct,
          sum(repeated_failed_attempts) repeated_failed_attempt_events,
          avg(repeat_rate) mean_repeat_rate,
          avg(suspected_waste_rate) mean_waste_rate,
          sum(estimated_wasted_cost_usd) estimated_wasted_cost_usd
        from read_parquet('{TERMINAL_RUNS}')
        where has_steps
        group by agent
        having count(*) >= 100
        order by repeated_failed_rca_rate_pct desc, repeated_failed_rca_runs desc
        limit 15;
        """,
    )

    terminal_repeat_rate_agents = query_df(
        con,
        f"""
        select agent,
          count(*) trajectory_runs,
          sum(success::int) successful_runs,
          avg(repeat_rate) mean_repeat_rate,
          median(repeat_rate) median_repeat_rate,
          avg(error_event_rate) mean_error_rate,
          avg(suspected_waste_rate) mean_waste_rate
        from read_parquet('{TERMINAL_RUNS}')
        where has_steps
        group by agent
        having count(*) >= 100
        order by mean_repeat_rate desc
        limit 10;
        """,
    )

    terminal_gpt5_scaffolds = query_df(
        con,
        f"""
        select agent,
          count(*) runs,
          sum(success::int) successes,
          avg(success::int) pass_rate,
          median(cost_usd) median_cost_usd,
          median(duration_seconds) median_duration_seconds,
          median(step_count) median_steps,
          median(tool_call_count) median_tool_calls,
          avg(error_event_rate) mean_error_rate,
          avg(repeat_rate) mean_repeat_rate,
          avg(suspected_waste_rate) mean_waste_rate
        from read_parquet('{TERMINAL_RUNS}')
        where has_steps and model = 'gpt-5@openai'
        group by agent
        having count(*) >= 100
        order by pass_rate desc;
        """,
    )

    terminal_early_stop_policy = query_df(
        con,
        f"""
        select policy,
          sum((triggered and not false_stop)::int) conservative_triggers,
          100.0 * sum((triggered and not false_stop)::int) / count(*) conservative_trigger_rate_pct,
          sum(case when triggered and not false_stop then events_saved else 0 end) events_saved,
          sum(case when triggered and not false_stop then estimated_cost_saved_usd else 0 end) estimated_cost_saved_usd,
          sum(case when triggered and not false_stop then estimated_duration_saved_seconds else 0 end) estimated_duration_saved_seconds
        from read_parquet('{TERMINAL_EARLY_STOP}')
        group by policy
        order by estimated_cost_saved_usd desc;
        """,
    )

    terminal_early_stop_max = query_df(
        con,
        f"""
        with e as (
          select run_id,
            max(case when triggered and not false_stop then estimated_cost_saved_usd else 0 end) max_cost,
            max(case when triggered and not false_stop then estimated_duration_saved_seconds else 0 end) max_duration,
            max(case when triggered and not false_stop then events_saved else 0 end) max_events,
            bool_or(triggered and not false_stop) conservative_triggered
          from read_parquet('{TERMINAL_EARLY_STOP}')
          group by run_id
        )
        select count(*) runs,
          sum(conservative_triggered::int) conservative_triggered_runs,
          100.0 * sum(conservative_triggered::int) / count(*) conservative_trigger_rate_pct,
          sum(max_events) events_saved,
          sum(max_cost) estimated_cost_saved_usd,
          sum(max_duration) estimated_duration_saved_seconds
        from e;
        """,
    )

    swe_overview_direct = query_df(
        con,
        f"""
        select count(*) runs,
          sum(success::int) successful_runs,
          avg(success::int) pass_rate,
          count(distinct task_name) tasks,
          count(distinct agent) agents,
          count(distinct model) models,
          sum(has_steps::int) trajectory_runs,
          avg(has_steps::int) trajectory_coverage,
          median(step_count) median_steps,
          median(tool_call_count) median_tool_calls,
          avg(suspected_waste_rate) mean_waste_rate,
          avg(error_event_rate) mean_error_rate,
          avg(repeat_rate) mean_repeat_rate,
          sum(case when has_cost then 1 else 0 end) cost_runs,
          sum(case when has_duration then 1 else 0 end) duration_runs
        from read_parquet('{SWE_RUNS}');
        """,
    ).iloc[0].to_dict()

    swe_outcome_direct = query_df(
        con,
        f"""
        select success,
          count(*) runs,
          median(step_count) median_steps,
          median(tool_call_count) median_tool_calls,
          avg(error_event_rate) mean_error_rate,
          avg(repeat_rate) mean_repeat_rate,
          avg(suspected_waste_rate) mean_waste_rate,
          sum(suspected_wasted_actions) suspected_wasted_actions,
          sum(error_events) error_events,
          sum(adjacent_repeats) adjacent_repeats,
          sum(same_result_repeats) same_result_repeats
        from read_parquet('{SWE_RUNS}')
        group by success
        order by success;
        """,
    )

    swe_failure_patterns = query_df(
        con,
        f"""
        select rule_based_rca,
          count(*) runs,
          sum(case when success=false then 1 else 0 end) failed_runs,
          avg(suspected_waste_rate) mean_waste_rate,
          avg(error_event_rate) mean_error_rate,
          avg(repeat_rate) mean_repeat_rate,
          sum(suspected_wasted_actions) suspected_wasted_actions
        from read_parquet('{SWE_RUNS}')
        group by 1
        order by runs desc;
        """,
    )

    afwb_totals = {
        "scenarios": len(afwb_gold),
        "avoidable_input_tokens": sum(row["avoidable_usage"]["input_tokens"] for row in afwb_gold),
        "avoidable_output_tokens": sum(row["avoidable_usage"]["output_tokens"] for row in afwb_gold),
        "avoidable_tool_calls": sum(row["avoidable_usage"]["tool_calls"] for row in afwb_gold),
        "avoidable_latency_ms": sum(row["avoidable_usage"]["latency_ms"] for row in afwb_gold),
        "avoidable_cost_usd": sum(row["avoidable_usage"]["cost_usd"] for row in afwb_gold),
    }

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "terminal_overview": terminal_overview,
        "terminal_quality": terminal_quality,
        "swe_quality": swe_quality,
        "swe_overview_direct": {k: clean_value(v) for k, v in swe_overview_direct.items()},
        "terminal_outcome_cost": records(terminal_outcome_cost),
        "terminal_trajectory_outcome": records(terminal_trajectory_outcome),
        "terminal_failure_patterns": records(terminal_failure_patterns),
        "terminal_repeated_failed_agents": records(terminal_repeated_failed_agents),
        "terminal_repeat_rate_agents": records(terminal_repeat_rate_agents),
        "terminal_gpt5_scaffolds": records(terminal_gpt5_scaffolds),
        "terminal_early_stop_policy": records(terminal_early_stop_policy),
        "terminal_early_stop_max": records(terminal_early_stop_max)[0],
        "swe_outcome_direct": records(swe_outcome_direct),
        "swe_failure_patterns": records(swe_failure_patterns),
        "afwb_scenarios": afwb_gold,
        "afwb_totals": afwb_totals,
    }

    data["derived"] = {}
    failed = next(row for row in data["terminal_outcome_cost"] if row["success"] is False)
    passed = next(row for row in data["terminal_outcome_cost"] if row["success"] is True)
    data["derived"]["terminal_failed_cost_share"] = failed["total_cost_usd"] / (
        failed["total_cost_usd"] + passed["total_cost_usd"]
    )
    data["derived"]["terminal_avg_failed_to_success_cost_ratio"] = failed["avg_cost_usd"] / passed["avg_cost_usd"]
    success_traj = next(row for row in data["terminal_trajectory_outcome"] if row["success"] is True)
    data["terminal_success_waste"] = success_traj

    data["figures"] = {
        "benchmark_coverage": chart_benchmark_coverage(data),
        "cost_outcome": chart_cost_outcome(data),
        "success_waste": chart_success_waste(data),
        "repeated_actions": chart_repeated_actions(data),
        "divergence": chart_divergence(data),
        "early_stop": chart_early_stop(data),
        "scaffold": chart_scaffold(data),
        "failure_patterns": chart_failure_patterns(data),
    }

    return data


def main() -> None:
    REPORTS.mkdir(exist_ok=True)
    data = build_data()
    OUT_JSON.write_text(json.dumps(data, indent=2, sort_keys=True))
    print(f"Wrote {OUT_JSON.relative_to(ROOT)}")
    for name, path in data["figures"].items():
        print(f"Wrote figure {name}: {path}")


if __name__ == "__main__":
    main()
