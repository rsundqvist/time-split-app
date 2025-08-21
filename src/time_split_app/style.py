"""Weg page style customization."""

import logging
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from . import config

CSS: str | None = None


def apply_custom_css() -> None:
    """Apply CSS style sheets."""
    if not config.USE_CUSTOM_CSS:
        return

    debug = config.DEBUG

    global CSS  # noqa: PLW0603
    if CSS is None or debug:
        path = Path(__file__).parent / "style.css"
        CSS = path.read_text()
        logging.getLogger(__name__).info(f"Read CSS style sheets from '{path}'.")

    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

    if debug:
        path = Path(__file__).parent / "style.css"

        left, right = st.columns(2)

        with left:
            rows = [
                f"<!-- {path} -->",
                f"<!-- {config.USE_CUSTOM_CSS=} -->",
                "",
                f"<style>\n{CSS}</style>",
            ]
            st.code("\n".join(rows), language="css")

        with right:
            st.dataframe(pd.Series(st.query_params, name="Query param value").sort_index().to_frame())
            st.dataframe(pd.Series(os.environ, name="Env var value").sort_index().to_frame())
