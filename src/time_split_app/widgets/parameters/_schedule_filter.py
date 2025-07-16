from dataclasses import dataclass
import streamlit as st

from time_split_app.widgets.types import Filters, QueryParams


@dataclass(frozen=True)
class ScheduleFilterWidget:
    limit: int = 99
    """Set the maximum fold count. Zero=no limit."""
    step: int = 99
    """Set the maximum fold step. Zero=no limit."""

    def select(self) -> Filters:
        """Get filtering parameters."""

        qp = QueryParams.get()

        limit = st.number_input(
            ":no_entry: Maximum fold count.",
            value="min" if qp.n_splits is None else qp.n_splits,
            min_value=0,
            max_value=self.limit or None,
            help="Keep at most *N* folds. Zero = no limit. Later folds are preferred.",
        )
        assert isinstance(limit, int)

        step = st.number_input(
            "🪜 Fold step size.",
            value="min" if qp.step is None else qp.step,
            min_value=1,
            max_value=self.step or None,
            help="Keep every *N* folds. Later folds are preferred.",
        )
        assert isinstance(step, int)

        return Filters(limit=limit, step=step)

    def __post_init__(self) -> None:
        if self.limit < 0:
            raise ValueError(f"{self.limit=} < 0")
        if self.step < 0:
            raise ValueError(f"{self.step=} < 0")
