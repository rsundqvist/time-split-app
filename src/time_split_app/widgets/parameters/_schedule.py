import datetime
from ast import literal_eval
from typing import Collection, TypeVar

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

        kinds: list[ScheduleType] = []
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
            if "schedule-type" not in st.session_state:
                if query_schedule is None:
                    st.session_state["schedule-type"] = kinds[0]
                else:
                    _, kind = self._process_user_input(query_schedule.strip(), kind=None)
                    st.session_state["schedule-type"] = kind

            kind = st.radio("schedule-type", kinds, horizontal=True, label_visibility="collapsed", key="schedule-type")
            assert kind is not None

            if kind == ScheduleType.DURATION:
                with st.container(key="tight-rows-schedule_span"):
                    schedule = select_duration("schedule", read_query_param="schedule")
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

                schedule, _ = self._process_user_input(user_input, kind)

        with right:
            filters = self._filter.select()

        return schedule, filters

    def _process_user_input(self, user_input: str, kind: ScheduleType | None) -> tuple[ProcessedSchedule, ScheduleType]:
        if kind is None:
            for kind in self._kinds:
                try:
                    return self._process_user_input(user_input, kind)
                except Exception:
                    pass

        if kind is ScheduleType.CRON:
            cron = user_input.strip()
            croniter.expand(cron)
            return cron, kind

        if kind is ScheduleType.DURATION:
            return _to_timedelta(user_input), kind

        if kind is ScheduleType.FREE_FORM:
            return _validate_literal(user_input), kind

        raise NotImplementedError(f"{kind=}")


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
