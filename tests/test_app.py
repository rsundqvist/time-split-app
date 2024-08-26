"""This is `very` limited.

There are loads of ways that the app can fail that this doesn't even begin to cover. Use the dev/*.sh-scripts to verify
changes manually.
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.filterwarnings("ignore")
def test_app():
    path = Path(__file__).parent.parent / "app.py"
    runner = AppTest.from_file(str(path)).run(timeout=10)

    verify_sections(runner)
    verify_frames(runner)


def verify_sections(runner: AppTest) -> None:
    actual = {container.value for container in runner.subheader}
    expected = {"Schedule", "Dataset spans", "Performance tweaker", "Select data"}  # Just a subset
    assert expected & actual == expected


def verify_frames(runner: AppTest) -> None:
    frames = [(len(container.value), container.value.columns.to_list()) for container in runner.dataframe]

    assert frames == [
        (1, ["Fold counts", "Data time", "Future data time"]),
        (12, ["fold_no", "fold", "dataset", "column 0", "column 1", "column 2", "n_rows", "n_hours"]),
        (1000, ["timestamp", "column 0", "column 1", "column 2"]),
        (2, ["FIGURE_DPI", "PLOT_RAW_TIMESERIES", "PLOT_AGGREGATIONS_PER_FOLD", "MAX_SPLITS"]),
        (1, ["Rows", "Cols", "Start", "Span", "End", "Size"]),
        (2, ["Index", "Original", "Change", "Expanded"]),
    ]
