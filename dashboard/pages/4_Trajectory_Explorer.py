from __future__ import annotations

import streamlit as st

from data import DISCLAIMER, available_datasets, run_options, run_steps, run_summary


st.caption(DISCLAIMER)
st.title("Trajectory Explorer")
dataset_labels = {label: key for key, label in available_datasets()}
selected_label = st.selectbox("Dataset", list(dataset_labels))
dataset_key = dataset_labels[selected_label]
options = run_options(dataset=dataset_key)
if not options:
    st.warning("No trajectory artifacts found.")
    st.stop()

run_id = st.selectbox("Run", options)
summary = run_summary(run_id, dataset=dataset_key)
if not summary.is_empty():
    st.dataframe(summary, width="stretch")
st.dataframe(run_steps(run_id, dataset=dataset_key), width="stretch")
