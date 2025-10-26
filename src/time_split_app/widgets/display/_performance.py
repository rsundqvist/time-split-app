import functools
import os
from typing import Collection

import numpy as np
import pandas as pd
import streamlit as st

from time_split_app import config
from time_split_app._logging import LOGGER

TypesDict = dict[str, type[int] | type[bool]]
ValuesDict = dict[str, int | bool]

LOGGER = LOGGER.getChild("PerformanceTweaksWidget")


class PerformanceTweaksWidget:
    """User-facing performance tweaks.

    This widget allows users to **reduce** (never increase) the configured limits (e.g. figure DPI) which have a large
    impact on rendering time.

    Defaults:
        Defaults may be configured using environment variables with the ``DEFAULT_``-prefix. Note that the config module
        values must still be respected, e.g.:

        .. code-block:: bash

           export PLOT_AGGREGATIONS_PER_FOLD=false
           export DEFAULT_PLOT_AGGREGATIONS_PER_FOLD=true
           streamlit run ...

        Will cause the server to instantly crash.

    Args:
        keys: Config keys to show to users.
    """

    def __init__(
        self,
        keys: Collection[str] = (
            "MAX_SPLITS",
            "FIGURE_DPI",
            "PLOT_RAW_TIMESERIES",
            "PLOT_AGGREGATIONS_PER_FOLD",
        ),
    ) -> None:
        _get_hard_limits()  # Populate

        types: TypesDict = {}
        values = config.get_values()

        for key in sorted(set(keys)):
            value = values[key]
            if isinstance(value, bool):  # Order matters - booleans are ints!
                types[key] = bool
            elif isinstance(value, int):
                types[key] = int
            else:
                raise TypeError(f"{key=}")

        self._types: TypesDict = types

    def update_config(self) -> None:
        """Show the configuration tweaking widget and update the global config."""
        st.subheader("Performance tweaker", divider="rainbow")
        st.write(
            "Reducing values may make the application run (much) faster, at the cost of reduced figure fidelity and/or"
            " a reduction in the amount of information shown about your dataset."
        )

        with st.form("server-config-form"):
            new_values = self._update_config()
            st.form_submit_button("Apply", type="primary", width="stretch")

        for key, value in new_values.items():
            setattr(config, key, value)

        self.compare_config()

    @classmethod
    def compare_config(cls) -> None:
        user = pd.Series(config.get_values(), name="User")
        server = pd.Series(_get_hard_limits(), name="Server")

        df = pd.concat([user, server], axis=1).T.style.apply(_highlight_lower)

        st.dataframe(df, width="stretch", hide_index=False)

    def _update_config(self) -> ValuesDict:
        new_values: ValuesDict = {}
        for key, key_type in self._types.items():
            if key_type is bool:
                new_values[key] = self._select_bool(key)
            elif key_type is int:
                new_values[key] = self._select_int(key)
            else:
                raise TypeError(f"{key=}")
        return new_values

    def _select_bool(self, key: str) -> bool:
        new_value = self._select_int(key, min_value=0)
        return bool(new_value)

    def _select_int(self, key: str, *, min_value: int = 1) -> int:
        current_value = getattr(config, key)
        max_value = _get_hard_limits()[key]

        if min_value == max_value:
            max_value = min_value + 1
            disabled = True
        else:
            disabled = False

        help = config.get_descriptions()[key]
        value = st.slider(
            f"Set `{key}` value.",
            value=current_value,
            min_value=min_value,
            max_value=max_value,
            disabled=disabled,
            help=f"**⚠️ Option locked by server.**\n\n{help}" if disabled else help,
        )
        assert isinstance(value, int)

        _check_hard_limit(key, max_value=max_value, value=value)

        return min(value, max_value)


def _check_hard_limit(key: str, *, max_value: int, value: int) -> None:
    if value <= max_value:
        return

    from os import _exit as force_exit

    LOGGER.critical(
        # The user can (probably) modify the browser code to send anything.
        f"Illegal config {value=} > {max_value=} for {key=}. Server shutting down.",
        extra={"value": value, "max_value": max_value, "label": key},
    )
    force_exit(51)  # regular exit will not halt the underlying server.


def _highlight_lower(series: pd.Series) -> list[str]:
    highlight = "background-color: rgba(0, 200, 0, 0.5)"
    return np.where(series < series["Server"], highlight, "").tolist()  # type: ignore[no-any-return]


@functools.cache
def _get_hard_limits() -> ValuesDict:
    limits = config.get_values()

    updated_keys = []
    # Update defaults, if they exist.
    for key, max_value in limits.items():
        default_key = f"DEFAULT_{key}"
        if (raw := os.environ.get(default_key, "").strip()) != "":
            default = raw.lower() != "false" if isinstance(max_value, bool) else int(raw)

            _check_hard_limit(key, max_value=max_value, value=int(default))

            updated_keys.append(key)
            LOGGER.info(f"Setting {key=} to {default=} (from {raw=}, max={max_value!r}).")
            setattr(config, key, default)
        else:
            LOGGER.info(f"Setting {key=} to the maximum value (since {default_key}={raw!r}): {max_value!r}.")

    current = config.get_values()
    LOGGER.info(
        f"Adjustable configuration keys ({len(limits | current)}): {list(limits)}"
        f"\n  {limits=}"
        f"\n  {current=}"
        f"\nUpdated keys ({len(updated_keys)}): {updated_keys}"
    )

    return limits
