from pathlib import Path

import pandas as pd
import pytest

from time_split_app.datasets import Dataset, DuplicateIndexError, load_dataset, load_dataset_configs


@pytest.mark.parametrize("name", ["ok", "ok-explicit-index"])
def test_load_dataset(name, monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    write_data()
    path = Path(__file__).parent / f"{name}.toml"
    config = load_dataset_configs(path)[0]

    dataset = load_dataset(config)
    assert isinstance(dataset, Dataset)
    assert isinstance(dataset.df.index, pd.DatetimeIndex)


class TestBadIndex:
    def test_bad_index(self):
        write_data()
        path = Path(__file__).parent / "bad-index-type.toml"
        config = load_dataset_configs(path)[0]

        with pytest.raises(TypeError, match="Bad index; expected a DatetimeIndex but got Index."):
            load_dataset(config)

    def test_duplicate_index(self):
        data = {"date": ["2019-05-11", "2019-05-12"], "x": [20, 19]}
        df = pd.DataFrame(data)
        unique = pd.DataFrame({"date": ["2025-01-01"], "x": [2025]})
        df = pd.concat([df] * 8 + [unique])

        df.to_csv("data.csv.zip", index=False)

        path = Path(__file__).parent / "ok.toml"
        config = load_dataset_configs(path)[0]

        with pytest.raises(DuplicateIndexError) as exc_info:
            load_dataset(config)

        exc = exc_info.value

        assert len(exc.samples) == 5
        assert exc.n_duplicated == 16
        assert exc.n_total == 17

        assert "2019-05-11" in repr(exc.__notes__[0])


def write_data():
    data = {"date": ["2019-05-11", "2019-05-12"], "x": [20, 19]}
    pd.DataFrame(data).to_csv("data.csv.zip", index=False)
