"""Custom implementations for selecting and serialized splitting parameters."""

from datetime import timedelta
from typing import Any

import streamlit as st
from time_split.app import create_explorer_link
from time_split.types import DatetimeIndexSplitterKwargs

from extensions.my_kwargs_type import MyParameterizedFilterFn, MySplitKwargs
from time_split_app.widgets.parameters import ScheduleFilterWidget, SplitterKwargsWidget
from time_split_app.widgets.types import QueryParams


def my_link_fn(*args: Any, **kwargs: Any) -> str:
    """Same signature as https://time-split.readthedocs.io/en/stable/api/time_split.app.html#time_split.app.create_explorer_link."""
    filter_fn: MyParameterizedFilterFn | None
    if filter_fn := kwargs.pop("filter", None):
        assert isinstance(filter_fn, MyParameterizedFilterFn), f"{type(filter_fn)=} | {filter_fn=}"  # noqa: S101
        kwargs["filter"] = filter_fn.serialize()

    return create_explorer_link(*args, **kwargs)


def my_select_fn() -> DatetimeIndexSplitterKwargs:
    """Returns keyword arguments for https://time-split.readthedocs.io/en/stable/api/time_split.html#time_split.split."""
    custom = "🌶️ Custom"
    selector = st.radio(
        f"Choose `{DatetimeIndexSplitterKwargs.__name__}` selector type.",
        [custom, "🍦 Default"],
        captions=[
            f"Use selector (`{MySplitKwargs.__name__}`).",
            f"Default selector (`{SplitterKwargsWidget.__name__}`).",
        ],
        horizontal=True,
    )
    return _from_custom_class() if selector == custom else SplitterKwargsWidget().select_params()


def _from_custom_class() -> DatetimeIndexSplitterKwargs:
    p = _get_my_split_kwargs()

    with st.container(border=True):
        st.subheader("Custom split parameters!", divider="rainbow")

        left, right = st.columns(2)
        p.days = left.slider("Days between folds.", 1, 14, p.days, format="%d days")

        until_next_fold = "Until next fold"
        choice = right.selectbox(
            "Select *after* data.",
            [until_next_fold, "Number of days"],
            index=0 if p.after == 1 else 1,
            help=f"Select `{until_next_fold}` to simulate models staying in use until a new model is trained.",
        )
        if choice == until_next_fold:
            p.after = 1
        else:
            p.after = _get_timedelta_after(p)

        left, right = st.columns(2)

        with left:
            p.limit, p.step = ScheduleFilterWidget(limit=7, step=7).select(limit=p.limit, step=p.step)

        with right, st.container(border=True):
            pf = p.filter
            pf.remove_odd_days = st.checkbox("Remove odd days?", pf.remove_odd_days)
            pf.min_days_training = st.slider("Minimum training days", 1, 14, pf.min_days_training, format="%d days")

    return p.to_kwargs()


@st.cache_data
def _get_my_split_kwargs() -> MySplitKwargs:
    rv: MySplitKwargs | None = None
    try:
        splitter_kwargs = QueryParams.get().get_splitter_kwargs()
        rv = MySplitKwargs.from_kwargs(splitter_kwargs)
    except ValueError:
        pass
    return MySplitKwargs() if rv is None else rv


def _get_timedelta_after(p: MySplitKwargs) -> timedelta:
    # See https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state#session-state-and-widget-state-association
    key = "after-days"

    value = st.session_state.get(key)
    if value is None:
        if isinstance(p.after, timedelta):
            value = p.after.days
        else:
            value = p.days

    days = st.slider("Number of future days.", 1, 14, value, format="%d days", key=key)
    return timedelta(days=days)
