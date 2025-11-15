"""This is `very` limited.

There are loads of ways that the app can fail that this doesn't even begin to cover. Use the dev/*.sh-scripts to verify
changes manually.
"""

import sys
from datetime import datetime
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import time_split_app as base_package


def dummy_range():
    import streamlit as st

    st.error(DUMMY_RANGE)
    return datetime.fromisoformat("2019-04-11 00:35:00"), datetime.fromisoformat("2019-05-11 21:30:00")


DUMMY_RANGE = f"{__name__}.{dummy_range.__name__}"


@pytest.mark.filterwarnings("ignore")
def test_app(monkeypatch):
    for name in list(sys.modules):
        if name.startswith(base_package.__name__):
            del sys.modules[name]

    monkeypatch.setenv("DATE_ONLY", "False")
    monkeypatch.setenv("DATA_GENERATOR_INITIAL_RANGE_FN", DUMMY_RANGE)

    path = Path(__file__).parent.parent / "app.py"
    runner = AppTest.from_file(str(path))
    runner.query_params = {"n_splits": "3"}

    runner.run(timeout=10)

    assert runner.error[0].value == DUMMY_RANGE

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
        (
            3,
            [
                ("Data", "column 0"),
                ("Data", "column 1"),
                ("Data", "column 2"),
                ("Data", "n_hours"),
                ("Data", "n_rows"),
                ("Future data", "column 0"),
                ("Future data", "column 1"),
                ("Future data", "column 2"),
                ("Future data", "n_hours"),
                ("Future data", "n_rows"),
            ],
        ),
        (1000, ["timestamp", "column 0", "column 1", "column 2"]),
        (2, ["FIGURE_DPI", "PLOT_RAW_TIMESERIES", "PLOT_AGGREGATIONS_PER_FOLD", "MAX_SPLITS"]),
        (1, ["Rows", "Cols", "Start", "Span", "End"]),
        (2, ["Index", "Original", "Change", "Expanded"]),
    ]

    actual_expansion = runner.dataframe[-1].value.to_string()
    assert actual_expansion == EXPECTED_EXPANSION.strip("\n")


EXPECTED_EXPANSION = """
   Index            Original   Change   Expanded
0  Start 2019-04-11 00:35:00     -35m 2019-04-11
1    End 2019-05-11 21:30:00  +2h 30m 2019-05-12
"""
