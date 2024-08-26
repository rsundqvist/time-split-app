import datetime

import streamlit as st


def select_datetime(label: str, initial: datetime.datetime | None = None, header: bool = True) -> datetime.datetime:
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
    )
    assert isinstance(date, datetime.date)

    time = st.time_input(
        f"select-{label}-time",
        value=initial.time(),
        label_visibility="collapsed",
        step=datetime.timedelta(minutes=5),
    )
    return datetime.datetime.combine(date, time)
