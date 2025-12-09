"""Dummy extensions for the Time Split application.

See https://time-split.readthedocs.io/en/latest/api/time_split.app.reexport.html for documentation.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Self

import numpy as np
import pandas as pd
import streamlit as st

from time_split_app.widgets import DataLoaderWidget


@dataclass
class MyDatasetParams:
    """Custom parameter class.

    Internal representation of the `params` argument passed to ``MyDatasetLoader.load()``.
    """

    ballons: bool = False
    periods: int = 999

    @classmethod
    def from_bytes(cls, params: bytes) -> Self:
        """Deserialize from JSON bytes."""
        string = params.decode()
        deserialized = json.loads(string)
        return cls(**deserialized)

    def to_bytes(self) -> bytes:
        """Serialize to JSON bytes."""
        serialized = json.dumps(asdict(self))
        return bytes(serialized.encode())


class MyDatasetLoader(DataLoaderWidget):
    """Generates arbitrary datasets (possibly from user input).

    The class should not have any required constructor arguments, but you may point ``DATASET_LOADER`` to an initialized
    instance.
    """

    def get_title(self) -> str:
        """Title shown in the `⚙️ Configure data` menu. Uses Markdown syntax."""
        return f"🎉 Use `{MyDatasetLoader.__name__}`!"

    def get_description(self) -> str:
        """Brief description shown in the `⚙️ Configure data` menu. Uses Markdown syntax."""
        return "It's a `time-split-app` party!"

    def get_prefix(self) -> bytes | None:
        """Return a loader prefix. Generated automatically if ``None``.

        Used to identify the loader when :attr:`.QueryParams.data` is round-tripped.
        """
        return None

    def load(self, params: bytes | None) -> tuple[pd.DataFrame, dict[str, str], bytes] | pd.DataFrame:
        """Load data.

        .. note::

           This method will be called many times due to the Streamlit data model.

        You may want to use ``@streamlit.cache_data`` or ``@streamlit.cache_resource`` to improve performance. See
        https://docs.streamlit.io/develop/concepts/architecture/caching
        for more information.

        Args:
            params: Parameter preset as bytes. Handling is implementation-specific.

        Returns:
            A :class:`pandas.DataFrame` or a tuple ``(data, aggregations, params)``, where the ``params: bytes`` may be given as
            the `params` argument to recreate the frame returned.

        See :attr:`.QueryParams.data` for more information regarding the `params` argument.
        """
        p = MyDatasetParams.from_bytes(params) if params else MyDatasetParams()

        with st.container(border=True):
            with st.container(horizontal=True):
                p.ballons = st.toggle("Balloons!", p.ballons)
                p.periods = st.slider("Periods", 1, 9999, p.periods)

            start, end = self.select_range(
                initial=(datetime.fromisoformat("2019-04-01"), datetime.fromisoformat("2019-05-11T20:30:00")),
                date_only=False,
                start_options=["absolute"],
                end_options=["absolute", "relative"],
            )

        df = _generate_data(start, end, p.periods)

        if p.ballons:
            st.balloons()

        aggregations = {c: "sum" for c in df.columns}
        params = p.to_bytes()

        return df, aggregations, params


@st.cache_resource
def _generate_data(start: datetime, end: datetime, periods: int) -> pd.DataFrame:
    index = pd.date_range(start, end, periods=periods)

    x = np.linspace(0, periods / 10, periods)
    f = np.random.default_rng(periods).random(periods).cumsum()

    data = {"dummy": 1 + np.sin(f * x)}

    return pd.DataFrame(data, index=index)
