import logging
from importlib import import_module
import streamlit as st

from ._data_loader_widget import DataLoaderWidget
from time_split_app import config


@st.cache_resource
def from_env_entrypoint() -> list[DataLoaderWidget]:
    loaders = []
    for value in config.DATASET_LOADER:
        if not value:
            continue

        loader = _from_user_spec(value)
        _sanity_check(loader)
        loaders.append(loader)
        break

    return loaders


def _sanity_check(loader: DataLoaderWidget) -> None:
    first = loader.get_prefix()
    second = loader.get_prefix()

    if first != second:
        msg = f"Bad {loader.get_prefix.__qualname__}(): Prefixes {first=} and {second=} do not match."
        raise RuntimeError(msg)

    if first is None:
        return

    if len(first) == 0:
        msg = f"Bad {loader.get_prefix.__qualname__}(): Prefix {first!r} is empty; return None instead."
        raise RuntimeError(msg)


def _from_user_spec(value: str) -> DataLoaderWidget:
    logging.getLogger(__package__).info(f"Resolving DataLoaderWidget implementation from DATASET_LOADER={value!r}.")

    module_name, _, attribute_name = value.partition(":")
    module = import_module(module_name)
    obj = getattr(module, attribute_name)

    if isinstance(obj, DataLoaderWidget):
        return obj
    if issubclass(obj, DataLoaderWidget):
        return obj()  # type: ignore[no-any-return]

    if callable(obj):
        loader = obj()
        if isinstance(loader, DataLoaderWidget):
            return loader

    cls = DataLoaderWidget.__name__
    msg = f"Bad DATASET_LOADER={value!r}: Expected a {cls} implementation, instance or factory function. Got: {obj!r}."
    raise TypeError(msg)
