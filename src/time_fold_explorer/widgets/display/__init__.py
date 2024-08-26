"""Widgets for interacting visualizing folds."""

from ._aggregate import AggregationWidget
from ._overview import FoldOverviewWidget
from ._plot_folds import PlotFoldsWidget
from ._code import CodeWidget
from ._performance import PerformanceTweaksWidget

__all__ = [
    "AggregationWidget",
    "PlotFoldsWidget",
    "FoldOverviewWidget",
    "CodeWidget",
    "PerformanceTweaksWidget",
]
