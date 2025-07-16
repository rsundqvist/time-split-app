"""Datasets on disk."""

from ._config import USE_ORIGINAL_INDEX, DatasetConfig, load_dataset_configs
from ._datasets import Dataset, load_dataset
from ._load import DuplicateIndexError, dataframe_from_path
from ._read_fn import COMPRESSION_SUFFIXES, FILE_SUFFIXES, get_pandas_read_function

__all__ = [
    "COMPRESSION_SUFFIXES",
    "FILE_SUFFIXES",
    "USE_ORIGINAL_INDEX",
    "Dataset",
    "DatasetConfig",
    "DuplicateIndexError",
    "dataframe_from_path",
    "get_pandas_read_function",
    "load_dataset",
    "load_dataset_configs",
]
