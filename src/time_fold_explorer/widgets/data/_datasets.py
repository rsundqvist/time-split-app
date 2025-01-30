import hashlib
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from typing import Any, Iterable

import pandas as pd
import streamlit as st
from time_split._compat import fmt_sec

from time_fold_explorer import config
from time_fold_explorer._logging import log_perf
from time_fold_explorer.widgets.data.load import read_file
from time_fold_explorer.widgets.types import DatasetConfig, Dataset, QueryParams


class DatasetWidget:
    """Prepackaged datasets."""

    def select(self) -> tuple[pd.DataFrame, dict[str, str], str]:
        """Let the user select an included dataset."""
        datasets = self.load_datasets()
        frames = {ds.label: ds for ds in datasets}

        options = [*frames]
        option_summaries = [ds.description.partition("\n")[0] for ds in datasets]
        index = 0 if (query_dataset := QueryParams.get().data) is None else _handle_query_arg(query_dataset, options)
        kwargs: dict[str, Any] = {
            "label": "Select dataset",
            "options": options,
            "index": index,
            "help": f"Dataset options ({len(options)}):"
            + "".join(f"\n * {label}: {summary}" for label, summary in zip(options, option_summaries))
            + f"\n\nDatasets are reloaded every `{config.DATASET_CACHE_TTL}` seconds.",
        }

        if len(options) <= config.DATASET_RADIO_LIMIT:
            selection = st.radio(
                **kwargs,
                horizontal=True,
                captions=option_summaries,
            )
        else:
            selection = st.selectbox(
                **kwargs,
                format_func=QueryParams.normalize_dataset,
            )
        assert selection is not None

        dataset = frames[selection]

        if dataset.description.partition("\n")[2]:
            st.subheader(dataset.label, divider=True)
            st.write(dataset.description)

        return dataset.df, dataset.aggregations, dataset.label

    @staticmethod
    def load_datasets() -> list[Dataset]:
        """Load configured datasets."""
        configs = load_dataset_configs()

        if configs:
            sha256 = hashlib.new("sha256", str(configs).encode(), usedforsecurity=False).hexdigest()
            return load_datasets(sha256, configs)
        else:
            return []

    @property
    def has_data(self) -> bool:
        return self.size > 0

    @property
    def size(self) -> int:
        configs = load_dataset_configs()
        return len(configs) if configs else 0


@st.cache_data(ttl=config.DATASET_CONFIG_CACHE_TTL, max_entries=1)
def load_dataset_configs() -> tuple[DatasetConfig, ...] | None:
    """Load configuration file."""
    configs = DatasetConfig.load_if_exists()

    if configs:
        _check_duplicates(configs)

    return configs


def _check_duplicates(configs: tuple[DatasetConfig, ...]) -> None:
    seen: dict[str, DatasetConfig] = {}
    for cfg in configs:
        label = cfg.label
        if label in seen:
            msg = f"Duplicated {label=}\n    old={seen[label]}\n    new={cfg}"
            raise ValueError(msg)
        else:
            seen[label] = cfg


@st.cache_data(ttl=config.DATASET_CACHE_TTL, max_entries=1)
def load_datasets(sha256: str, _cfgs: tuple[DatasetConfig, ...]) -> list[Dataset]:
    """Load datasets from configuration."""
    start = perf_counter()

    max_workers = 2
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="load-dataset") as executor:
        datasets = list(executor.map(_load_dataset, _cfgs))

    seconds = perf_counter() - start
    log_perf(
        f"Loaded {len(_cfgs)} datasets using {max_workers} threads in {fmt_sec(seconds)}",
        df={ds.label: ds.df for ds in datasets},
        seconds=seconds,
        extra={"sha256": f"0x{sha256}"},
    )
    return datasets


def _load_dataset(cfg: DatasetConfig) -> Dataset:
    start = perf_counter()

    df = read_file(cfg.path, **cfg.read_function_kwargs)

    df[cfg.index] = pd.to_datetime(df[cfg.index].astype(str))
    df = df.set_index(cfg.index)

    dataset = Dataset.from_config(df, cfg)

    seconds = perf_counter() - start
    log_perf(
        f"Loaded dataset '{cfg.path}' in {fmt_sec(seconds)}",
        df,
        seconds,
        extra={"config.path": cfg.path, "config.label": cfg.label, "config.kwargs": cfg.read_function_kwargs},
    )
    return dataset


def _handle_query_arg(query: int | str | tuple[Any, Any], options: Iterable[str]) -> int:
    if isinstance(query, int):
        return query
    if isinstance(query, tuple):
        return 0  # User switched to datasets after lading with a generated range URL.

    normalized = [QueryParams.normalize_dataset(opt) for opt in options]
    query = QueryParams.normalize_dataset(query)
    return normalized.index(query)
