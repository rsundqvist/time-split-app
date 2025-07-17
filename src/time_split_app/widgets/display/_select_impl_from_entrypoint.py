import logging
from importlib import import_module

import streamlit as st

from time_split_app import config
from time_split_app.widgets.types import PlotFn


@st.cache_resource
def get_user_plot_fn() -> PlotFn | None:
    value = config.PLOT_FN
    return _from_user_spec(value) if value else None


def _from_user_spec(value: str) -> PlotFn:
    logger = logging.getLogger(__package__)
    logger.info(f"Resolving plot() implementation from PLOT_FN={value!r}.")

    module_name, _, attribute_name = value.partition(":")
    module = import_module(module_name)
    obj = getattr(module, attribute_name)

    if callable(obj):
        return obj  # type: ignore[no-any-return]

    msg = f"Bad PLOT_FN={value!r}: Expected callable `(...) -> Axes`. Got: {obj!r}."
    raise TypeError(msg)
