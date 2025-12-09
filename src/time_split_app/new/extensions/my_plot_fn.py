"""Dummy extensions for the Time Split application.

See https://time-split.readthedocs.io/en/latest/api/time_split.app.reexport.html for documentation.
"""

from typing import Any

import pandas as pd
from matplotlib.axes import Axes
from time_split import plot


def my_plot_fn(*args: Any, available: pd.DataFrame, **kwargs: Any) -> Axes:
    """Same signature as https://time-split.readthedocs.io/en/stable/api/time_split.html#time_split.plot."""
    if "dummy" in available.columns:
        row_counts = available["dummy"].groupby(pd.Grouper(freq="3h")).sum()
        kwargs.setdefault("row_count_bin", row_counts)

    ax = plot(*args, available=available, **kwargs)
    ax.set_title("my_plot_fn")

    return ax
