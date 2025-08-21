import datetime
from typing import Self

import pandas as pd
import streamlit as st

from time_split_app import config


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
            default_unit = "minutes"
            units.extend(("seconds", "minutes", "hours"))

        periods = {}
        for unit in units:
            kwargs = {unit: 1}
            n = delta / datetime.timedelta(**kwargs)
            periods[unit] = round(n)

        return cls(default_unit, periods=periods)

    def select(self, label: str, *, horizontal: bool = True) -> datetime.timedelta:
        """Prompt user to select a duration.

        Args:
            label: Label to show.
            horizontal: If ``True``, show elements side-by-side.

        Returns:
            A timedelta.
        """
        if horizontal:
            with st.container(key=f"tight-columns-DurationWidget.select-{label}"):
                left, right = st.columns(2)
        else:
            container = st.container()
            left = right = container

        with right:
            options = [*self._periods]
            unit = st.selectbox(
                f"select-{label}-unit",
                options=options,
                index=options.index(self._unit),
                label_visibility="collapsed",
                disabled=len(options) == 1,
            )
            assert isinstance(unit, str)

        with left:
            periods = st.number_input(
                f"select-{label}-periods",
                min_value=1,
                max_value=None,
                value=self._periods[unit],
                label_visibility="collapsed",
            )
            assert isinstance(periods, int)

        timedelta = pd.Timedelta(f"{periods} {unit}").to_pytimedelta()
        assert isinstance(timedelta, datetime.timedelta)
        return timedelta


def select_duration(
    label: str,
    *,
    horizontal: bool = True,
    delta: datetime.timedelta | int = 7,
    date_only: bool | None = None,
) -> datetime.timedelta:
    """See :meth:`DurationWidget.select`."""
    return DurationWidget.from_delta(delta, date_only).select(label, horizontal=horizontal)
