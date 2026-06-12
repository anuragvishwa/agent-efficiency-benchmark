from __future__ import annotations

from pathlib import Path

import streamlit as st

from data import DISCLAIMER


st.caption(DISCLAIMER)
st.title("Methodology")
path = Path("METHODOLOGY.md")
if path.exists():
    st.markdown(path.read_text())
else:
    st.info("METHODOLOGY.md has not been generated yet.")
