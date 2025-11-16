from pprint import pformat
from typing import Any

import pandas as pd
import streamlit as st
from rics.strings import format_seconds
from streamlit.delta_generator import DeltaGenerator
from time_split._frontend._to_string import _PrettyTimestamp
from time_split.app import create_explorer_link
from time_split.types import DatetimeIndexSplitterKwargs, DatetimeSplitBounds, DatetimeSplits, DatetimeTypes

from time_split_app import config
from time_split_app._select_link_impl_from_entrypoint import get_user_link_fn
from time_split_app.widgets.display import CodeWidget, FoldOverviewWidget, PlotFoldsWidget
from time_split_app.widgets.types import QueryParams


def primary(
    *,
    df: pd.DataFrame,
    plot_folds_widget: PlotFoldsWidget,
    split_kwargs: DatetimeIndexSplitterKwargs,
    limits: tuple[DatetimeTypes, DatetimeTypes],
    dataset: str | bytes | None,
    # Overview params
    fold_overview_widget: FoldOverviewWidget,
    splits: DatetimeSplits,
    all_splits: DatetimeSplits,
) -> None:
    st.header("Folds", divider="rainbow")

    with st.container(border=True):
        display_container, config_container = st.columns([20, 3])

        with config_container:
            # TODO(streamlit): https://github.com/streamlit/streamlit/issues/9870
            #   segmented_control with a required value
            figure_option = "📊 Show Figure"
            choice = st.selectbox(
                "Fold display style",
                [figure_option, "📝 Show Table"],
                help="Determines how folds are visualized.\n\nTODO: https://github.com/streamlit/streamlit/issues/9870",
            )
            show_figure = choice == figure_option

        plot_kwargs = {}
        if show_figure:
            plot_kwargs = folds_as_figure(df, plot_folds_widget, split_kwargs, display_container, config_container)
        else:
            folds_as_table(splits, display_container, config_container)

        with config_container:
            used, avail = fold_overview_widget.get_data_utilization(splits, limits)
            st.write(
                f"*Using `{format_seconds(used)}` of `{format_seconds(avail)}` **({used / avail:.1%})** of the available data range.*"
            )

    with st.container(border=True):
        left, right = st.columns([20, 4])
        with left:
            st.subheader(
                "Code snippets",
                divider="rainbow",
                help=(
                    "The [integration](https://time-split.readthedocs.io/en/stable/api/time_split.integration.html)"
                    " modules accept the same parameters as `time_fold.split()`."
                ),
            )

        with right:
            show_permalink(
                split_kwargs=split_kwargs,
                plot_kwargs=plot_kwargs,
                limits=limits if dataset is None else dataset,
            )

        left, mid, right = st.columns([10, 10, 4])

        with right:
            with st.container(border=True):
                st.subheader(
                    "Types",
                    divider=True,
                    help="Select type preferences. The `time-split` package uses Pandas types internally. "
                    "May not work for `📝 Free form` input.",
                )
                code_widget = CodeWidget.select()

            st.write(
                """
                * Click [here](https://time-split.readthedocs.io/en/stable/api/time_split.html#time_split.split) for `split()` docs.
                * Click [here](https://time-split.readthedocs.io/en/stable/api/time_split.html#time_split.plot) for `plot()` docs.
                """
            )

        with left:
            code_widget.show_split_code(split_kwargs, limits=limits)
            fold_overview_widget.show_overview(splits, all_splits=all_splits)
        with mid:
            code_widget.show_plot_code(split_kwargs, plot_kwargs=plot_kwargs, limits=limits)

        code_widget.show_splits(splits)


def show_permalink(
    *,
    split_kwargs: DatetimeIndexSplitterKwargs,
    plot_kwargs: dict[str, Any],
    limits: tuple[DatetimeTypes, DatetimeTypes] | str | bytes,
) -> None:
    permalink_kwargs = {**split_kwargs, **plot_kwargs, "data": limits}
    permalink_kwargs.pop("bar_labels", None)  # Not supported

    host = config.PERMALINK_BASE_URL
    if host == "":
        host = "http://localhost:8501"
        warn = True
    else:
        warn = False

    link_fn = get_user_link_fn() or create_explorer_link

    link = link_fn(host=host, **permalink_kwargs)
    st.write(f"Click [here]({link}) for sharable permalink.")

    with st.popover("🤝 Show permalink details", width="stretch"):
        if warn:
            st.warning(f"May not be accurate; {config.PERMALINK_BASE_URL=} not set.", icon="⚠️")

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
            doc = "https://time-split.readthedocs.io/en/stable/api/time_split.app.html#time_split.app.create_explorer_link"
            st.caption(
                f"Parameters may be [converted]({doc}) to equivalent values. "
                "Note that `data` is called `available` by the core library."
            )


def folds_as_figure(
    df: pd.DataFrame,
    plot_folds_widget: PlotFoldsWidget,
    split_kwargs: DatetimeIndexSplitterKwargs,
    display_container: DeltaGenerator,
    config_container: DeltaGenerator,
) -> dict[str, Any]:
    with config_container, st.container(border=True):
        st.subheader("Plot style", divider=True)
        plot_kwargs = plot_folds_widget.select()

    with display_container:
        plot_folds_widget.plot(split_kwargs, df, **plot_kwargs)

    return plot_kwargs


def folds_as_table(
    splits: DatetimeSplits,
    display_container: DeltaGenerator,
    config_container: DeltaGenerator,
) -> None:
    url = "https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes"

    with config_container, st.container(border=True):
        st.subheader("Table style", divider=True)
        fmt = st.text_input(
            "✏️️️ Select timestamp format.",
            value="{.auto}",
            placeholder="See help for options.",
            help="Select a property `{.auto}` or `{.iso}` or `{.date}`. You may also use "
            f"regular datetime [Format Codes]({url}) such as `{{:%Y-%m-%d (%A)}}`.",
        ).strip()
        if not fmt:
            fmt = "{.auto}"

    with display_container:
        table = pd.DataFrame.from_records(splits, columns=DatetimeSplitBounds._fields).map(_PrettyTimestamp)
        table.index.name = "fold_no"
        table = table.map(fmt.format)
        st.dataframe(table)
