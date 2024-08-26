from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from typing import Collection, Any, Iterable

import pandas as pd
import streamlit as st

from time_split._compat import fmt_sec
from time_fold_explorer._logging import log_perf
from time_fold_explorer import config
from time_fold_explorer.widgets.data.load import read_file
from time_fold_explorer.widgets.types import DatasetConfig, Dataset, QueryParams


class DatasetWidget:
    """Prepackaged datasets.

    Args:
        configs: Available datasets.
    """

    def __init__(
        self,
        configs: Collection[DatasetConfig] | str | None = None,
    ) -> None:
        if configs is None:
            configs = DatasetConfig.load_if_exists()
        elif isinstance(configs, str):
            configs = DatasetConfig.load(configs)
        self.configs = configs or ()

    def select(self) -> tuple[pd.DataFrame, dict[str, str], str]:
        """Let the user select an included dataset."""
        datasets = self.load_datasets()
        frames = {ds.label: ds for ds in datasets}

        options = [*frames]
        index = 0 if (query_dataset := QueryParams.get().data) is None else _handle_query_arg(query_dataset, options)
        selection = st.radio(
            "select-dataset",
            options,
            index=index,
            captions=[ds.description.partition("\n")[0] for ds in datasets],
            horizontal=True,
            label_visibility="collapsed",
        )
        assert selection is not None

        dataset = frames[selection]

        if dataset.description.partition("\n")[2]:
            st.subheader(dataset.label, divider=True)
            st.write(dataset.description)

        return dataset.df, dataset.aggregations, dataset.label

    def load_datasets(self) -> list[Dataset]:
        """Load configured datasets."""
        return load_datasets(self.configs)

    @property
    def has_data(self) -> bool:
        return bool(self.configs)

    def __post_init__(self) -> None:
        cfgs: dict[str, DatasetConfig] = {}
        for cfg in self.configs:
            label = cfg.label
            if label in cfgs:
                msg = f"Duplicated {label=}\n    old={cfgs[label]}\n    new={cfg}"
                raise ValueError(msg)
            else:
                cfgs[label] = cfg


@st.cache_data(ttl=config.DATASET_CACHE_TTL)
def load_datasets(cfgs: Collection[DatasetConfig]) -> list[Dataset]:
    """Load datasets from configuration."""
    start = perf_counter()

    max_workers = 2
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="load-dataset") as executor:
        datasets = list(executor.map(_load_dataset, cfgs))

    seconds = perf_counter() - start
    log_perf(
        f"Loaded {len(cfgs)} datasets using {max_workers} worker threads in {fmt_sec(seconds)}",
        df={ds.label: ds.df for ds in datasets},
        seconds=seconds,
        extra={},
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
