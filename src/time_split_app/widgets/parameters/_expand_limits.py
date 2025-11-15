from ast import literal_eval
from dataclasses import dataclass
from typing import ContextManager, Any

import numpy as np
import pandas as pd
import streamlit as st
from time_split._frontend._to_string import stringify

from time_split.settings import auto_expand_limits as settings
from time_split_app.widgets.types import ExpandLimitsType, QueryParams
from time_split.support import expand_limits
from time_split.types import ExpandLimits


@dataclass
class ExpandLimitsWidget:
    auto: bool = True
    """Preselect the `'auto'` option and add a dedicated button for it."""
    disabled: bool = True
    """Enable disabling option."""
    free_from: bool = True
    """Allow free-form input parsed using :func:`ast.literal_eval`."""

    default_value: str = "d<3h"
    """Default (pre-selected) value for the manual input field."""
    change_props: str = "color: black; background-color: rgba(255, 200, 50, 0.5);"
    """Properties used to highlight changed limits. Set to an empty string to disable."""
    no_change_props: str = "color: rgba(200, 200, 200, 0.5)"
    """Properties used to highlight unchanged limits. Set to an empty string to disable."""

    _container: ContextManager[Any] | None = None

    def select(self) -> ExpandLimits:
        self._container = st.container(border=True)

        with self._container:
            self._write_header()
            return self._select()

    def show_expand_limits(self, limits: tuple[pd.Timestamp, pd.Timestamp], spec: ExpandLimits) -> None:
        if self._container is None:
            self._write_header()
            self._show_expand_limits(limits, spec)
        else:
            with self._container:
                self._show_expand_limits(limits, spec)

    @classmethod
    def _write_header(cls) -> None:
        st.header("Data limits expansion", divider="rainbow", help=EXPAND_LIMITS_HELP)

    def _show_expand_limits(self, limits: tuple[pd.Timestamp, pd.Timestamp], spec: ExpandLimits) -> None:
        try:
            expanded_limits = expand_limits(limits, spec=spec)
        except Exception as e:
            st.exception(e)
            st.stop()

        if limits == expanded_limits:
            if spec:
                st.info("Limits were not expanded.", icon="ℹ️")
            return

        data = {
            "Index": ["Start", "End"],
            "Original": limits,
            "Expanded": expanded_limits,
        }
        df = pd.DataFrame(data)
        df["Change"] = [stringify(row.Original, new=row.Expanded, diff_only=True) for row in df.itertuples()]

        same = df["Expanded"] == df["Original"]
        st.dataframe(
            df[["Index", "Original", "Change", "Expanded"]].style.apply(
                lambda _: np.where(~same, self.change_props, self.no_change_props),
                axis=0,
            ),
            width="stretch",
            hide_index=True,
        )

    def get_options(self) -> list[ExpandLimitsType]:
        options = []

        if self.auto:
            options.append(ExpandLimitsType.AUTO)
        if self.disabled:
            options.append(ExpandLimitsType.DISABLED)
        if self.free_from:
            options.append(ExpandLimitsType.FREE_FORM)

        return options

    def _select(self) -> ExpandLimits:
        options = self.get_options()

        query = QueryParams.get().expand_limits
        if query is None:
            index = 0
        elif isinstance(query, bool):
            index = options.index(ExpandLimitsType.AUTO if query is True else ExpandLimitsType.DISABLED)
        else:
            index = options.index(ExpandLimitsType.FREE_FORM)

        choice = st.radio(
            "Data limits expansion",
            options,
            index=index,
            horizontal=True,
            label_visibility="collapsed",
        )

        if choice == ExpandLimitsType.DISABLED:
            return False
        elif choice == ExpandLimitsType.AUTO:
            spec = "auto"
        else:
            value = query if isinstance(query, str) else self.default_value

            user_input = st.text_input(
                "expand-limits",
                value=value,
                placeholder=str(tuple(settings.day)),
                label_visibility="collapsed",
            )
            try:
                spec = literal_eval(user_input)
            except Exception:
                spec = user_input.strip()

            if not spec:
                st.stop()

        return spec


EXPAND_LIMITS_HELP = (
    "See the [User guide](https://time-split.readthedocs.io/en/stable/guide/expand-limits.html) for help."
    " Automatic expansion is configurable using the global "
    " [`auto_expand_limits`](https://time-split.readthedocs.io/en/stable/api/time_split.settings.html#time_split.settings.auto_expand_limits)"
    " configuration object. Manual input is validated using the "
    "[`expand_limits()`](https://time-split.readthedocs.io/en/stable/api/time_split.support.html#time_split.support.expand_limits)"
    " support function."
)
