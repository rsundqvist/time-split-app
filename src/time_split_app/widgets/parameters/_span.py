from ast import literal_eval
from typing import Literal

import pandas as pd
import streamlit as st

from time_split_app import config
from time_split_app.widgets.types import SpanType, QueryParams
from time_split.types import Span

SpanArg = Literal["before", "after"]


class SpanWidget:
    """Widget for managing `before` and `after` arguments.

    Args:
        span: Span direction.
        step: Max value in the user form for integer spans. Set to zero to disable.
        duration: Allow duration-based (timedelta) inputs.
        all: Allow the `'all'` option.
        free_from: Allow free-form input parsed using :func:`ast.literal_eval`.
    """

    def __init__(
        self,
        span: SpanArg,
        *,
        step: int = 10,
        duration: bool = True,
        all: bool = True,
        free_from: bool = True,
    ) -> None:
        if span not in {"before", "after"}:
            raise TypeError(f"{span=}")

        qp = QueryParams.get()
        is_before = span == "before"
        query_span = qp.before if is_before else qp.after

        kinds: list[SpanType] = []
        if step:
            kinds.append(SpanType.STEP)
        if duration:
            kinds.append(SpanType.DURATION)
        if all:
            kinds.append(SpanType.ALL)
        if free_from or query_span is not None:
            kinds.append(SpanType.FREE_FORM)

        if not kinds:
            raise ValueError("Allow at least one input type.")

        self._kinds = kinds
        self._step = step
        self._is_before = is_before

    @property
    def span(self) -> SpanArg:
        return "before" if self._is_before else "after"

    def get_span(self, label: str, default_kind: SpanType) -> Span:
        """Get before/after input from the user."""
        return self._get_span(label, default_kind)

    def _get_span(self, label: str, default_kind: SpanType) -> Span:
        kinds = self._kinds

        qp = QueryParams.get()
        query_span = qp.before if self._is_before else qp.after

        radio_key = f"{type(self).__name__}-{label}-span-radio"

        kind: SpanType
        if radio_key not in st.session_state:
            kind = default_kind

            if query_span:
                query_span_kind = self._span_kind(query_span)
                if query_span_kind in kinds:
                    kind = query_span_kind

            st.session_state[radio_key] = kind

        prefix = ":arrow_left:" if self._is_before else ":arrow_right:"

        with st.container(key=f"tight-rows-{label}_span"):
            kind = st.radio(f"{prefix} Span :primary[***{label}***] the fold date.", kinds, key=radio_key)

        if kind is SpanType.STEP:
            return st.number_input(label, min_value=1, max_value=self._step, label_visibility="collapsed")

        if kind is SpanType.DURATION:
            with st.container(key=f"tight-rows-{label}_span_duration"):
                from ..time import select_duration

                return select_duration(label, read_query_param=self.span)

        text_input_key = f"{type(self).__name__}-{label}-span-user-input"
        if kind is SpanType.ALL:
            text_input_key = text_input_key + "-all"
            st.session_state[text_input_key] = "all"
        else:
            st.session_state.setdefault(text_input_key, "10 days 6 hours")

        user_input = st.text_input(
            label,
            label_visibility="collapsed",
            disabled=kind != SpanType.FREE_FORM,
            key=text_input_key,
        )

        if not user_input.strip():
            st.stop()

        return self._process_user_input(kind, user_input)

    @classmethod
    def _span_kind(cls, query_span: str) -> SpanType | None:
        if query_span == "all":
            return SpanType.ALL

        try:
            int(query_span)
            return SpanType.STEP
        except Exception:
            pass

        try:
            timestamp = pd.Timedelta(query_span)  # Ensure valid time span

            for unit in "d", "h", "m":
                num = timestamp / pd.Timedelta(1, unit)
                if num.is_integer():
                    return SpanType.DURATION

                if config.DATE_ONLY:
                    # Valid time span but not for date-only. Assume free form.
                    return SpanType.FREE_FORM

            return SpanType.DURATION
        except Exception:
            pass

        return SpanType.FREE_FORM

    def _process_user_input(self, kind: SpanType, user_input: str) -> Span:
        if kind == SpanType.ALL:
            return "all"

        if kind is SpanType.FREE_FORM:
            try:
                return literal_eval(user_input)
            except Exception:
                return user_input.strip()

        raise NotImplementedError(f"{kind=}")


def select_spans(before: SpanWidget, *, after: SpanWidget) -> tuple[Span, Span]:
    with st.container(border=True):
        st.subheader(
            "Dataset spans",
            divider="rainbow",
            help="https://time-split.readthedocs.io/en/stable/guide/spans.html",
        )

        left, right = st.columns(2, gap="medium")
        with left:
            before_span = before.get_span("before", default_kind=SpanType.DURATION)
        with right:
            after_span = after.get_span("after", default_kind=SpanType.STEP)

    return before_span, after_span
