from __future__ import annotations

from pathlib import Path

import polars as pl
import streamlit as st

from data import (
    DISCLAIMER,
    afwb_gold,
    afwb_scenarios,
    afwb_trace_summary,
    available_datasets,
    query,
)
from formatting import money, pct


st.set_page_config(page_title="Agent Efficiency Benchmark", layout="wide")
st.caption(DISCLAIMER)
st.title("Agent Efficiency Benchmark")
st.info(
    "Model alone is insufficient; harness, tools, context handling, verification, "
    "and recovery behavior materially affect agent outcomes."
)
report_path = Path("reports/lumniverse_agent_efficiency_benchmark.pdf")
if report_path.exists():
    st.download_button(
        "Download benchmark insights PDF",
        data=report_path.read_bytes(),
        file_name="lumniverse_agent_efficiency_benchmark.pdf",
        mime="application/pdf",
    )

datasets = available_datasets()
tabs = st.tabs([label for _, label in datasets] + ["AFWB Lite"])

for (dataset_key, label), tab in zip(datasets, tabs[:-1]):
    with tab:
        overview = query("SELECT * FROM overview", dataset=dataset_key).to_dicts()[0]
        cols = st.columns(5)
        cols[0].metric("Runs", f"{overview['runs']:,}")
        cols[1].metric("Pass rate", pct(overview["pass_rate"]))
        cols[2].metric("Trajectory coverage", pct(overview["trajectory_coverage"]))
        cols[3].metric("Cost coverage", pct(overview["cost_field_coverage"]))
        cost_value = (
            "Cost unavailable"
            if dataset_key == "swe_agent"
            else money(overview["estimated_wasted_cost_usd"])
        )
        cols[4].metric("Estimated wasted cost", cost_value)

        st.write(
            {
                "dataset": label,
                "dataset_revision": overview.get("dataset_revision"),
                "snapshot_cutoff": overview.get("snapshot_cutoff"),
                "methodology_version": overview.get("methodology_version"),
            }
        )

        st.subheader("Top agent/model systems")
        st.dataframe(
            query(
                "SELECT agent, model, runs, tasks, pass_rate_micro, "
                "trajectory_coverage, cost_metrics_eligible, "
                "observed_cost_per_success_usd "
                "FROM agent_model_leaderboard ORDER BY runs DESC LIMIT 25",
                dataset=dataset_key,
            ),
            width="stretch",
        )

with tabs[-1]:
    scenarios = afwb_scenarios()
    gold = afwb_gold()
    trace_summary = afwb_trace_summary()

    cols = st.columns(5)
    cols[0].metric("Scenarios", f"{scenarios.height:,}")
    cols[1].metric(
        "Gold labels",
        f"{gold.height:,}",
    )
    cols[2].metric(
        "Reference traces",
        f"{trace_summary.filter(pl.col('variant') == 'reference').select('traces').item():,}"
        if not trace_summary.is_empty()
        else "0",
    )
    cols[3].metric(
        "Mutated traces",
        f"{trace_summary.filter(pl.col('variant') == 'mutated').select('traces').item():,}"
        if not trace_summary.is_empty()
        else "0",
    )
    cols[4].metric("Hosted calls", "0")

    st.write(
        {
            "milestone": "Foundation",
            "scenario_set": "first 4 RCA scenarios",
            "trace_output": "results/afwb/raw/",
            "local_only": True,
        }
    )

    st.subheader("Trace generation")
    st.dataframe(trace_summary, width="stretch")

    st.subheader("Foundation scenarios")
    st.dataframe(scenarios, width="stretch")

    st.subheader("Gold RCA labels")
    st.dataframe(gold, width="stretch")
