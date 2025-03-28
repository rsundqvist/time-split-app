from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import pandas as pd
import streamlit as st
import streamlit.config as stc
from rics.strings import format_bytes

from time_split._compat import fmt_sec
from time_fold_explorer import config
from time_fold_explorer._logging import log_perf
from time_fold_explorer.widgets.types import DataSource, QueryParams
from ._datasets import DatasetWidget
from ._sample_data import SampleDataWidget


from .load import VALID_SUFFIXES, error_on_unaggregated_data, read_file, make_formatter


@dataclass(frozen=True)
class DataWidget:
    sample_data: SampleDataWidget | pd.DataFrame | None = field(default_factory=SampleDataWidget)
    """Set to ``None`` to disable selection of the default timeseries sample data."""
    upload: bool = True
    """Enable to allow user data uploads."""
    datasets: DatasetWidget = field(default_factory=DatasetWidget)
    """Widget used to load included datasets."""

    n_samples: int = -1
    """Number of sample rows to show.

    Set to 0 to hide the sampled data view, or -1 to show all rows. Set to ``None`` to disable entirely.
    """

    def select_data(
        self,
    ) -> tuple[pd.DataFrame, tuple[pd.Timestamp, pd.Timestamp], DataSource, dict[str, str], str | None]:
        """Show data selection widget."""
        start = perf_counter()

        df, _, source, aggregations, dataset = self._select_data()

        df = df.convert_dtypes()
        limits = df.index.min(), df.index.max()

        n_rows, n_cols = df.shape
        st.caption(
            f"Finished loading dataset of type `{source.name.lower().replace('_', ' ')}` "
            f"and `shape={n_rows}x{n_cols}` in `{fmt_sec(perf_counter() - start)}`."
        )
        return df, limits, source, aggregations, dataset

    def _select_data(self) -> tuple[pd.DataFrame, float, DataSource, dict[str, str], str | None]:
        st.subheader("Select data", divider="rainbow")
        sources = self.get_data_sources()

        options = [*sources]

        if (query_data := QueryParams.get().data) is None:
            index = 0
        elif isinstance(query_data, tuple):
            index = options.index(DataSource.GENERATE)
        else:
            index = options.index(DataSource.BUNDLED)

        source = st.radio(
            "data-source",
            options,
            index=index,
            captions=[*sources.values()],
            horizontal=True,
            label_visibility="collapsed",
        )
        assert source is not None

        with st.container(border=True):
            return self._load_data(source)

    @classmethod
    def upload_dataset(cls) -> pd.DataFrame:
        """Let the user upload their own data."""
        start = perf_counter()
        file = st.file_uploader("upload-file", type=VALID_SUFFIXES, label_visibility="collapsed")

        if file is None:
            st.sidebar.info("Click `⚙️ Configure data` and select a dataset to continue.", icon="ℹ️")
            msg = "No data selected. Click `⚙️ Configure data` and select a dataset to continue."
            raise ValueError(msg)

        with TemporaryDirectory("time-split") as tmp:
            path = Path(tmp) / file.name
            path.write_bytes(file.read())
            df = read_file(str(path))

        # Record performance
        seconds = perf_counter() - start
        msg = f"Read file `'{file.name}'` of size `{format_bytes(file.size)}` (`shape={df.shape}`) in `{fmt_sec(seconds)}`."
        log_perf(
            msg,
            df,
            seconds,
            extra={"file": file.name, "id": file.file_id, "type": file.type, "bytes": file.size},
        )
        st.caption(msg)

        return df

    def _load_data(self, source: DataSource) -> tuple[pd.DataFrame, float, DataSource, dict[str, str], str | None]:
        df: pd.DataFrame | None = None
        aggregations: dict[str, str] = {}
        dataset: str | None = None

        start = perf_counter()
        if source == DataSource.GENERATE:
            if self.sample_data is None:
                raise ValueError("No sample data widget configured.")
            df = df if isinstance(self.sample_data, pd.DataFrame) else self.sample_data.select()
        if source == DataSource.USER_UPLOAD:
            df = self.upload_dataset()
        if source == DataSource.BUNDLED:
            df, aggregations, dataset = self.datasets.select()

        if df is None:
            raise NotImplementedError(f"{source=}")

        if not isinstance(df.index, pd.DatetimeIndex):
            if source != DataSource.USER_UPLOAD:
                msg = f"Data must have a DatetimeIndex: {df.index}"
                raise TypeError(msg)
            df = self._select_index(df)

        df = df.sort_index()
        error_on_unaggregated_data(df)
        seconds = perf_counter() - start

        return df, seconds, source, aggregations, dataset

    @classmethod
    def show_data_overview(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Create data overview."""
        start = perf_counter()

        st.subheader("Overview", divider="rainbow")

        frames = [
            df.dtypes.rename("dtype"),
            df.memory_usage(index=False, deep=True).rename("memory").map(format_bytes),
            df.isna().mean().map("{:.2%}".format).rename("nan"),
            df.min().rename("min"),
            df.mean().rename("mean"),
            df.max().rename("max"),
            df.sum().rename("sum"),
        ]

        details = pd.concat(frames, axis=1)
        details.index.name = "Column"

        memory = df.memory_usage(index=True, deep=True)
        long = 9999
        st.caption(
            f"Data has shape `{len(df)}x{len(df.columns)}` and contains `{df.size:{'_d' if df.size > long else ''}}` "
            f"elements, using `{format_bytes(memory.sum())}` of memory (including `{format_bytes(memory['Index'])}` for"
            f" `index='{df.index.name}'` of type `{type(df.index).__name__}[{df.index.dtype}]`)."
        )
        st.dataframe(details, use_container_width=True)

        # Record performance
        seconds = perf_counter() - start
        msg = f"Created overview for data of `shape={df.shape}` in `{fmt_sec(seconds)}`."
        log_perf(
            msg,
            df,
            seconds,
            extra={"aggregations": sorted(details), "frame": "data-overview"},
        )
        st.caption(msg)

        return details

    def show_data(self, df: pd.DataFrame) -> None:
        st.subheader("Data", divider="rainbow")

        df, info = self._head(df)
        st.dataframe(df.reset_index(), hide_index=False, use_container_width=True)
        st.caption(info)

    def plot_data(self, df: pd.DataFrame) -> None:
        start = perf_counter()

        df, info = self._head(df)

        ax = df.plot()
        ax.figure.suptitle(df.index.name)
        ax.set_xlabel(None)
        ax.figure.autofmt_xdate()

        with st.container(border=True):
            st.pyplot(ax.figure, dpi=config.FIGURE_DPI)

        seconds = perf_counter() - start
        msg = f"Created `raw` figure for data of `shape={df.shape}` in `{fmt_sec(seconds)}`."
        log_perf(msg, df, seconds, extra={"figure": "raw"})
        st.caption(msg + " " + info)

    def _head(self, df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
        n_df = len(df)
        head = df.head(self.n_samples) if (0 < self.n_samples < n_df) else df
        n_head = len(head)

        pretty_head = make_formatter(n_head)(n_head)
        pretty_df = make_formatter(n_df)(n_df)

        return (
            head,
            f"Showing {'all' if n_df == n_head else 'the first'} `{pretty_head}` of `{pretty_df}` (`{n_head / n_df :.2%}`) rows.",
        )

    def get_data_sources(self) -> dict[DataSource, str]:
        sources = {}

        data = QueryParams.get().data

        if self.sample_data or isinstance(data, tuple):
            sources[DataSource.GENERATE] = "Timeseries in a selected range."
        if self.upload is not False:
            limit = stc.get_option("server.maxUploadSize")
            sources[DataSource.USER_UPLOAD] = f"Size limit {limit} MB."
        if (self.datasets and self.datasets.has_data) or isinstance(data, (int, str)):
            sources[DataSource.BUNDLED] = f"Select one of {self.datasets.size} included datasets."

        return sources

    @classmethod
    def select_range_subset(cls, df: pd.DataFrame) -> tuple[pd.DataFrame, tuple[pd.Timestamp, pd.Timestamp]]:
        min_value = df.index[0].to_pydatetime()
        max_value = df.index[-1].to_pydatetime()

        with st.container(border=True):
            st.subheader("Subset range", divider="red")
            st.caption("Select a subset of the available range of data.")

            with st.container(border=True):
                start, end = st.slider(
                    "partial-range",
                    min_value=min_value,
                    max_value=max_value,
                    value=(min_value, max_value),
                    step=pd.Timedelta(minutes=5).to_pytimedelta(),
                    format="YYYY-MM-DD HH:mm:ss",
                    help="Drag the sliders to use a subset of the original data.",
                    label_visibility="collapsed",
                )

            avail = (max_value - min_value).total_seconds()
            used = (end - start).total_seconds()
            st.caption(
                f"You've selected `{fmt_sec(used)}` of `{fmt_sec(avail)}` "
                f"(`{used / avail :.1%}`) of the total available data range."
            )

        df = df[start:end]
        limits = df.index.min(), df.index.max()
        return df, limits

    @staticmethod
    def _select_index(df: pd.DataFrame) -> pd.DataFrame:
        index: None | int = None

        lower: pd.Index = df.columns.map(str.lower)
        for s in "date", "time", "datetime", "timestamp":
            try:
                index = lower.get_loc(s)
                break
            except KeyError:
                pass

        def format_func(column: str) -> str:
            return f"{column} [{df.dtypes[column]}]"

        selection = st.selectbox(
            "Select index column",
            options=df.columns,
            format_func=format_func,
            index=index,
        )
        if selection is None:
            st.info(
                "Select a [datetime](http://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.Timestamp.html)-like index column to continue.",
                icon="ℹ️",
            )
            st.stop()

        columns = df[selection]
        max_to_show = 3
        st.code((columns.sample(max_to_show) if len(columns) > max_to_show else columns).map(repr).to_string())

        try:
            datetime_index = pd.DatetimeIndex(columns.astype(str))
        except Exception as e:
            st.exception(e)
            st.stop()

        df[selection] = datetime_index
        df = df.set_index(selection)

        return df

    @classmethod
    def show_summary(cls, df: pd.DataFrame) -> None:
        index_start, index_end = df.index.min(), df.index.max()
        summary = {
            "Rows": len(df),
            "Cols": len(df.columns),
            "Start": index_start,
            "Span": fmt_sec((index_end - index_start).total_seconds()),
            "End": index_end,
            "Size": format_bytes(df.memory_usage(deep=True, index=True).sum(), decimals=1),
        }
        st.dataframe(
            pd.Series(summary).to_frame().T,
            hide_index=True,
            use_container_width=True,
            selection_mode="single-column",
        )
