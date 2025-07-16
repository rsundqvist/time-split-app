import datetime
from ast import literal_eval
from typing import Callable, Collection, TypeVar

import pandas as pd
import streamlit as st
from croniter import croniter

from ..time import select_duration


from time_split_app.widgets.types import ScheduleType, Filters, QueryParams
from ._schedule_filter import ScheduleFilterWidget

ProcessedSchedule = str | datetime.timedelta | list[str] | tuple[str, ...]
R = TypeVar("R")


class ScheduleWidget:
    """Schedule input widget.

    Args:
        free_from: Allow free-form input parsed using :func:`ast.literal_eval`.
        duration: Allow duration-based (timedelta) inputs.
        cron: Allow `cron <https://pypi.org/project/croniter/>`_ expressions.
        filter: Fold filtering parameters.
    """

    def __init__(
        self,
        free_from: bool = True,
        duration: bool = True,
        cron: bool = True,
        filter: ScheduleFilterWidget | None = None,
    ) -> None:
        if filter is None:
            filter = ScheduleFilterWidget()

        kinds = []
        if cron:
            kinds.append(ScheduleType.CRON)
        if duration:
            kinds.append(ScheduleType.DURATION)
        if free_from or QueryParams.get().schedule is not None:
            kinds.append(ScheduleType.FREE_FORM)
        if not kinds:
            raise ValueError("Allow at least one input type.")

        self._kinds = kinds
        self._filter = filter

    def get_schedule(self) -> tuple[ProcessedSchedule, Filters]:
        """Get schedule input from the user."""
        with st.container(border=True):
            return self._get_schedule()

    def _get_schedule(self) -> tuple[ProcessedSchedule, Filters]:
        kinds = self._kinds
        query_schedule = QueryParams.get().schedule

        st.subheader(
            "Schedule",
            divider="rainbow",
            help="https://time-split.readthedocs.io/en/stable/guide/schedules.html",
        )

        schedule: ProcessedSchedule
        left, right = st.columns(2)
        with left:
            index = 0 if query_schedule is None else kinds.index(ScheduleType.FREE_FORM)
            kind = st.radio("schedule-type", kinds, index=index, horizontal=True, label_visibility="collapsed")
            assert kind is not None

            if kind == ScheduleType.DURATION:
                with st.container(key="tight-rows-schedule_span"):
                    schedule = select_duration("schedule")
            else:
                defaults = {
                    ScheduleType.CRON: "0 0 * * MON,FRI",
                    ScheduleType.FREE_FORM: repr(["2019-04-26", "2019-04-29", "2019-05-03", "2019-05-06"]),
                }

                user_input = st.text_area(
                    "schedule",
                    value=defaults[kind] if query_schedule is None else query_schedule,
                    placeholder=f"Enter {kind.name.replace('_', ' ').capitalize()}-schedule.",
                    height=83,
                    label_visibility="collapsed",
                )

                if not user_input.strip():
                    st.stop()

                schedule = self._process_user_input(kind, user_input)

        with right:
            filters = self._filter.select()

        return schedule, filters

    def _process_user_input(self, kind: ScheduleType, user_input: str) -> ProcessedSchedule:
        if kind is ScheduleType.CRON:
            _validate(user_input, croniter.expand)
            return user_input.strip()

        if kind is ScheduleType.DURATION:
            return _validate(user_input, _to_timedelta)

        if kind is ScheduleType.FREE_FORM:
            return _validate(user_input, _validate_literal)

        raise NotImplementedError(f"{kind=}")


def _validate(value: str, validator: Callable[[str], R]) -> R:
    try:
        return validator(value)
    except Exception as e:
        st.exception(e)
        st.stop()


def _to_timedelta(s: str) -> datetime.timedelta:
    timedelta = pd.Timedelta(s)
    if timedelta <= pd.Timedelta(0):
        st.error(f"Bad {timedelta=}; must be positive.", icon="🚨")
    return timedelta.to_pytimedelta()  # type: ignore[no-any-return]


def _validate_literal(s: str) -> ProcessedSchedule:
    try:
        val = literal_eval(s)
    except SyntaxError:
        val = s

    if isinstance(val, Collection) and not isinstance(val, str):
        pd.DatetimeIndex(val)

    return val  # type: ignore[no-any-return]
