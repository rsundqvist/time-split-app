"""Simple custom split parameters class.

This is a complex example that uses a custom filter.
"""

import json
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Literal, Self

import pandas as pd
from time_split.types import DatetimeIndexSplitterKwargs


@dataclass
class MyParameterizedFilterFn:
    """Parameterized fold filter.

    If parameters aren't needed, plain strings and static methods can be used instead.
    """

    remove_odd_days: bool = False
    min_days_training: int = 1

    def filter(self, start: pd.Timestamp, mid: pd.Timestamp, _: pd.Timestamp) -> bool:
        """Apply filter to fold."""
        if self.remove_odd_days and mid.day % 2 != 0:
            return False

        if self.min_days_training and (mid - start).days < self.min_days_training:  # noqa: SIM103
            return False

        return True

    __call__ = filter

    def serialize(self) -> str | None:
        """Serialize to string."""
        filters = {
            "remove_odd_days": self.remove_odd_days,
            "min_days_training": self.min_days_training,
        }
        filters = {key: value for key, value in filters.items() if value}
        return json.dumps(filters) if filters else None

    @classmethod
    def deserialize(cls, filters: str | None) -> Self:
        """Deserialize from string."""
        if not filters:
            return cls()

        kwargs = json.loads(filters)
        return cls(**kwargs)


@dataclass
class MySplitKwargs:
    """A custom splitter arguments class.

    In a real solution, this would probably be part of a shared namespace used both by the time-split-app and whatever
    pipeline actually uses the splits for cross-validation.
    """

    days: int = 7
    after: Literal[1] | timedelta = 1
    step: int = 1
    limit: int = 3
    filter: MyParameterizedFilterFn = field(default_factory=MyParameterizedFilterFn)

    @classmethod
    def from_kwargs(cls, splitter_kwargs: DatetimeIndexSplitterKwargs) -> Self | None:
        """Convert from :class:`.DatetimeIndexSplitterKwargs`."""
        rv = cls()

        if days := cls._extract_days(splitter_kwargs):
            rv.days = days

        if "after" in splitter_kwargs:
            value = splitter_kwargs["after"]
            if isinstance(value, timedelta):
                rv.after = value
            elif value == 1:
                rv.after = value  # type: ignore[assignment]  # MyPy narrowing doesn't work here.

        if "step" in splitter_kwargs:
            rv.step = splitter_kwargs["step"]
        if "n_splits" in splitter_kwargs:
            rv.limit = splitter_kwargs["n_splits"]

        filter_value = splitter_kwargs.pop("filter", None)
        if isinstance(filter_value, str):
            rv.filter = MyParameterizedFilterFn.deserialize(filter_value)

        return rv

    @classmethod
    def _extract_days(cls, splitter_kwargs: DatetimeIndexSplitterKwargs) -> int | None:
        if schedule := splitter_kwargs.get("schedule"):
            if isinstance(schedule, timedelta):
                return schedule.days
            elif isinstance(schedule, str):
                count, _, unit = schedule.partition(" ")
                assert "days" in unit, f"{schedule=}"  # noqa: S101
                return int(count)

        return None

    def to_kwargs(self) -> DatetimeIndexSplitterKwargs:
        """Convert to :class:`.DatetimeIndexSplitterKwargs`."""
        return DatetimeIndexSplitterKwargs(
            schedule=timedelta(days=self.days),
            before="all",
            after=self.after,
            step=self.step,
            n_splits=self.limit,
            filter=self.filter,  # Callable; needs special handling create_explorer_link()
            expand_limits="d",
        )
