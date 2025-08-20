"""Dummy extensions for the Time Split application.

See https://time-split.readthedocs.io/en/latest/api/time_split.app.reexport.html for documentation.
"""

from typing import Any

import pandas as pd
from matplotlib.axes import Axes
from time_split import plot
from time_split.app import create_explorer_link
from time_split.types import DatetimeIndexSplitterKwargs

from time_split_app.widgets import DataLoaderWidget
from time_split_app.widgets.parameters import ExpandLimitsWidget, ScheduleWidget, SpanWidget, SplitterKwargsWidget


class MyDatasetLoader(DataLoaderWidget):
    """Generates arbitrary datasets (possibly from user input).

    The class should not have any required constructor arguments, but you may point ``DATASET_LOADER`` to an initialized
    instance.
    """

    def get_title(self) -> str:
        """Title shown in the `⚙️ Configure data` menu. Uses Markdown syntax."""
        return f"🎉 Generate using `{MyDatasetLoader.__name__}`!."

    def get_description(self) -> str:
        """Brief description shown in the `⚙️ Configure data` menu. Uses Markdown syntax."""
        return f"Data created by the `{MyDatasetLoader.__name__}` class."

    def load(self, params: bytes | None) -> tuple[pd.DataFrame, dict[str, str], bytes] | pd.DataFrame:
        """Load data.

        .. note::

           This method will be called many times due to the Streamlit data model.

        You may want to use ``@streamlit.cache_data`` or ``@streamlit.cache_resource`` to improve performance. See
        https://docs.streamlit.io/develop/concepts/architecture/caching
        for more information.

        Args:
            params: Parameter preset as bytes. Handling is implementation-specific.

        Returns:
            A :class:`pandas.DataFrame` or a tuple ``(data, aggregations, params)``, where the ``params: bytes`` may be given as
            the `params` argument to recreate the frame returned.

        See :attr:`.QueryParams.data` for more information regarding the `params` argument.
        """
        if params:
            raise NotImplementedError(f"{params=}")

        initial = pd.Timestamp("2019-04-01"), pd.Timestamp("2019-05-11T20:30:00")
        start, end = self.select_range(
            initial,
            date_only=False,
            start_options=["absolute"],
            end_options=["absolute", "relative"],
        )

        index = pd.date_range(start, end)
        data = {"dummy-data": [1] * len(index)}

        return pd.DataFrame(data, index=index)


def my_plot_fn(*args: Any, **kwargs: Any) -> Axes:
    """Same signature as https://time-split.readthedocs.io/en/stable/api/time_split.html#time_split.plot."""
    ax = plot(*args, **kwargs)
    ax.set_title("my_plot_fn")
    return ax


def my_select_fn() -> DatetimeIndexSplitterKwargs:
    """Returns keyword arguments for https://time-split.readthedocs.io/en/stable/api/time_split.html#time_split.split."""
    return SplitterKwargsWidget(
        schedule_widget=ScheduleWidget(),
        before_widget=SpanWidget(span="before"),
        after_widget=SpanWidget(span="after"),
        limits_widget=ExpandLimitsWidget(),
    ).select_params()


def my_link_fn(*args: Any, **kwargs: Any) -> str:
    """Same signature as https://time-split.readthedocs.io/en/stable/api/time_split.app.html#time_split.app.create_explorer_link."""
    return create_explorer_link(*args, **kwargs)
