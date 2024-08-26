"""This is `very` limited.

There are loads of ways that the app can fail that this doesn't even begin to cover. Use the dev/*.sh-scripts to verify
changes manually.
"""

import pytest
from time_fold_explorer.widgets.types import QueryParams


@pytest.mark.parametrize(
    "data, expected",
    [
        # Trivial zeroing of all fields except the minute
        # start=2019-05-01 00:00:31
        ("1556668831-1557606871", ("2019-05-01 00:00:00", "2019-05-11 20:35:00")),  # end=20:34:31
        ("1556668831-1557606749", ("2019-05-01 00:00:00", "2019-05-11 20:30:00")),  # end=20:32:29
        # Flipping hours/dates
        # start=(2019-04-30 23:59:40, 2019-05-11 20:59:31)
        ("1556668780-1557608371", ("2019-05-01 00:00:00", "2019-05-11 21:00:00")),
        # Exact
        ("1556668800-1557606600", ("2019-05-01 00:00:00", "2019-05-11 20:30:00")),
    ],
)
def test_timestamps(data: str, expected: tuple[str, str]) -> None:
    expected_start, expected_end = expected

    actual = QueryParams.make(data=data).data  # naive utc
    assert isinstance(actual, tuple) and len(actual) == 2
    start, end = map(str, actual)

    assert start == expected_start
    assert end == expected_end
