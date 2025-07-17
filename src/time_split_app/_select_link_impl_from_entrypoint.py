import logging
from importlib import import_module

import streamlit as st

from time_split_app import config
from time_split_app.widgets.types import LinkFn


@st.cache_resource
def get_user_link_fn() -> LinkFn | None:
    value = config.LINK_FN
    return _from_user_spec(value) if value else None


def _from_user_spec(value: str) -> LinkFn:
    logger = logging.getLogger(__package__)
    logger.info(f"Resolving create_explorer_link() implementation from LINK_FN={value!r}.")

    module_name, _, attribute_name = value.partition(":")
    module = import_module(module_name)
    obj = getattr(module, attribute_name)

    if callable(obj):
        return obj  # type: ignore[no-any-return]

    msg = f"Bad LINK_FN={value!r}: Expected callable `(...) -> str`. Got: {obj!r}."
    raise TypeError(msg)
