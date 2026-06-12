from __future__ import annotations

import plotly.express as px
import streamlit as st

from data import DISCLAIMER, available_datasets, query
from formatting import pct


st.caption(DISCLAIMER)
st.title("Overview")
for (dataset_key, label), tab in zip(
    available_datasets(),
    st.tabs([label for _, label in available_datasets()]),
):
    with tab:
        overview = query("SELECT * FROM overview", dataset=dataset_key).to_dicts()[0]
        st.write(
            {
                "runs": overview["runs"],
                "trajectory_coverage": pct(overview["trajectory_coverage"]),
                "cost_coverage": pct(overview["cost_field_coverage"]),
                "dataset_revision": overview.get("dataset_revision"),
                "snapshot_cutoff": overview.get("snapshot_cutoff"),
                "methodology_version": overview.get("methodology_version"),
            }
        )

        outcomes = query("SELECT * FROM outcome_comparison", dataset=dataset_key)
        st.plotly_chart(
            px.bar(outcomes, x="success", y="runs", color="scope", barmode="group"),
            use_container_width=True,
        )
        st.dataframe(outcomes, use_container_width=True)
