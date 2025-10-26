"""Streamlit application file."""

import logging
from time import perf_counter

import streamlit as st
from rics.plotting import configure as configure_plotting
from time_split import split

from time_split_app import _views, config, style
from time_split_app._logging import configure_logging, log_perf
from time_split_app._support import enforce_max_splits, get_about
from time_split_app.widgets.data import DataWidget
from time_split_app.widgets.display import (
    AggregationWidget,
    FoldOverviewWidget,
    PerformanceTweaksWidget,
    PlotFoldsWidget,
)
from time_split_app.widgets.parameters import SplitterKwargsWidget, get_user_select_fn
from time_split_app.widgets.types import DataSource, QueryParams

st.set_page_config(
    page_title="Time Split",
    page_icon="https://raw.githubusercontent.com/rsundqvist/time-split/master/docs/logo-icon.png",
    layout="wide",
    menu_items=None,
    initial_sidebar_state="expanded",
)

start = perf_counter()


if config.CONFIGURE_LOGGING:
    configure_logging()
if config.CONFIGURE_PLOTTING:
    configure_plotting()


if config.PROCESS_QUERY_PARAMS:
    QueryParams.set()  # Fail fast if the query is incorrect.
elif st.query_params:
    st.error("Query parameters are not allowed.", icon="🚨")
    st.write(st.query_params)
    st.write("Remove these parameters from the URL and try again.")
    st.stop()

style.apply_custom_css()

PERFORMANCE_TWEAKS_WIDGET = PerformanceTweaksWidget()
DATA_WIDGET = DataWidget(n_samples=config.RAW_DATA_SAMPLES)
SPLITTER_KWARGS_WIDGET = SplitterKwargsWidget()
AGGREGATION_WIDGET = AggregationWidget()

select_params = get_user_select_fn() or SPLITTER_KWARGS_WIDGET.select_params
with st.sidebar:
    sidebar_top = st.container()
    split_kwargs = select_params()

tabs = [
    ":bar_chart: Folds",
    ":chart_with_upwards_trend: Aggregations per fold",
    ":mag: Show raw data",
    ":grey_question: About",
]
folds_tab, aggregations_tab, data_tab, about_tab = st.tabs(tabs)

with about_tab:
    left, right = st.columns([3, 4])
    with left:
        st.write(get_about())

    with right, st.container(border=True):
        PERFORMANCE_TWEAKS_WIDGET.update_config()

with sidebar_top:
    with st.popover("⚙️ Configure data", width="stretch"):
        df, limits, data_source, default_aggregations, dataset = DATA_WIDGET.select_data()
        aggregations = AGGREGATION_WIDGET.configure(df, default_aggregations)
        # df, limits = DATA_WIDGET.select_range_subset(df)
        # st.caption("Changes will take effect immediately.")
    DATA_WIDGET.show_summary(df)

with st.sidebar:
    expand_limits = split_kwargs.get("expand_limits", "auto")
    SPLITTER_KWARGS_WIDGET.limits_widget.show_expand_limits(limits, expand_limits)

with data_tab:
    if data_source == DataSource.GENERATE:
        st.info("This is generated data. Use the `⚙️ Configure data` view to select a dataset.", icon="ℹ️")
    DATA_WIDGET.show_data(df)

    if config.PLOT_RAW_TIMESERIES:
        DATA_WIDGET.plot_data(df)
    else:
        st.warning(f"{config.PLOT_RAW_TIMESERIES=}", icon="⚠️")
        st.write("See the `❔ About` tab to update the configuration. Don't forget to click `Apply`!")

try:
    SPLITS = split(**split_kwargs, available=limits)
except ValueError as e:
    st.error(e, icon="🚨")
    st.write({**split_kwargs, "available": limits})
    st.stop()
ALL_SPLITS = split(**split_kwargs, available=limits, ignore_filters=True)

enforce_max_splits(len(ALL_SPLITS), split_kwargs, limits)

with folds_tab:
    _views.primary(
        df=df,
        plot_folds_widget=PlotFoldsWidget(),
        fold_overview_widget=FoldOverviewWidget(),
        split_kwargs=split_kwargs,
        limits=limits,
        dataset=QueryParams.normalize_dataset(dataset) if isinstance(dataset, str) else dataset,
        splits=SPLITS,
        all_splits=ALL_SPLITS,
    )

with aggregations_tab:
    AGGREGATION_WIDGET.plot_aggregations(df, split_kwargs=split_kwargs, aggregations=aggregations)

# Record performance
TOTAL_RUNTIME = perf_counter() - start
msg = f"Finished all tasks in **{1000 * TOTAL_RUNTIME:.1f}** ms."
msg = log_perf(
    msg,
    df,
    TOTAL_RUNTIME,
    extra={"n_splits": len(SPLITS), "n_splits_removed": len(ALL_SPLITS) - len(SPLITS)},
    level=logging.INFO,
)

with sidebar_top:
    func = st.warning
    for limit, candidate in (0.50, st.success), (1.0, st.info):
        if limit >= TOTAL_RUNTIME:
            func = candidate
            break

    func(msg, icon="⏱️")
st.toast(msg, icon="⏱️")
