from typing import Any

import pandas as pd

from ._config import USE_ORIGINAL_INDEX
from ._read_fn import get_pandas_read_function


def dataframe_from_path(path: str, index: str, verify: bool = True, **kwargs: Any) -> pd.DataFrame:
    """Read dataframe from path.

    Args:
        path: A path. The read function to use is derived based on the file suffix(es).
        index: Index column. Pass ``{USE_ORIGINAL_INDEX!r}`` if the frame on disk already has a datetime-like index.
        verify: If ``True``, verify the index.
        **kwargs: Keyword arguments for the read function.

    Returns:
        A pandas DataFrame.

    Raises:
        DuplicateIndexError: If the data is not aggregated (only if `verify` is ``True``).
    """
    pandas_read_fn = get_pandas_read_function(path)
    df = pandas_read_fn(path, **kwargs)

    if index == USE_ORIGINAL_INDEX:
        if not isinstance(df.index, pd.DatetimeIndex):
            raise TypeError(f"Bad index; expected a {pd.DatetimeIndex.__name__} but got {type(df.index).__name__}.")
    else:
        df[index] = pd.to_datetime(df[index].astype(str))
        df = df.set_index(index)

    if verify is False or df.index.is_unique:
        return df

    raise DuplicateIndexError(df)


dataframe_from_path.__doc__ = dataframe_from_path.__doc__.format(USE_ORIGINAL_INDEX=USE_ORIGINAL_INDEX)  # type: ignore[union-attr]


class DuplicateIndexError(Exception):
    """Error raised when unaggregated data is detected."""

    def __init__(self, df: pd.DataFrame, head: int = 5) -> None:
        super().__init__("Data must be pre-aggregated.")
        self._size = len(df)

        index = df.index
        self._name = index.name

        duplicates = df.loc[index.duplicated(False)]
        self._n_duplicates = len(duplicates)

        if len(duplicates) > head:
            duplicates = duplicates.head(head)

        self._samples = duplicates.sort_index(ascending=False)
        self.add_note(f"Sample data (showing 3/{self._n_duplicates} duplicate rows):\n{self._samples.head(3)}")

    @property
    def samples(self) -> pd.DataFrame:
        """Sample data with duplicated index values."""
        return self._samples

    @property
    def n_duplicated(self) -> int:
        """Total number of duplicated index values."""
        return self._n_duplicates

    @property
    def n_total(self) -> int:
        """Total number of rows in the original frame."""
        return self._size
