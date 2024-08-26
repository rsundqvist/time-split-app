from pprint import pformat
from typing import Any

import pandas as pd
import streamlit as st
from time_split._compat import fmt_sec
from time_split.support import create_explorer_link
from time_split.types import DatetimeIndexSplitterKwargs, DatetimeSplits, DatetimeTypes

from time_fold_explorer import config
from time_fold_explorer.widgets.display import CodeWidget, FoldOverviewWidget, PlotFoldsWidget
from time_fold_explorer.widgets.types import QueryParams


def primary(
    *,
    df: pd.DataFrame,
    plot_folds_widget: PlotFoldsWidget,
    split_kwargs: DatetimeIndexSplitterKwargs,
    limits: tuple[DatetimeTypes, DatetimeTypes],
    dataset: str | None,
    # Overview params
    fold_overview_widget: FoldOverviewWidget,
    splits: DatetimeSplits,
    all_splits: DatetimeSplits,
) -> None:
    st.header("Folds", divider="rainbow")

    with st.container(border=True):
        left, right = st.columns([20, 4])
        with right, st.container(border=True):
            st.subheader("Plot preferences", divider=True)
            plot_kwargs = plot_folds_widget.select()
        with left:
            plot_folds_widget.plot(split_kwargs, df, **plot_kwargs)

    with st.container(border=True):
        left, right = st.columns([20, 4])
        with left:
            st.subheader(
                "Code snippets",
                divider="rainbow",
                help=(
                    "The [integration](https://time-split.readthedocs.io/en/stable/generated/time_split.integration.html)"
                    " modules accept the same parameters as `time_fold.split()`."
                ),
            )
        with right, st.popover("🤝 Show permalink", use_container_width=True):
            show_permalink(
                split_kwargs=split_kwargs,
                plot_kwargs=plot_kwargs,
                limits=limits if dataset is None else dataset,
            )

        left, mid, right = st.columns([10, 10, 4])

        with right:
            with st.container(border=True):
                st.subheader(
                    "Type preferences",
                    divider=True,
                    help="The `time-split` package uses Pandas types internally. May not work for `📝 Free form` input.",
                )
                code_widget = CodeWidget.select()

            st.write(
                """
                * Click [here](https://time-split.readthedocs.io/en/stable/generated/time_split.html#time_split.split) for `split()` docs.
                * Click [here](https://time-split.readthedocs.io/en/stable/generated/time_split.html#time_split.plot) for `plot()` docs.
                """
            )

            used, avail = fold_overview_widget.get_data_utilization(splits, limits)
            st.caption(
                f"Using `{fmt_sec(used)}` of `{fmt_sec(avail)}` (`{used / avail :.1%}`) of the available data range."
            )

        with left:
            code_widget.show_split_code(split_kwargs, limits=limits)
            fold_overview_widget.show_overview(splits, all_splits=all_splits)
        with mid:
            code_widget.show_plot_code(split_kwargs, plot_kwargs=plot_kwargs, limits=limits)


def show_permalink(
    *,
    split_kwargs: DatetimeIndexSplitterKwargs,
    plot_kwargs: dict[str, Any],
    limits: tuple[DatetimeTypes, DatetimeTypes] | str,
) -> None:
    permalink_kwargs = {**split_kwargs, **plot_kwargs, "data": limits}
    permalink_kwargs.pop("bar_labels")  # Not supported

    host = config.PERMALINK_BASE_URL
    if host == "":
        host = "http://localhost:8501"
        st.warning(f"May not be accurate; {config.PERMALINK_BASE_URL=} not set.", icon="⚠️")

    link = create_explorer_link(host, **permalink_kwargs)
    st.header("Share this link", divider=True)
    with st.container(border=True):
        st.write(f"[{link}]({link})")

    convert = CodeWidget("string").convert

    st.header(
        "Parameters",
        divider=True,
        help="Input parameters are extracted from the URL in the address bar of your browser."
        " Output parameters are used to generate the new link above.",
    )
    with st.container(border=True):
        left, right = st.columns(2)
        with left:
            st.write("Input parameters.")
            st.code(pformat(convert(QueryParams.get().to_dict(filter=False)), width=35))

        with right:
            st.write("Output parameters.")
            st.code(pformat(convert(permalink_kwargs.copy()), width=35))
        doc = "https://time-split.readthedocs.io/en/stable/generated/time_split.support.html#time_split.support.create_explorer_link"
        st.caption(
            f"Parameters may be [converted]({doc}) to equivalent values. "
            "Note that `data` is called `available` by core library."
        )
