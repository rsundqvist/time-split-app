"""Utility methods for dataframe formatting."""

from collections.abc import Mapping as _Mapping
from typing import Any as _Any

import pandas as _pd
import streamlit as _st
from matplotlib import colormaps as _colormaps


def select_cmap(key: str) -> str | None:
    """Select colormap.

    See Also:
        The Matplotlib `colormaps <https://matplotlib.org/stable/users/explain/colors/colormaps.html>`_ page.

    Args:
        key: Widget key prefix.

    Returns:
        A colormap string or ``None``.
    """
    disabled = "🚫 Disabled"
    options = [disabled, *sorted(_colormaps)]
    cmap = _st.selectbox(
        "Colormap",
        options,
        options.index("PuBu"),
        help="Matplotlib [colormap](https://matplotlib.org/stable/users/explain/colors/colormaps.html) to use."
        f" Set to `{disabled}` to disable cell highlighting.",
        key=f"{key}:{select_cmap.__name__}",
    )
    return None if cmap == disabled else cmap


def select_formatters(key: str, dtypes: _Mapping[str, _Any]) -> dict[str, str]:
    """Select column formatters.

    Args:
        key: Widget key prefix.
        dtypes: A mapping ``{column: dtype}``. Determines default formats.

    Returns:
        A dict ``{column: format}`` (such as ``{"my-float": "{:.2f}"}``).
    """
    with _st.popover("Format", width="stretch", icon="✏️"):
        formatters = {}
        for column, dtype in dtypes.items():
            if _pd.api.types.is_integer_dtype(dtype):
                default = "{:_d}"
            else:
                default = "{:.2f}"

            fmt = _st.text_input(f"Select `{column!r}` format.", default, key=f"{key}:{column}")
            if not fmt:
                fmt = "{}"
            formatters[column] = fmt
        return formatters
