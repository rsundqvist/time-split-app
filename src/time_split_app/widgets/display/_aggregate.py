import logging
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from typing import Collection, Callable

import pandas as pd
import streamlit as st
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
from rics.misc import get_by_full_name
from rics.strings import format_seconds
from time_split._frontend._to_string import stringify
from time_split.integration.pandas import split_pandas
from time_split.types import DatetimeIndexSplitterKwargs

from time_split_app import config


from time_split_app.formatting import select_cmap, select_formatters


class AggregationWidget:
    """Aggregations per fold and dataset.

    Args:
        aggregations: Aggregation options.
        odd_row_props: Properties for oddly-numbered fold rows in the output table.
        default: Default aggregation per columns.
        plot_fn: Function used to plot folds.
    """

    def __init__(
        self,
        aggregations: Collection[str] = ("min", "mean", "max", "sum"),
        odd_row_props: str = "background-color: rgba(100, 100, 100, 0.5)",
        default: str = "mean",
        plot_fn: Callable[[pd.DataFrame, dict[str, str]], None] | None = None,
    ) -> None:
        self._agg = tuple(aggregations)
        self._props = str(odd_row_props)
        self._default = self._agg.index(default)
        if plot_fn is None:
            plot_fn = _get_plot_fn()
        self._plot_fn = plot_fn

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
                start = perf_counter()
                self._plot_fn(agg, aggregations | reserved)

                seconds = perf_counter() - start
                msg = f"Created `aggregation` figure for `{len(folds)}` folds in `{format_seconds(seconds)}`."
                log_perf(
                    msg,
                    df,
                    seconds,
                    extra={"figure": "aggregated-columns", "n_folds": len(folds)},
                )
                st.caption(msg)
            else:
                st.warning(f"{config.PLOT_AGGREGATIONS_PER_FOLD=}", icon="⚠️")
                st.write("See the `❔ About` tab to update the configuration. Don't forget to click `Apply`!")

    @classmethod
    def plot_matplotlib(cls, df: pd.DataFrame, aggregations: dict[str, str]) -> None:
        start = perf_counter()
        st.subheader("Plot", divider="rainbow")

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

        tabs = st.tabs([c for c in columns])

        for (i, column), future in zip(enumerate(columns), futures, strict=True):
            pbar.progress(p, f"Plotting column `{i + 1}/{len(columns)}`: `{column!r}`")

            fig = future.result()
            with tabs[i]:
                st.pyplot(fig, clear_figure=True, dpi=config.FIGURE_DPI)

            p += 1 / len(columns)
            pbar.progress(p)

        seconds = perf_counter() - start
        pbar.progress(
            p,
            f"Finished plotting `{len(folds)}` folds and `{len(columns)}` columns in `{int(1000 * seconds)}` ms.",
        )

    @classmethod
    def plot_seaborn(cls, df: pd.DataFrame, aggregations: dict[str, str]) -> None:  # Not used
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

    @classmethod
    def plot_plotly(cls, df: pd.DataFrame, aggregations: dict[str, str]) -> None:
        st.subheader("Plot", divider="rainbow")

        df.to_pickle("df.pkl")
        with open("aggregations.json", "w") as f:
            f.write(str(aggregations).replace("'", '"'))

        fig = df.plot(backend="plotly")
        st.plotly_chart(fig, width="stretch")

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

        agg, num_folds = self._aggregate(df, split_kwargs, aggregations)

        left, right = st.columns([20, 3])
        with right, st.container(border=True):
            st.subheader("Table style", divider=True)
            table = self._format_table(agg)
        with left:
            st.dataframe(table)

        # Record performance
        n_folds = agg.index.get_level_values("fold").nunique()
        seconds = perf_counter() - start
        msg = f"Aggregated datasets in {n_folds} folds for data of `shape={df.shape}` in `{format_seconds(seconds)}`."
        log_perf(msg, df, seconds, extra={"n_folds": n_folds, "aggregations": aggregations}, level=logging.DEBUG)
        st.caption(msg)

        return agg

    @classmethod
    def _aggregate(
        cls,
        df: pd.DataFrame,
        split_kwargs: DatetimeIndexSplitterKwargs,
        aggregations: dict[str, str],
    ) -> tuple[pd.DataFrame, int]:
        frames: dict[tuple[int, pd.Timestamp], pd.DataFrame] = {}

        for fold in split_pandas(df, **split_kwargs):
            data = fold.data.agg(aggregations).rename("Data")
            future_data = fold.future_data.agg(aggregations).rename("Future data")

            # TODO Fixa dessa! Ska matcha "Row counts" i figur!!
            agg = pd.concat([data, future_data], axis=1)
            agg.loc["n_rows", [data.name, future_data.name]] = [len(fold.data), len(fold.future_data)]
            agg.loc["n_hours", [data.name, future_data.name]] = [_hours(fold.data), _hours(fold.future_data)]

            frames[(len(frames), fold.training_date)] = agg.T

        return pd.concat(frames, names=["fold_no", "fold", "dataset"]), len(frames)

    @classmethod
    def _format_table(cls, df: pd.DataFrame) -> "pd.io.formats.style.Styler":
        datasets = df.index.get_level_values("dataset").unique()

        column_formats = select_formatters("AggregationWidget", df.dtypes)
        column_formats["n_rows"] = "{:.0f}"

        formatters = {}
        for column, fmt in column_formats.items():
            for dataset in datasets:
                formatters[(column, dataset)] = fmt

        df = df.unstack(level="dataset")
        if st.toggle("Pretty folds", value=True, help="Uncheck to display timestamps."):
            index = df.index.get_level_values("fold").map(lambda ts: f"{stringify(ts)} ({ts.day_name()})")
            df.index = df.index.set_levels(index, level="fold")

        if st.toggle(
            "Dataset out",
            value=True,
            help="Use the dataset (e.g. `Future data`) instead of the column itself (e.g. `n_rows`) as the outer level in the table.",
        ):
            df = df.reorder_levels([1, 0], axis="columns")
            formatters = {(dataset, column): fmt for (column, dataset), fmt in formatters.items()}

        df = df.sort_index(axis="columns")

        styler = df.style
        styler = styler.format(formatters)

        if cmap := select_cmap("AggregationWidget"):
            styler = styler.background_gradient(cmap)

        return styler

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


def _hours(s: pd.Series) -> float:
    timedelta = s.index.max() - s.index.min()
    seconds = float(timedelta.total_seconds())
    hours = seconds / (60 * 60)
    return hours


@st.cache_resource
def _get_plot_fn() -> Callable[[pd.DataFrame, dict[str, str]], None]:
    if value := config.PLOT_RAW_TIMESERIES_FN:
        LOGGER.info(f"Using {config.PLOT_RAW_TIMESERIES_FN=}.")
        return get_by_full_name(value, default_module=__package__)

    try:
        import plotly.express as backend

        LOGGER.info(f"Using {AggregationWidget.plot_plotly.__qualname__} to plot raw timeseries.")
        return AggregationWidget.plot_plotly
    except ImportError:
        LOGGER.info(f"Using {AggregationWidget.plot_matplotlib.__qualname__} to plot raw timeseries.")
        return AggregationWidget.plot_matplotlib


from time_split_app._logging import log_perf, LOGGER
