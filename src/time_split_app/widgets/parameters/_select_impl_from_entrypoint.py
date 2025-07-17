import logging
from importlib import import_module

import streamlit as st

from time_split_app import config
from time_split_app.widgets.types import SelectSplitParams


@st.cache_resource
def get_user_select_fn() -> SelectSplitParams | None:
    value = config.SPLIT_SELECT_FN
    return _from_user_spec(value) if value else None


def _from_user_spec(value: str) -> SelectSplitParams:
    logger = logging.getLogger(__package__)
    logger.info(f"Resolving select_split_params() implementation from SPLIT_SELECT_FN={value!r}.")

    module_name, _, attribute_name = value.partition(":")
    module = import_module(module_name)
    obj = getattr(module, attribute_name)

    if callable(obj):
        return obj  # type: ignore[no-any-return]

    msg = f"Bad SPLIT_SELECT_FN={value!r}: Expected callable `() -> DatetimeIndexSplitterKwargs`. Got: {obj!r}."
    raise TypeError(msg)
