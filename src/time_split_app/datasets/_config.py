import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

USE_ORIGINAL_INDEX = "__INDEX__"
"""Special value indicating that the dataset already has a datetime-like index."""


@dataclass(frozen=True, kw_only=True)
class DatasetConfig:
    """Configuration type for datasets on disk."""

    label: str
    """Name shown in the UI (Markdown).

    When using :func:`load_dataset_configs`, this will default to the section header.
    """

    path: str
    """Dataset path. May be prefixed for remote paths, e.g. ``s3://my-bucket/my-data.csv.zip``."""

    index: str = USE_ORIGINAL_INDEX
    """Index column. Must be datetime-like.

    Use ``'__INDEX__'`` (default) if the dataset already has a suitable index.
    """

    aggregations: dict[str, str] = field(default_factory=dict)
    """Default column aggregations known to pandas, e.g. ``{'my-column': 'max'}``. Users may override these in the UI."""

    description: str = ""
    """A longer dataset description for the UI (Markdown). The first row will be used as a summary."""

    read_function_kwargs: dict[str, Any] = field(default_factory=dict)
    """Keyword arguments for the read function derived based on `path`, e.g. :func:`pandas.read_csv`.

    The `path` is always passed as a positional argument in the first position.
    """


def load_dataset_configs(file: str | Path) -> list[DatasetConfig]:
    """Read dataset configs from file.

    Returns one :class:`.DatasetConfig` object per top-level section in `file`.

    Args:
        file: Path to a TOML file.

    Returns:
        A list of dataset configs
    """
    labels: dict[str, DatasetConfig] = {}
    rv: list[DatasetConfig] = []
    config: dict[str, Any]
    for section, config in _read_toml(file).items():
        config.setdefault("label", section)

        try:
            cfg = _create(config, seen=labels)
        except Exception as e:
            e.add_note(f"{section=}")
            e.add_note(f"{config=}")
            e.add_note(f"{file=}")
            raise

        rv.append(cfg)

    return rv


def _read_toml(file: str | Path) -> dict[str, Any]:
    file = str(file)

    try:
        import fsspec  # type: ignore[import-untyped]

        with fsspec.open(file, "rb") as f:
            return tomllib.load(f)
    except ImportError as e:
        if "://" in file:
            msg = f"Cannot load dataset config {file=} without package '{e.name}'."
            raise ImportError(msg) from e

    with Path(file).open("rb") as f:
        return tomllib.load(f)


def _create(raw: dict[str, Any], *, seen: dict[str, DatasetConfig]) -> DatasetConfig:
    from ._read_fn import get_pandas_read_function

    config = DatasetConfig(**raw)

    label = config.label
    if previous := seen.get(label):
        msg = f"Duplicate label: {label!r}. Current: {config!r}, {previous=}."
        error = ValueError(msg)
        error.add_note(f"current={config!r}")
        error.add_note(f"previous={previous!r}")
        raise error

    get_pandas_read_function(config.path)

    seen[label] = config

    return config
