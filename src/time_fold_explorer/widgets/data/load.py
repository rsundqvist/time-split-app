"""Utility functions for loading datasets."""

import typing as _t

import pandas as _pd
import streamlit as _st


def read_file(path: str, **kwargs: _t.Any) -> _pd.DataFrame:
    """Read frame from filepath."""
    parts = path.rsplit(".", maxsplit=3)

    is_compressed = path.endswith(COMPRESSION_SUFFIXES)
    file_format = parts[-2] if is_compressed else parts[-1]

    if (pandas_read_fn := FILE_SUFFIXES.get(file_format)) is None:
        raise NotImplementedError(f"{file_format=}")

    try:
        return pandas_read_fn(path, **kwargs)
    except Exception as e:
        _st.error(e)
        _st.stop()


FILE_SUFFIXES: dict[str, _t.Callable[[str], _pd.DataFrame]] = {
    "csv": _pd.read_csv,
    "json": _pd.read_json,
    "parq": _pd.read_parquet,
    "parquet": _pd.read_parquet,
    "feather": _pd.read_feather,
    "ftr": _pd.read_feather,
    "orc": _pd.read_orc,
}
"""Permitted file types and their corresponded read functions."""

COMPRESSION_SUFFIXES: tuple[str, ...] = "zip", "gzip", "bz2", "zstd", "xz", "tar"
"""Permitted compression types."""


def _make_valid_suffixes() -> tuple[str, ...]:
    all_types: list[str] = []
    for compression_type in COMPRESSION_SUFFIXES:
        all_types.extend(f"{file_type}.{compression_type}" for file_type in FILE_SUFFIXES)
    return *FILE_SUFFIXES, *all_types


VALID_SUFFIXES = _make_valid_suffixes()
"""Permitted suffixes for uploaded files and configured datasets."""
del _make_valid_suffixes


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
    _st.dataframe(samples.reset_index(), hide_index=False, use_container_width=True)
    _st.write(f"Showing `{len(samples)}/{len(duplicated_df)}` duplicated rows. Original `shape={df.shape}`.")

    _st.stop()


_UNAGGREGATED_DATA_MESSAGE = """
Found `{n_duplicated}` duplicate values in `index='{index}'`.

While the `time-split` [package](https://time-split.readthedocs.io/) is designed primarily with unaggregated data in
mind, this application requires pre-aggregated data for performance reasons.
"""
