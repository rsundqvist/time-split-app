from pathlib import Path

import pytest

from time_split_app.datasets import DatasetConfig, load_dataset_configs


def test_ok():
    path = Path(__file__).parent / "ok.toml"
    actual = load_dataset_configs(path)

    assert actual == [
        DatasetConfig(
            label="ok",
            path="./data.csv.zip",
            index="__INDEX__",
            aggregations={"x": "sum"},
            description="",
            read_function_kwargs={"index_col": "date", "parse_dates": True},
        )
    ]


def test_bad_path():
    path = Path(__file__).parent / "bad-path.toml"

    with pytest.raises(Exception, match="Could not derive a read function; suffix='xlsx'"):
        load_dataset_configs(path)


def test_duplicate_label():
    path = Path(__file__).parent / "duplicate-label.toml"

    with pytest.raises(ValueError, match="Duplicate label: 'ok'"):
        load_dataset_configs(path)
