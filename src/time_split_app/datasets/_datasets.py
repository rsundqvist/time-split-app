from dataclasses import asdict, dataclass

import pandas as pd

from ._config import DatasetConfig
from ._load import dataframe_from_path


@dataclass(frozen=True, kw_only=True)
class Dataset(DatasetConfig):
    """A loaded preconfigured dataset."""

    df: pd.DataFrame

    def __post_init__(self) -> None:
        for column, aggregation in self.aggregations.items():
            assert column in self.df.columns  # noqa: S101
            series = self.df[column].head()
            series.agg(aggregation)


def load_dataset(config: DatasetConfig) -> Dataset:
    """Load dataset from config.

    Args:
        config: A dataset configuration object.

    Returns:
        A :class:`Dataset` instance.
    """
    df = dataframe_from_path(config.path, config.index, **config.read_function_kwargs)
    return Dataset(df=df, **asdict(config))
