import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from time_fold_explorer import config
from time_fold_explorer.widgets.parameters import select_datetime, DurationWidget
from time_fold_explorer.widgets.types import QueryParams
from time_split.types import DatetimeTypes


class SampleDataWidget:
    """Generated datasets."""

    def __init__(
        self,
        initial_range: tuple[DatetimeTypes, DatetimeTypes] = ("2019-04-11 00:35:00", "2019-05-11 21:30:00"),
    ) -> None:
        self._initial_range = initial_range

    def select(self, prompt: bool = True) -> pd.DataFrame:
        """Select and return data in the desired bounds."""
        query_range = QueryParams.get().data

        if isinstance(query_range, tuple):
            start, end = query_range
        else:
            start, end = map(lambda ts: pd.Timestamp(ts).to_pydatetime(), self._initial_range)

        if prompt:
            start, end = self._prompt(initial=(start, end))

        if start >= end:
            st.error(f"Bad range: `start='{start}'` must be before `end='{end}'`", icon="🚨")
            st.stop()

        return self._load_sample_date(n_rows=None, start=start, end=end)

    @classmethod
    @st.cache_data(ttl=config.DATASET_CACHE_TTL)
    def _load_sample_date(cls, **kwargs: Any) -> pd.DataFrame:
        return cls.load_sample_data(**kwargs)

    @classmethod
    def load_sample_data(
        cls, n_rows: int | None = 397, *, start: DatetimeTypes | None = None, end: DatetimeTypes | None
    ) -> pd.DataFrame:
        """Load timeseries sample data.

        The original timeseries has 397 rows. If `length` is greater, the original timeseries is repeated. Every other
        frames is reversed in order to preserve continuity. Index is generated using :func:`pandas.date_range`, using
        ``periods=n_rows``.

        Args:
            n_rows: Desired timeseries length.
            start: Index start.
            end: Index end.

        Returns:
            Sample timeseries data.
        """
        timeseries: pd.DataFrame = pd.read_csv(Path(__file__).parent / "sample.csv", header=None)
        reverse_timeseries = timeseries.iloc[::-1]

        index = pd.date_range(start, end, freq="5 min", periods=n_rows, name="timestamp")

        frames: list[pd.DataFrame] = []
        while len(frames) * len(timeseries) < len(index):
            frames.append(reverse_timeseries if len(frames) % 2 else timeseries)
        df = pd.concat(frames, ignore_index=True)

        if len(df) > len(index):
            df = df.tail(len(index))

        df.columns = [f"column {i}" for i in df]
        df.index = index

        return df

    @classmethod
    def _prompt(
        cls, initial: tuple[datetime.datetime, datetime.datetime]
    ) -> tuple[datetime.datetime, datetime.datetime]:
        start_date = "Start date"
        end_date = "End date"
        now = "Now"

        initial_start, initial_end = initial

        seconds = (initial_end - initial_start).total_seconds()
        duration_widget = DurationWidget(
            default_periods={
                "days": round(seconds / (24 * 60 * 60)),
                "hours": round(seconds / (60 * 60)),
                "minutes": round(seconds / 60),
            },
            default_unit="minutes",
        )

        left, right = st.columns(2)
        with left:
            start_type = st.radio(
                "start-selection-type",
                [start_date, "Duration", now],
                horizontal=True,
                label_visibility="collapsed",
            )
        with right:
            end_type = st.radio(
                "end-selection-type",
                [end_date, "Duration", now],
                horizontal=True,
                label_visibility="collapsed",
            )

        if start_type == "Relative start" and end_type == "Relative end":
            st.error("At least one of `Start date` and `End date` must be fixed.", icon="🚨")
            st.stop()

        start: datetime.datetime | None = None
        end: datetime.datetime | None = None
        if start_type in {start_date, now}:
            with left:
                start = select_datetime("Start", None if start_type == now else initial_start, header=False)
        if end_type in {end_date, now}:
            with right:
                end = select_datetime("End", None if end_type == now else initial_end, header=False)

        if start_type not in {start_date, now}:
            assert end is not None
            with left:
                start = end - duration_widget.select("start-duration")
        if end_type not in {end_date, now}:
            assert start is not None
            with right:
                end = start + duration_widget.select("end-duration")

        assert start is not None
        assert end is not None

        if start >= end:
            st.info("Select a valid range (start before end).", icon="ℹ️")
            st.stop()

        return start, end
