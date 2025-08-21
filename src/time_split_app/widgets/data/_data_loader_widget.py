import abc
from collections.abc import Collection
from datetime import date, datetime, timedelta
from typing import Literal, overload

import pandas as pd
import streamlit as st
from rics.types import LiteralHelper
from rics.misc import get_by_full_name
from time_split_app import config

AnyDateRange = tuple[datetime, datetime] | tuple[date, date]
Anchor = Literal["absolute", "relative", "now"]
AnchorOptions = Collection[Anchor]
ANCHOR_HELPER: LiteralHelper[Anchor] = LiteralHelper(Anchor, default_name="anchor", normalizer=str.lower)

ABSOLUTE = "absolute"
NOW = "now"
RELATIVE = "relative"


class DataLoaderWidget(abc.ABC):
    """Load or generate datasets that require user input."""

    @abc.abstractmethod
    def get_title(self) -> str:
        """Title shown in the `⚙️ Configure data` menu. Uses Markdown syntax."""

    @abc.abstractmethod
    def get_description(self) -> str:
        """Brief description shown in the `⚙️ Configure data` menu. Uses Markdown syntax."""

    @abc.abstractmethod
    def load(self, params: bytes | None) -> tuple[pd.DataFrame, dict[str, str], bytes] | pd.DataFrame:
        """Load data.

        .. note::

           This method will be called many times due to the Streamlit data model.

        You may want to use ``@streamlit.cache_data`` or ``@streamlit.cache_resource`` to improve performance. See
        https://docs.streamlit.io/develop/concepts/architecture/caching
        for more information.

        The :meth:`select_range`-method may be used to prompt the user for a date range in which to retrieve data. If
        any other input is needed, you may use the

        Args:
            params: Parameter preset as bytes. Handling is implementation-specific.

        Returns:
            A :class:`pandas.DataFrame` or a tuple ``(data, aggregations, params)``, where the ``params: bytes`` may be given as
            the `params` argument to recreate the frame returned.

        See :attr:`.QueryParams.data` for more information regarding the `params` argument.
        """

    @classmethod
    @overload
    def select_range(
        cls,
        initial: AnyDateRange | None = None,
        *,
        date_only: Literal[False] = False,
        start_options: AnchorOptions | None = None,
        end_options: AnchorOptions | None = None,
    ) -> tuple[datetime, datetime]: ...

    @classmethod
    @overload
    def select_range(
        cls,
        initial: AnyDateRange | None = None,
        *,
        date_only: Literal[True],
        start_options: AnchorOptions | None = None,
        end_options: AnchorOptions | None = None,
    ) -> tuple[date, date]: ...

    @classmethod
    def select_range(
        cls,
        initial: AnyDateRange | None = None,
        *,
        date_only: bool | None = None,
        start_options: AnchorOptions | None = None,
        end_options: AnchorOptions | None = None,
    ) -> AnyDateRange:
        """Support method for getting user date range input.

        Args:
            initial: Initial range used by the widget.
            date_only: If ``True``, disable the time selector and return dates. Default = based on config.
            start_options: Start options to make available to the user. Default = all.
            end_options: End options to make available to the user. Default = all.

        Returns:
            A tuple ``(start, end)``.

        Raises:
            TypeError: If `start_options` or `start_options` are invalid.
        """
        from functools import partial

        from ..time import select_datetime, DurationWidget

        if date_only is None:
            date_only = config.DATE_ONLY

        start_options = ANCHOR_HELPER.options if start_options is None else cls._check(start_options, name="start")
        end_options = ANCHOR_HELPER.options if end_options is None else cls._check(end_options, name="end")

        select_datetime = partial(select_datetime, header=False, date_only=date_only)

        if initial is None:
            initial = initial_range_fn()
        initial_start, initial_end = initial
        delta: timedelta = initial_end - initial_start
        duration_widget = DurationWidget.from_delta(delta, date_only)

        with st.container(key=f"tight-rows-{cls.select_range.__qualname__}"):
            left, right = st.columns(2)
            left.subheader("Select Start", divider=True)
            right.subheader("Select End", divider=True)

            left_index, right_index = 0, 0
            if initial_range_fn is default_initial_range_fn:
                try:
                    left_index = [*start_options].index("relative")
                    right_index = [*end_options].index("now")
                except Exception:
                    pass

            with left:
                start_type = st.radio(
                    "start-selection-type",
                    start_options,
                    index=left_index,
                    horizontal=True,
                    format_func=str.title,
                    label_visibility="collapsed",
                )

            with right:
                end_type = st.radio(
                    "end-selection-type",
                    end_options,
                    index=right_index,
                    horizontal=True,
                    format_func=str.title,
                    label_visibility="collapsed",
                )

            if start_type == RELATIVE and end_type == RELATIVE:
                st.error("At least one of `Start date` and `End date` must be fixed.", icon="🚨")
                st.stop()

            start: datetime | date | None = None
            end: datetime | date | None = None

            # Handle explicit starts
            if start_type == NOW:
                with left:
                    start = select_datetime("Start", None, disabled=True)
            elif start_type == ABSOLUTE:
                with left:
                    start = select_datetime("Start", initial_start)

            # Handle explicit ends
            if end_type == NOW:
                with right:
                    end = select_datetime("End", None, disabled=True)
            elif end_type == ABSOLUTE:
                with right:
                    end = select_datetime("End", initial_end)

            # Handle relative start anchor.
            if start_type == RELATIVE:
                assert end is not None
                with left:
                    start = end - duration_widget.select("start-duration")
            # Handle relative end anchor.
            elif end_type == RELATIVE:
                assert start is not None
                with right:
                    end = start + duration_widget.select("end-duration")

        assert start is not None
        assert end is not None

        if start >= end:
            st.info("Select valid range.", icon="ℹ️")  # noqa: RUF001
            st.stop()

        return start, end

    @classmethod
    def _check(cls, options: AnchorOptions, name: str) -> AnchorOptions:
        name = f"{name}_options"
        if len(options) > len(ANCHOR_HELPER.options):
            raise TypeError(f"Bad {name}={options!r}; max length is {len(ANCHOR_HELPER.options)}.")
        for i, option in enumerate(options):
            ANCHOR_HELPER.check(option, f"start_options[{i}]")
        if len(set(options)) != len(options):
            raise ValueError(f"Bad {name}; options must be unique.")

        return options


DEFAULT_INITIAL_RANGE_SECONDS = 30 * 24 * 60 * 60  # 30 days


def default_initial_range_fn() -> tuple[datetime, datetime] | tuple[date, date]:
    now = datetime.now()
    return now - timedelta(seconds=DEFAULT_INITIAL_RANGE_SECONDS), now


if func_name := config.DATA_GENERATOR_INITIAL_RANGE_FN:
    try:
        # Undocumented behavior!
        value = int(func_name)
        if value > 0:
            DEFAULT_INITIAL_RANGE_SECONDS = value
        initial_range_fn = default_initial_range_fn

    except ValueError:
        initial_range_fn = get_by_full_name(func_name)
else:
    initial_range_fn = default_initial_range_fn
