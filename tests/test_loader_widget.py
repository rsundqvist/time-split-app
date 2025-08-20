import logging
from datetime import datetime

import pytest

from time_split_app import config
from time_split_app.widgets import DataLoaderWidget

logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").disabled = True


@pytest.mark.parametrize(
    "start_option, end_option",
    [
        ("absolute", "absolute"),
        ("absolute", "relative"),
        ("relative", "absolute"),
    ],
)
def test_select_range(start_option, end_option, monkeypatch):
    start = datetime.fromisoformat("2019-04-11 00:35:00")
    end = datetime.fromisoformat("2019-05-11 21:30:00")

    monkeypatch.setattr(config, "DATA_GENERATOR_INITIAL_RANGE_FN", lambda: (start, end))
    monkeypatch.setattr(config, "DATE_ONLY", False)

    actual = DataLoaderWidget.select_range(
        initial=(start, end),
        start_options=[start_option],
        end_options=[end_option],
    )

    assert actual == (start, end)


def test_select_date_range_date_only():
    start = datetime(2019, 4, 11, 0, 35)
    end = datetime(2019, 5, 11, 21, 30)
    actual = DataLoaderWidget.select_range(
        initial=(start, end),
        start_options=["absolute"],
        end_options=["relative"],
        date_only=True,
    )

    assert actual == (start.date(), end.date())
