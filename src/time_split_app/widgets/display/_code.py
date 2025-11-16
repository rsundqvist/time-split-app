import datetime
from typing import Any, Callable, TypeAlias, Self

import pandas as pd
import streamlit as st
from time_split.types import DatetimeIndexSplitterKwargs, DatetimeTypes, DatetimeSplits, DatetimeSplitBounds

from time_split_app.widgets.types import TypePreference

AnyTimestamp: TypeAlias = str | datetime.date | datetime.datetime | pd.Timestamp
AnyTimedelta: TypeAlias = str | datetime.timedelta | pd.Timedelta

TimestampConverter = Callable[[AnyTimestamp], AnyTimestamp]
TimedeltaConverter = Callable[[AnyTimedelta], AnyTimedelta]
Converters = tuple[TimestampConverter, TimedeltaConverter]


class CodeWidget:
    """Output code that can be copy-pasted."""

    @classmethod
    def select(cls) -> Self:
        examples = {
            TypePreference.STRING: "'2019-05-11'",
            TypePreference.PYTHON: "datetime(2024, 6, 25)",
            TypePreference.PANDAS: "pd.Timestamp('2024-06-25')",
        }
        captions = [f"E.g. `{examples[ts]}`." for ts in TypePreference]

        selection = st.radio(
            "type-preference",
            examples,
            index=2,
            horizontal=True,
            captions=captions,
            label_visibility="collapsed",
        )
        assert selection is not None
        return cls(selection)

    def __init__(self, type_preference: TypePreference | str) -> None:
        if not isinstance(type_preference, TypePreference):
            type_preference = TypePreference[type_preference.upper()]
        self._type = type_preference

    def convert(self, arg: Any) -> Any:
        """Convert types in an arbitrary object."""
        if isinstance(arg, str):
            return arg
        if isinstance(arg, datetime.date):
            return self._convert_timestamp(arg, self._type)
        if isinstance(arg, datetime.timedelta):
            return self._convert_timedelta(arg, self._type)

        if isinstance(arg, dict):
            for key, value in arg.items():
                arg[key] = self.convert(value)
        elif isinstance(arg, DatetimeSplitBounds):
            items = (self.convert(a) for a in arg)
            return DatetimeSplitBounds(*items)
        elif isinstance(arg, (set, list, tuple)):
            arg_type = type(arg)
            return arg_type(self.convert(a) for a in arg)

        return arg

    def show_split_code(
        self,
        split_kwargs: DatetimeIndexSplitterKwargs,
        *,
        limits: tuple[DatetimeTypes, DatetimeTypes],
    ) -> None:
        split_kwargs = self.convert(split_kwargs.copy())
        limits = self.convert(limits)

        text = self._make_call("splits", "split", **split_kwargs, available=limits)
        text = self._with_imports(text, self._type)
        text = self._add_logged_splits(text)
        st.code(text)

    def show_plot_code(
        self,
        split_kwargs: DatetimeIndexSplitterKwargs,
        *,
        plot_kwargs: dict[str, Any],
        limits: tuple[DatetimeTypes, DatetimeTypes],
    ) -> None:
        split_kwargs = self.convert(split_kwargs.copy())
        plot_kwargs = self.convert(plot_kwargs.copy())
        limits = self.convert(limits)

        text = self._make_call("ax", "plot", **split_kwargs, available=limits, **plot_kwargs)
        text = "from rics import plotting \n\nplotting.configure()  # Configure plot style\n" + text
        text = self._with_imports(text, self._type)
        st.code(text)

    def show_splits(self, splits: DatetimeSplits) -> None:
        text = "\n".join(f"    {s!r}," for s in self.convert(splits))
        text = f"\nsplits = [\n{text}\n]"

        if self._type != TypePreference.PANDAS:
            text = text.replace(DatetimeSplitBounds.__name__, "")
            for field in DatetimeSplitBounds._fields:
                text = text.replace(f"{field}=", "")
        else:
            text = "from time_split.types import DatetimeSplitBounds\n" + text

        text = self._with_imports(text, self._type)
        if self._type == TypePreference.PANDAS:
            text = self._add_logged_splits(text)
        text = self._strip_midnight(text)
        st.code(text)

    @classmethod
    def _make_call(cls, __assign: str, __func: str, **kwargs: Any) -> str:
        lines = []

        for key, value in kwargs.items():
            if isinstance(value, tuple) and len(value) == 2:
                left, right = value
                lines.append(f"    {key}=({left!r},")
                space = " " * (len(key) + 4 + 2)
                lines.append(space + f"{right!r}),")
            else:
                lines.append(f"    {key}={value!r},")
        arguments = "\n".join(lines)

        text = f"\n{__assign} = time_split.{__func}(\n{arguments}\n)"
        text = cls._strip_midnight(text)
        return text

    @staticmethod
    def _with_imports(text: str, type_preference: TypePreference) -> str:
        text = "import time_split\n" + text

        if type_preference is TypePreference.STRING:
            return text

        if type_preference is TypePreference.PYTHON:
            imports = []
            if "datetime.datetime" in text:
                text = text.replace("datetime.datetime(", "datetime(")
                imports.append("datetime")
            if "datetime.timedelta" in text:
                text = text.replace("datetime.timedelta(", "timedelta(")
                imports.append("timedelta")

            if imports:
                text = f"from datetime import {', '.join(imports)}\n" + text
            return text

        if type_preference is TypePreference.PANDAS:
            imports = []
            if "Timestamp(" in text:
                text = text.replace("Timestamp(", "pd.Timestamp(")
                imports.append("Timestamp")
            if "Timedelta(" in text:
                text = text.replace("Timedelta(", "pd.Timedelta(")
                imports.append("Timedelta")

            if imports:
                text = "import pandas as pd\n" + text
            return text

        raise TypeError(f"{type_preference=}")

    @staticmethod
    def _convert_timestamp(timestamp: AnyTimestamp, type_preference: TypePreference) -> AnyTimestamp:
        if type_preference is TypePreference.STRING:
            return str(timestamp)

        if type_preference is TypePreference.PYTHON:
            if isinstance(timestamp, str):
                timestamp = pd.Timestamp(timestamp)
            if isinstance(timestamp, pd.Timestamp):
                timestamp = timestamp.to_pydatetime()
            return timestamp

        if type_preference is TypePreference.PANDAS:
            return pd.Timestamp(timestamp)

        raise TypeError(f"{type_preference=}")

    @staticmethod
    def _convert_timedelta(timedelta: AnyTimedelta, type_preference: TypePreference) -> AnyTimedelta:
        if type_preference is TypePreference.STRING:
            return str(timedelta)

        if type_preference is TypePreference.PYTHON:
            if isinstance(timedelta, str):
                timedelta = pd.Timedelta(timedelta)
            if isinstance(timedelta, pd.Timedelta):
                timedelta = timedelta.to_pytimedelta()
            return timedelta

        if type_preference is TypePreference.PANDAS:
            return pd.Timedelta(timedelta)

        raise TypeError(f"{type_preference=}")

    @classmethod
    def _add_logged_splits(cls, text: str) -> str:
        return text + '\nlogged_splits = time_split.log_split_progress(splits, logger="<logger-or-name>")'

    @classmethod
    def _strip_midnight(cls, text: str) -> str:
        return text.replace(" 00:00:00'", "'").replace(", 0, 0)", ")")
