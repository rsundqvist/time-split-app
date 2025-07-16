import datetime
from pathlib import Path

import pandas as pd
import streamlit as st
from ._data_loader_widget import DataLoaderWidget
from time_split.types import DatetimeTypes

from time_split_app import config


class SampleDataWidget(DataLoaderWidget):
    """Generated datasets."""

    def get_title(self) -> str:
        return "🪄 Generate"

    def get_description(self) -> str:
        return "Dummy data."

    @classmethod
    def load(cls, params: None | bytes) -> pd.DataFrame:
        if params:
            raise NotImplementedError
        start, end = cls.select_range()
        return cls._load_sample_data(start, end).copy()

    @classmethod
    @st.cache_resource(ttl=config.DATASET_CACHE_TTL, max_entries=4)
    def _load_sample_data(cls, start: datetime.datetime, end: datetime.datetime) -> pd.DataFrame:
        return cls.generate_sample_data(start=start, end=end, n_rows=None)

    @classmethod
    def generate_sample_data(
        cls,
        n_rows: int | None = 397,
        *,
        start: DatetimeTypes | None = None,
        end: DatetimeTypes | None,
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
