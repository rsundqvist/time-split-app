from collections.abc import Callable, Mapping

import pandas as pd

FILE_SUFFIXES: Mapping[str, Callable[[str], pd.DataFrame]] = {
    "csv": pd.read_csv,
    "json": pd.read_json,
    "parq": pd.read_parquet,
    "parquet": pd.read_parquet,
    "feather": pd.read_feather,
    "ftr": pd.read_feather,
    "orc": pd.read_orc,
}
"""Permitted file types and their corresponded read functions."""

COMPRESSION_SUFFIXES: tuple[str, ...] = "zip", "gzip", "bz2", "zstd", "xz", "tar"
"""Permitted compression types."""


def get_pandas_read_function(path: str) -> Callable[[str], pd.DataFrame]:
    """Derive a pandas read function from `path`.

    Args:
        path: Path to a frame.

    Returns:
        A callable ``(path) -> pd.DataFrame``.

    Raises:
        ValueError: If no suitable function could be found.
    """
    parts = path.rsplit(".", maxsplit=3)

    is_compressed = path.endswith(COMPRESSION_SUFFIXES)
    file_suffix = parts[-2] if is_compressed else parts[-1]
    read_fn = FILE_SUFFIXES.get(file_suffix)
    if read_fn:
        return read_fn

    msg = f"Could not derive a read function; suffix={file_suffix!r} (from {path=}) not in {(*FILE_SUFFIXES,)}."
    raise ValueError(msg)
