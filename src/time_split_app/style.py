"""Weg page style customization."""

import logging
from pathlib import Path

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

        rows = [
            f"<!-- {path} -->",
            f"<!-- {config.DEBUG=} -->",
            f"<!-- {config.USE_CUSTOM_CSS=} -->",
            "",
            f"<style>\n{CSS}</style>",
        ]
        st.code("\n".join(rows), language="css")
