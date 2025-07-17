import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rics.paths import AnyPath, any_path_to_path

USE_ORIGINAL_INDEX = "__INDEX__"
"""Special value indicating that the dataset already has a datetime-like index."""


@dataclass(frozen=True, kw_only=True)
class DatasetConfig:
    """Configuration type for datasets on disk."""

    label: str
    """Name shown in the UI (Markdown).

    When using :func:`load_dataset_configs`, this will default to do the section header.
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


def load_dataset_configs(file: AnyPath) -> list[DatasetConfig]:
    """Read dataset configs from file.

    Returns one :class:`.DatasetConfig` object per top-level section in `file`.

    Args:
        file: Path to a TOML file.

    Returns:
        A list of dataset configs
    """

    def check_config(path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError

    with any_path_to_path(file, postprocessor=check_config).open("rb") as f:
        raw = tomllib.load(f)

    labels: dict[str, DatasetConfig] = {}
    rv: list[DatasetConfig] = []
    config: dict[str, Any]
    for section, config in raw.items():
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
