import itertools
from typing import Sized

import pandas as pd

from rics.strings import format_seconds
from time_split.types import DatetimeSplitCounts, DatetimeSplits


class FoldOverviewWidget:
    def show_overview(self, splits: DatetimeSplits, *, all_splits: DatetimeSplits) -> None:
        import streamlit as st

        kept_hours = self.time(splits)
        all_hours = self.time(all_splits)
        removed_hours = DatetimeSplitCounts(
            data=all_hours.data - kept_hours.data,
            future_data=all_hours.future_data - kept_hours.future_data,
        )
        hours = [kept_hours, removed_hours, all_hours]

        overview = {
            "Fold counts": " / ".join(map(str, self.counts(splits, all_splits=all_splits))),
            "Data time": " / ".join(format_seconds(counts.data) for counts in hours),
            "Future data time": " / ".join(format_seconds(counts.future_data) for counts in hours),
        }

        st.dataframe(pd.Series(overview, name="Kept / Removed / Total").to_frame().T, width="stretch")

    @classmethod
    def get_data_utilization(cls, splits: DatetimeSplits, limits: tuple[pd.Timestamp, pd.Timestamp]) -> tuple[int, int]:
        available = limits[1] - limits[0]
        used = max(*itertools.chain.from_iterable(splits)) - min(*itertools.chain.from_iterable(splits))
        return int(used.total_seconds()), int(available.total_seconds())

    @classmethod
    def time(cls, splits: DatetimeSplits) -> DatetimeSplitCounts:
        data = pd.Timedelta(0)
        future_data = pd.Timedelta(0)
        for start, mid, end in splits:
            data += mid - start
            future_data += end - mid

        return DatetimeSplitCounts(data=int(data.total_seconds()), future_data=int(future_data.total_seconds()))

    @classmethod
    def counts(cls, splits: DatetimeSplits, *, all_splits: DatetimeSplits | int) -> tuple[int, int, int]:
        if isinstance(all_splits, Sized):
            all_splits = len(all_splits)

        return len(splits), all_splits - len(splits), all_splits
