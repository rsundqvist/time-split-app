import datetime
from typing import Self, Literal

import pandas as pd
import streamlit as st

from time_split_app import config
from time_split_app.widgets.types import QueryParams

ReadQueryParam = Literal["schedule", "before", "after"]


class DurationWidget:
    """Duration specified by unit and count.

    Args:
        default_unit: Default unit; must be a key in `periods`.
        periods: A dict ``{unit: default_periods}``.
    """

    def __init__(
        self,
        default_unit: str,
        *,
        periods: dict[str, int],
    ) -> None:
        self._unit = default_unit
        self._units = sorted(periods, key=lambda unit: pd.Timedelta(1, unit), reverse=True)
        self._periods = periods

    @classmethod
    def from_delta(cls, delta: datetime.timedelta | int, date_only: bool | None = None) -> Self:
        if isinstance(delta, int):
            delta = datetime.timedelta(days=delta)
        if date_only is None:
            date_only = config.DATE_ONLY

        units = ["days"]
        if date_only:
            default_unit = "days"
        else:
            default_unit = "hours"
            units.extend(("seconds", "minutes", "hours"))

        periods = {}
        for unit in units:
            kwargs = {unit: 1}
            n = delta / datetime.timedelta(**kwargs)
            periods[unit] = round(n)

        return cls(default_unit, periods=periods)

    def select(
        self,
        label: str,
        *,
        horizontal: bool = True,
        read_query_param: ReadQueryParam | None = None,
    ) -> datetime.timedelta:
        """Prompt the user to select a duration.

        Args:
            label: Label to show.
            horizontal: If ``True``, show elements side-by-side.
            read_query_param: Attribute of :class:`.QueryParams` from which to read the default.

        Returns:
            A timedelta.
        """
        if horizontal:
            with st.container(key=f"tight-columns-DurationWidget.select-{label}"):
                left, right = st.columns([4, 3])
        else:
            container = st.container()
            left = right = container

        unit = self._unit
        periods = self._periods[unit]
        unit_label = f"select-{label}-unit"
        previous_unit_label = unit_label + "-previous"
        periods_label = f"select-{label}-periods"
        if unit_label not in st.session_state or periods_label not in st.session_state:
            if read_query_param:
                try:
                    periods, unit = self._read_query_param(read_query_param)
                except Exception:
                    pass

            st.session_state[unit_label] = unit
            st.session_state[periods_label] = periods

        with right:
            unit = st.selectbox(
                unit_label,
                options=self._units,
                label_visibility="collapsed",
                disabled=len(self._units) == 1,
                key=unit_label,
            )
            assert isinstance(unit, str)

        if previous_unit := st.session_state.get(previous_unit_label):
            if unit != previous_unit:
                prev_periods = st.session_state[periods_label]
                new_periods = pd.Timedelta(prev_periods, previous_unit) / pd.Timedelta(1, unit)
                st.session_state[periods_label] = round(new_periods) or 1
        st.session_state[previous_unit_label] = unit

        with left:
            # Periods may be huge, would be nice to add separates. Not supported by
            # https://github.com/alexei/sprintf.js/issues/124 though.
            periods = st.number_input(
                periods_label,
                min_value=1,
                max_value=None,
                label_visibility="collapsed",
                key=periods_label,
            )
            assert isinstance(periods, int)

        return pd.Timedelta(periods, unit).to_pytimedelta()  # type: ignore[no-any-return]

    def _read_query_param(self, param: ReadQueryParam) -> tuple[int, str]:
        schedule = getattr(QueryParams.get(), param)
        for unit in self._periods:
            if unit.removesuffix("s") in schedule:
                timedelta = pd.Timedelta(schedule)
                periods = int(timedelta / pd.Timedelta(1, unit=unit))
                # Check for float.is_integer() assumed to be done before this widget type is selected.
                return periods, unit

        msg = f"Could not derive unit and periods from {schedule=}."
        raise ValueError(msg)


def select_duration(
    label: str,
    *,
    horizontal: bool = True,
    delta: datetime.timedelta | int = 7,
    date_only: bool | None = None,
    read_query_param: ReadQueryParam | None = None,
) -> datetime.timedelta:
    """See :meth:`DurationWidget.select`."""
    return DurationWidget.from_delta(delta, date_only).select(
        label,
        horizontal=horizontal,
        read_query_param=read_query_param,
    )
