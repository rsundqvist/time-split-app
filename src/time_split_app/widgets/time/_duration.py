import datetime
from collections.abc import Iterable

import pandas as pd
import streamlit as st

from time_split_app import config


class DurationWidget:
    """Duration specified by unit and count.

    Args:
        default_unit: Default unit. Must be in `units`. Default is ``units[0]``.
        units: An iterable of permitted units. Default is determined by ``config.DATE_ONLY``.
        default_periods: Default period counts per unit.
    """

    def __init__(
        self,
        default_unit: str | None = None,
        units: Iterable[str] | None = None,
        default_periods: dict[str, int] | None = None,
    ) -> None:
        units = (*units,)

        if units is None:
            units = ("days",) if config.DATE_ONLY else ("days", "hours", "minutes")
        elif not units:
            raise ValueError("Need at least one unit.")

        if default_unit is None:
            self._unit = units[0]
        else:
            if default_unit not in units:
                raise ValueError(f"{default_unit=} must be in {units=}")
            self._unit = default_unit

        default_periods = {} if default_periods is None else default_periods.copy()
        for unit, periods in default_periods.items():
            if periods <= 0:
                raise ValueError(f"Bad default {periods=} for {unit=}.")

        defaults = {"days": 7, "hours": 7 * 60, "minutes": 7 * 60 * 60}
        for unit in units:
            default = defaults.get(unit, 1)
            default_periods.setdefault(unit, default)

        self._units = units
        self._periods = default_periods

    def select(self, label: str, *, horizontal: bool = False) -> datetime.timedelta:
        """Prompt user to select a duration.

        Args:
            label: Label to show.
            horizontal: If ``True``, show elements side-by-side.

        Returns:
            A timedelta.
        """
        if horizontal:
            left, right = st.columns(2)
        else:
            container = st.container()
            left = right = container

        with right:
            unit = st.selectbox(
                f"select-{label}-unit",
                options=self._units,
                index=self._units.index(self._unit),
                label_visibility="collapsed",
                disabled=len(self._units) == 1,
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


def select_duration(label: str, *, horizontal: bool = False) -> datetime.timedelta:
    """See :meth:`DurationWidget.select`."""
    return DurationWidget().select(label, horizontal=horizontal)
