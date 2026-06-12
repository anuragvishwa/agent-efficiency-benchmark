from __future__ import annotations

import streamlit as st

from data import DISCLAIMER, available_datasets, query, report_json


st.caption(DISCLAIMER)
st.title("Data Quality")
for (dataset_key, label), tab in zip(
    available_datasets(),
    st.tabs([label for _, label in available_datasets()]),
):
    with tab:
        quality_path = (
            "reports/swe_agent_data_quality.json"
            if dataset_key == "swe_agent"
            else "reports/data_quality.json"
        )
        st.json(report_json(quality_path))
        st.subheader("Coverage by system")
        st.dataframe(
            query(
                "SELECT * FROM trajectory_coverage_by_system ORDER BY runs DESC",
                dataset=dataset_key,
            ),
            width="stretch",
        )
        st.dataframe(
            query(
                "SELECT * FROM cost_coverage_by_system ORDER BY runs DESC",
                dataset=dataset_key,
            ),
            width="stretch",
        )
