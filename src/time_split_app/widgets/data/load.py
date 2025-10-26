"""Utility functions for loading datasets."""

import typing as _t

import pandas as _pd
import streamlit as _st


def make_formatter(data: _pd.Series | float | int) -> _t.Callable[[float], str]:
    """Create a formatter based on magnitude.

    Args:
        data: An series or a scalar. Base decision on ``abs(mean(data))`` if a series.

    Returns:
        A formatting callable ``(float) -> str``.
    """
    value = data.abs().mean() if isinstance(data, _pd.Series) else abs(data)

    if value > 999:  # noqa: PLR2004
        spec = "_d" if value > 9999 else "d"  # noqa: PLR2004
        return lambda f: f"{int(f):{spec}}"

    if value > 10:
        fmt = "{:.1f}"
    elif value > 1:
        fmt = "{:.2f}"
    else:
        fmt = "{:.4g}"
    return fmt.format


def error_on_unaggregated_data(df: _pd.DataFrame) -> None:
    """Show error in modal window."""

    if df.index.is_unique:
        return

    _st.error("Data must be pre-aggregated.", icon="🚨")
    _error_on_unaggregated_data(df)


@_st.dialog("🚨 Bad data")
def _error_on_unaggregated_data(df: _pd.DataFrame) -> _t.Never:
    _st.error("Data must be pre-aggregated.", icon="🚨")

    index = df.index
    duplicated = index.duplicated(False)

    message = _UNAGGREGATED_DATA_MESSAGE.format(index=df.index.name, n_duplicated=duplicated.sum())
    _st.write(message)

    duplicated_df = df.loc[duplicated]
    max_to_show = 5
    samples = duplicated_df.head(max_to_show).sort_index() if len(duplicated_df) > max_to_show else duplicated_df
    _st.dataframe(samples.reset_index(), hide_index=False, width="stretch")
    _st.write(f"Showing `{len(samples)}/{len(duplicated_df)}` duplicated rows. Original `shape={df.shape}`.")

    _st.stop()


_UNAGGREGATED_DATA_MESSAGE = """
Found `{n_duplicated}` duplicate values in `index='{index}'`.

While the `time-split` [package](https://time-split.readthedocs.io/) is designed primarily with unaggregated data in
mind, this application requires pre-aggregated data for performance reasons.
"""
