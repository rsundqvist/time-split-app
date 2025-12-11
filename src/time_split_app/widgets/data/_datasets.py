from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, UTC
from time import perf_counter
from typing import Any, Iterable

import pandas as pd
import streamlit as st
from rics.strings import format_seconds
from time_split_app.datasets import Dataset, DatasetConfig, load_dataset

from time_split_app import config
from time_split_app._logging import log_perf, LOGGER
from time_split_app.widgets.types import QueryParams

from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx, ScriptRunContext
from time_split_app.datasets import load_dataset_configs as load_dataset_configs_from_path


class DatasetWidget:
    """Prepackaged datasets."""

    def __init__(self) -> None:
        self._sizes: dict[str, int] = {}
        self._digest = b""

    def select(self) -> tuple[pd.DataFrame, dict[str, str], str]:
        """Let the user select an included dataset."""
        datasets = self.load_datasets()
        frames = {ds.label: ds for ds in datasets}

        options = [*frames]
        option_summaries = [ds.description.partition("\n")[0] for ds in datasets]
        query_dataset = QueryParams.get().data
        index = _handle_query_arg(query_dataset, options) if isinstance(query_dataset, str) else 0
        kwargs: dict[str, Any] = {
            "label": "Select dataset.",
            "options": options,
            "index": index,
            "help": f"# Dataset options ({len(options)}):\n\n"
            + "".join(f"\n* {label}: {summary}" for label, summary in zip(options, option_summaries))
            + f"\n\nDatasets are refreshed every `{config.DATASET_CACHE_TTL // 60:_d}` minutes. Datasets are forcibly"
            f" reloaded if the config file (`'{config.DATASETS_CONFIG_PATH}'`) is changed.",
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

    def load_datasets(self) -> list[Dataset]:
        """Load configured datasets."""
        configs, configs_loaded, digest = load_dataset_configs()

        if configs:
            datasets, datasets_loaded = load_datasets(digest, configs)
        else:
            datasets_loaded = None
            datasets = []
        LOGGER.debug("Dataset load timestamp: configs=%r, datasets=%r", configs_loaded, datasets_loaded)

        sizes = {ds.label: len(ds.df) for ds in datasets}
        if self._sizes != sizes or self._digest != digest:
            sha256 = f"0x{digest.hex()}"
            extra = {"sha256": sha256, "sizes": sizes}
            LOGGER.info(f"Loaded {len(sizes)} datasets with {sizes=} and config digest (sha256)={sha256}.", extra=extra)
            self._digest = digest
            self._sizes = sizes

        if config.DEBUG:
            rows = [
                f"{config.DATASETS_CONFIG_PATH=}",
                f"{configs_loaded=}",
                f"{datasets_loaded=}",
            ]
            st.code("\n".join(rows))

        return datasets

    @property
    def has_data(self) -> bool:
        return self.size > 0

    @property
    def size(self) -> int:
        configs, _, _ = load_dataset_configs()
        return len(configs) if configs else 0


@st.cache_resource(ttl=config.DATASET_CONFIG_CACHE_TTL, max_entries=1)
def load_dataset_configs() -> tuple[tuple[DatasetConfig, ...] | None, datetime, bytes]:
    """Load configuration file."""
    now = datetime.now(UTC)

    path = config.DATASETS_CONFIG_PATH
    if not path:
        return None, now, b""

    LOGGER.debug("Loading datasets from path=%r", path, extra={"path": path})
    try:
        digest, configs = load_dataset_configs_from_path(path, return_digest=True)
    except Exception as e:
        if config.REQUIRE_DATASETS:
            from os import _exit as force_exit

            LOGGER.exception(f"Failed to load dataset config {path=}. Refusing to start since REQUIRE_DATASETS=True.")
            force_exit(52)  # regular exit will not halt the underlying server.

        if isinstance(e, FileNotFoundError):
            LOGGER.info(
                f"Datasets file DATASETS_CONFIG_PATH={path} does not exist. No datasets will be loaded.",
                extra={"path": path},
            )
            config.DATASETS_CONFIG_PATH = ""
        else:
            LOGGER.warning(
                f"Failed to read dataset config {path=}: {e!r}.",
                exc_info=True,
                extra={"path": path},
            )

        return None, now, b""

    sha256 = f"0x{digest.hex()}"
    extra = {"sha256": sha256, "path": path, "count": len(configs)}
    LOGGER.info(f"Loaded {len(configs)} configs from {path=} with digest (sha256)={sha256}.", extra=extra)
    return (*configs,), now, digest


@st.cache_resource(ttl=config.DATASET_CACHE_TTL, max_entries=1)
def load_datasets(digest: bytes, _cfgs: tuple[DatasetConfig, ...]) -> tuple[list[Dataset], datetime]:
    """Load datasets from configuration."""
    start = perf_counter()

    now = datetime.now(UTC)

    script_run_ctx = get_script_run_ctx()

    max_workers = 2
    with ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix="load-dataset",
        initializer=_add_script_run_ctx,
        initargs=(script_run_ctx,),
    ) as executor:
        datasets = list(executor.map(_load_dataset, _cfgs))

    seconds = perf_counter() - start
    log_perf(
        f"Loaded {len(_cfgs)} datasets using {max_workers} threads in {format_seconds(seconds)}.",
        df={ds.label: ds.df for ds in datasets},
        seconds=seconds,
        extra={"sha256": f"0x{digest.hex()}"},
    )
    return datasets, now


def _add_script_run_ctx(ctx: ScriptRunContext | None) -> None:
    add_script_run_ctx(ctx=ctx)


def _load_dataset(cfg: DatasetConfig) -> Dataset:
    start = perf_counter()

    dataset = load_dataset(cfg)

    seconds = perf_counter() - start
    log_perf(
        f"Loaded dataset '{cfg.path}' in {format_seconds(seconds)}",
        dataset.df,
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
