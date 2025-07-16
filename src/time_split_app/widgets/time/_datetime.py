import datetime
from typing import Literal, overload

import streamlit as st

AnyDate = datetime.datetime | datetime.date


@overload
def select_datetime(
    label: str,
    initial: AnyDate | None = None,
    *,
    header: bool = True,
    date_only: Literal[False] = False,
    disabled: bool = False,
) -> datetime.datetime: ...


@overload
def select_datetime(
    label: str,
    initial: AnyDate | None = None,
    *,
    header: bool = True,
    date_only: Literal[True],
    disabled: bool = False,
) -> datetime.date: ...


def select_datetime(
    label: str,
    initial: AnyDate | None = None,
    *,
    header: bool = True,
    date_only: bool = False,
    disabled: bool = False,
) -> AnyDate:
    """Prompt user to select datetime.

    Args:
        label: Widget label.
        initial: Initial date. Pass ``None`` for current time.
        header: If ``True``, show `label` in a Streamlit header.
        date_only: If ``True``, disable the time selector and return plain :class:`datetime.date` instances.
        disabled: If ``True``, disable user input to the Streamlit widget.

    Returns:
        A datetime or date.
    """
    if initial is None:
        initial = datetime.datetime.now()
        initial = initial.replace(second=0, microsecond=0)

    if header:
        st.header(label)

    date = st.date_input(
        f"select-{label}-date",
        value=initial,
        min_value=datetime.date(1990, 1, 1),
        max_value=datetime.date(2100, 1, 1),
        format="YYYY-MM-DD",
        label_visibility="collapsed",
        disabled=disabled,
    )

    if date_only:
        return date

    assert isinstance(initial, datetime.datetime)

    time = st.time_input(
        f"select-{label}-time",
        value=initial.time(),
        label_visibility="collapsed",
        step=datetime.timedelta(minutes=5),
        disabled=disabled,
    )

    return datetime.datetime.combine(date, time)
