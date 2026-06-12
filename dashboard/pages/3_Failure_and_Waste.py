from __future__ import annotations

import plotly.express as px
import streamlit as st

from data import DISCLAIMER, available_datasets, query


st.caption(DISCLAIMER)
st.title("Failure and Waste")
for (dataset_key, label), tab in zip(
    available_datasets(),
    st.tabs([label for _, label in available_datasets()]),
):
    with tab:
        if dataset_key == "swe_agent":
            st.caption("Cost metrics are unavailable for SWE-agent trajectories.")
        patterns = query(
            "SELECT * FROM failure_patterns ORDER BY failed_runs DESC",
            dataset=dataset_key,
        )
        st.plotly_chart(
            px.bar(patterns, x="rule_based_rca", y="failed_runs"),
            use_container_width=True,
        )
        st.dataframe(patterns, use_container_width=True)

        st.subheader("Early-stop simulation")
        try:
            early = query(
                "SELECT * FROM early_stop_simulation LIMIT 5000",
                dataset=dataset_key,
            )
            st.dataframe(early, use_container_width=True)
        except Exception:
            st.info("Run the early-stop command to populate this table.")
