from __future__ import annotations

import streamlit as st

from data import DISCLAIMER, available_datasets, query


st.caption(DISCLAIMER)
st.title("Leaderboards")
for (dataset_key, label), tab in zip(
    available_datasets(),
    st.tabs([label for _, label in available_datasets()]),
):
    with tab:
        tab_systems, tab_agents, tab_models = st.tabs(
            ["Agent + Model", "Agents", "Models"]
        )
        with tab_systems:
            st.dataframe(
                query(
                    "SELECT * FROM agent_model_leaderboard ORDER BY runs DESC",
                    dataset=dataset_key,
                ),
                use_container_width=True,
            )
        with tab_agents:
            st.dataframe(
                query(
                    "SELECT * FROM agent_leaderboard ORDER BY runs DESC",
                    dataset=dataset_key,
                ),
                use_container_width=True,
            )
        with tab_models:
            st.dataframe(
                query(
                    "SELECT * FROM model_uncontrolled_leaderboard ORDER BY runs DESC",
                    dataset=dataset_key,
                ),
                use_container_width=True,
            )
