import logging
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from typing import Collection

import numpy as np
import pandas as pd
import streamlit as st
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from time_split._compat import fmt_sec
from time_split._frontend._to_string import stringify
from time_split.integration.pandas import split_pandas
from time_fold_explorer import config
from time_fold_explorer._logging import log_perf
from time_split.types import DatetimeIndexSplitterKwargs


class AggregationWidget:
    """Aggregations per fold and dataset.

    Args:
        aggregations: Aggregation options.
        odd_row_props: Properties for oddly-numbered fold rows in the output table.
        default: Default aggregation
    """

    def __init__(
        self,
        aggregations: Collection[str] = ("min", "mean", "max", "sum"),
        odd_row_props: str = "background-color: rgba(100, 100, 100, 0.5)",
        default: str = "mean",
    ) -> None:
        self._agg = tuple(aggregations)
        self._props = str(odd_row_props)
        self._default = self._agg.index(default)

    def plot_aggregations(
        self,
        df: pd.DataFrame,
        *,
        split_kwargs: DatetimeIndexSplitterKwargs,
        aggregations: dict[str, str],
    ) -> None:
        reserved = {"n_rows": "sum", "n_hours": "sum"}

        if forbidden := set(reserved).intersection(aggregations):
            raise ValueError(f"Found {len(forbidden)} reserved keys {sorted(aggregations)} in {aggregations=}")

        with st.spinner("Aggregating data..."):
            st.subheader("Aggregated folds", divider="rainbow")

            # TODO frame agg + figure in separate calls
            agg = self.aggregate(df, split_kwargs=split_kwargs, aggregations=aggregations)

            if config.PLOT_AGGREGATIONS_PER_FOLD:
                self._plot(agg, aggregations | reserved)
            else:
                st.warning(f"{config.PLOT_AGGREGATIONS_PER_FOLD=}", icon="⚠️")
                st.write("See the `❔ About` tab to update the configuration. Don't forget to click `Apply`!")

    @staticmethod
    def _plot(df: pd.DataFrame, aggregations: dict[str, str]) -> None:
        start = perf_counter()

        columns = df.columns
        folds = df.pivot_table(index="fold", columns="dataset", aggfunc=aggregations, sort=False)
        pbar, p = st.progress(0.0), 0.0

        def plot(column: str) -> Figure:
            fig, ax = plt.subplots()
            folds[column].plot(ax=ax, marker="o")
            ax.set_title(f"${aggregations[column]}({column!r})$".replace("_", "\\_"))
            ax.set_xlabel("")
            ax.set_xticks(folds.index)
            fig.autofmt_xdate(ha="center", rotation=15)
            return fig

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(plot, column) for column in columns]

        for (i, column), future in zip(enumerate(columns), futures, strict=True):
            pbar.progress(p, f"Plotting column `{i + 1}/{len(columns)}`: `{column!r}`")

            fig = future.result()
            st.pyplot(fig, clear_figure=True, dpi=config.FIGURE_DPI)

            p += 1 / len(columns)
            pbar.progress(p)
        seconds = perf_counter() - start

        pbar.progress(
            p,
            f"Finished plotting `{len(folds)}` folds and `{len(columns)}` columns in `{int(1000 * seconds)}` ms.",
        )

        msg = f"Created `aggregation` figure for data of `shape={folds.shape}` in `{fmt_sec(seconds)}`."
        log_perf(
            msg,
            df,
            seconds,
            extra={"figure": "aggregated-columns", "n_folds": len(folds)},
        )
        st.caption(msg)

    @staticmethod
    def _plot_seaborn(df: pd.DataFrame, aggregations: dict[str, str]) -> None:  # Not used
        import seaborn as sns

        melt = df.melt(ignore_index=False).reset_index()
        melt["dataset"] = melt["dataset"].astype("category")
        melt["variable"] = melt["variable"].map(lambda c: f"${aggregations[c]}({c})$".replace("_", "\\\\_"))

        g = sns.FacetGrid(
            melt,
            height=4,
            aspect=4,
            row="variable",
            hue="dataset",
            sharex=True,
            sharey=False,
        )
        g.map_dataframe(sns.lineplot, x="fold", y="value", marker="o")

        g.set_ylabels("")
        g.set_titles(row_template="{row_name}")
        g.figure.autofmt_xdate(ha="center", rotation=15)
        g.add_legend(loc="upper left", title="", bbox_to_anchor=(0, 1.01, 0, 0))

        st.pyplot(g.figure, clear_figure=True, dpi=config.FIGURE_DPI)

    def aggregate(
        self,
        df: pd.DataFrame,
        *,
        split_kwargs: DatetimeIndexSplitterKwargs,
        aggregations: dict[str, str],
    ) -> pd.DataFrame:
        """Aggregate datasets resulting from a split of `df`.

        Args:
            df: A dataframe. Must have a ``DatetimeIndex``.
            split_kwargs: Keyword arguments for :func:`time_split.split`.
            aggregations: A dict ``{column: agg_fn}``.

        Returns:
            A frame with the same columns as `df` and a `MultiIndex` with levels
            ``fold_no[int], fold[pd.Timestamp], dataset[str]``.
        """
        start = perf_counter()

        agg = self._aggregate(df, split_kwargs, aggregations)

        pretty = agg.reset_index()
        pretty["fold"] = pretty["fold"].map(lambda ts: f"{stringify(ts)} ({ts.day_name()})")
        st.dataframe(
            pretty.style.apply(
                lambda row: np.where([row["fold_no"] % 2 == 1] * len(row), self._props, ""),
                axis=1,
            ),
            use_container_width=True,
        )

        # Record performance
        n_folds = agg.index.get_level_values("fold").nunique()
        seconds = perf_counter() - start
        msg = f"Aggregated datasets in {n_folds} folds for data of `shape={df.shape}` in `{fmt_sec(seconds)}`."
        log_perf(msg, df, seconds, extra={"n_folds": n_folds, "aggregations": aggregations}, level=logging.DEBUG)
        st.caption(msg)

        return agg

    @classmethod
    def _aggregate(
        cls,
        df: pd.DataFrame,
        split_kwargs: DatetimeIndexSplitterKwargs,
        aggregations: dict[str, str],
    ) -> pd.DataFrame:
        frames: dict[tuple[int, pd.Timestamp], pd.DataFrame] = {}

        for fold in split_pandas(df, **split_kwargs):
            data = fold.data.agg(aggregations).rename("Data")
            future_data = fold.future_data.agg(aggregations).rename("Future data")

            agg = pd.concat([data, future_data], axis=1)
            agg.loc["n_rows", [data.name, future_data.name]] = list(map(len, (fold.data, fold.future_data)))
            agg.loc["n_hours", [data.name, future_data.name]] = list(map(_get_timedelta, (fold.data, fold.future_data)))

            frames[(len(frames), fold.training_date)] = agg.T

        return pd.concat(frames, names=["fold_no", "fold", "dataset"])

    def configure(self, df: pd.DataFrame, defaults: dict[str, str] | None = None) -> dict[str, str]:
        with st.container(border=True):
            st.subheader("Column configuration", divider="red")
            st.caption("Select aggregations for the `📈 Aggregations per fold` tab.")
            return self._select_aggregation(df, {} if defaults is None else defaults)

    def _select_aggregation(self, df: pd.DataFrame, defaults: dict[str, str]) -> dict[str, str]:
        tabs = st.tabs(df.columns.to_list())

        dtypes = df.dtypes

        options = self._agg
        if missing := set(defaults.values()).difference(options):
            options += tuple(missing)

        aggregations = {}
        for column, tab in zip(df.columns, tabs, strict=True):
            index = options.index(default) if (default := defaults.get(column)) else self._default
            agg = tab.radio(
                f"Select fold-level aggregation for `{column}` with `dtype={dtypes[column]}`.",
                options,
                index=index,
                horizontal=True,
                key=f"{column}-aggregation",
            )
            assert agg is not None
            aggregations[column] = agg

        return aggregations


def _get_timedelta(s: pd.Series) -> pd.Timedelta:
    return (s.index.max() - s.index.min()).total_seconds() / 60
