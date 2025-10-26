from dataclasses import dataclass, field
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

import pandas as pd
import streamlit as st
import streamlit.config as stc
from rics.strings import format_bytes, format_seconds
from ._data_loader_widget import DataLoaderWidget
from time_split_app.datasets import get_pandas_read_function, COMPRESSION_SUFFIXES, FILE_SUFFIXES
from ..types import DataSource, QueryParams
from ... import config
from ..._logging import log_perf
from ._datasets import DatasetWidget
from ._sample_data import SampleDataWidget
from ._loader_from_env_entrypoint import from_env_entrypoint
from .load import error_on_unaggregated_data, make_formatter


def _get_upload_limit() -> int:
    return int(stc.get_option("server.maxUploadSize"))


@dataclass(frozen=True)
class DataWidget:
    sample_data: SampleDataWidget | None = (
        field(default_factory=SampleDataWidget) if config.ENABLE_DATA_GENERATOR else None
    )
    """Set to ``None`` to disable selection of the default timeseries sample data."""
    upload: bool = _get_upload_limit() > 0
    """Enable user data uploads."""
    datasets: DatasetWidget = field(default_factory=DatasetWidget)
    """Widget used to load included datasets."""
    custom_dataset_loader: list[DataLoaderWidget] = field(default_factory=from_env_entrypoint)
    """List of user-defined loader implementations."""

    n_samples: int = -1
    """Number of sample rows to show.

    Set to 0 to hide the sampled data view, or -1 to show all rows. Set to ``None`` to disable entirely.
    """

    def select_data(
        self,
    ) -> tuple[pd.DataFrame, tuple[pd.Timestamp, pd.Timestamp], DataSource, dict[str, str], str | bytes | None]:
        """Show data selection widget."""
        start = perf_counter()

        df, _, source, aggregations, dataset = self._select_data()

        df = df.convert_dtypes()
        limits = df.index.min(), df.index.max()

        n_rows, n_cols = df.shape
        st.caption(
            f"Finished loading dataset of type `{source.name.lower().replace('_', ' ')}` "
            f"and `shape={n_rows}x{n_cols}` in `{format_seconds(perf_counter() - start)}`."
        )
        return df, limits, source, aggregations, dataset

    def _select_data(self) -> tuple[pd.DataFrame, float, DataSource, dict[str, str], str | bytes | None]:
        st.subheader("Select data", divider="rainbow")
        sources = self.get_data_sources()

        titles = {}
        captions = []
        for (src, index), (title, caption) in sources.items():
            titles[(src, index)] = title
            captions.append(caption)
        options = [*sources]

        if not options:
            raise ValueError("All data source options have been disabled.")

        if (query_data := QueryParams.get().data) is None:
            index = 0
        elif isinstance(query_data, tuple):
            index = options.index((DataSource.GENERATE, None))
        elif isinstance(query_data, bytes):
            index = options.index((DataSource.CUSTOM_DATASET_LOADER, 0))
        else:
            index = options.index((DataSource.BUNDLED, None))

        source, variant = st.radio(
            "data-source",
            options,
            index=index,
            captions=captions,
            horizontal=True,
            format_func=titles.__getitem__,
            label_visibility="collapsed",
        )
        assert source is not None

        return self._load_data(source, variant)

    @classmethod
    def upload_dataset(cls) -> pd.DataFrame:
        """Let the user upload their own data."""
        start = perf_counter()

        suffixes = [*FILE_SUFFIXES, *COMPRESSION_SUFFIXES]
        file = st.file_uploader("upload-file", type=suffixes, label_visibility="collapsed")

        if file is None:
            st.sidebar.info("Click `⚙️ Configure data` and select a dataset to continue.", icon="ℹ️")
            msg = "No data selected. Click `⚙️ Configure data` and select a dataset to continue."
            raise ValueError(msg)

        read_fn = get_pandas_read_function(file.name)
        with TemporaryDirectory("time-split") as tmp:
            path = Path(tmp) / file.name
            path.write_bytes(file.read())
            df = read_fn(str(path))

        # Record performance
        seconds = perf_counter() - start
        msg = f"Read file `'{file.name}'` of size `{format_bytes(file.size)}` (`shape={df.shape}`) in `{format_seconds(seconds)}`."
        log_perf(
            msg,
            df,
            seconds,
            extra={"file": file.name, "id": file.file_id, "type": file.type, "bytes": file.size},
        )
        st.caption(msg)

        return df

    def _load_data(
        self,
        source: DataSource,
        variant: int | None,
    ) -> tuple[pd.DataFrame, float, DataSource, dict[str, str], str | bytes | None]:
        aggregations: dict[str, str] = {}
        dataset: str | bytes | None = None

        start = perf_counter()

        df: pd.DataFrame | None
        match source:
            case DataSource.GENERATE:
                if self.sample_data is None:
                    raise ValueError("No sample data widget configured.")
                df = self.sample_data.load(None)
            case DataSource.USER_UPLOAD:
                df = self.upload_dataset()
            case DataSource.BUNDLED:
                df, aggregations, dataset = self.datasets.select()
            case DataSource.CUSTOM_DATASET_LOADER:
                assert variant is not None
                df, aggregations, dataset = self._handle_custom_loader(variant)
            case _:
                raise TypeError(f"{source=}")

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

    def _handle_custom_loader(self, variant: int) -> tuple[pd.DataFrame, dict[str, str], bytes | None]:
        loader = self.custom_dataset_loader[variant]

        if variant == 0:
            params = QueryParams.get().data
            if not isinstance(params, bytes):
                params = None
        else:
            params = None
        result = loader.load(params)

        def error_msg() -> str:
            return (
                f"Bad implementation {type(loader).__qualname__}: "
                f"Must return either a tuple `(df, aggregations, params)` or just `DataFrame`. Got: {result}."
            )

        if isinstance(result, tuple):
            if len(result) != 3:
                raise TypeError(error_msg())
            df, aggregations, params = result

            if params and variant > 0:
                with st.container(border=True):
                    st.warning("Params are only supported for the primary loader.", icon="⚠️")
                    st.text("The parameters")
                    st.code(params)
                    st.text("returned by")
                    st.code(loader)
                    st.text("will be ignored.")

                params = None

            elif not isinstance(params, bytes):
                raise TypeError(error_msg())

            if not isinstance(aggregations, dict):
                raise TypeError(error_msg())

        else:
            df = result
            aggregations = {}
            params = None

        if not isinstance(df, pd.DataFrame):
            raise TypeError(error_msg())

        return df, aggregations, params

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
        st.dataframe(details, width="stretch")

        # Record performance
        seconds = perf_counter() - start
        msg = f"Created overview for data of `shape={df.shape}` in `{format_seconds(seconds)}`."
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
        st.dataframe(df.reset_index(), hide_index=False, width="stretch")
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
        msg = f"Created `raw` figure for data of `shape={df.shape}` in `{format_seconds(seconds)}`."
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
            f"Showing {'all' if n_df == n_head else 'the first'} `{pretty_head}` of `{pretty_df}` (`{n_head / n_df:.2%}`) rows.",
        )

    def get_data_sources(self) -> dict[tuple[DataSource, int | None], tuple[str, str]]:
        sources: dict[tuple[DataSource, int | None], tuple[str, str]] = {}

        qp = QueryParams.get()
        data = qp.data

        if self.sample_data or isinstance(data, tuple):
            if self.sample_data is None:
                raise ValueError(f"Cannot use {qp!r} with {config.ENABLE_DATA_GENERATOR=}.")
            sources[DataSource.GENERATE, None] = (
                self.sample_data.get_title(),
                self.sample_data.get_description(),
            )

        if self.upload:
            sources[DataSource.USER_UPLOAD, None] = (
                DataSource.USER_UPLOAD.value,
                f"Limit {_get_upload_limit()} MB.",
            )

        if (self.datasets and self.datasets.has_data) or isinstance(data, (int, str)):
            sources[DataSource.BUNDLED, None] = (
                DataSource.BUNDLED.value,
                f"Select one of {self.datasets.size} datasets.",
            )

        for i, loader in enumerate(self.custom_dataset_loader):
            sources[(DataSource.CUSTOM_DATASET_LOADER, i)] = (
                loader.get_title(),
                loader.get_description(),
            )

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
                f"You've selected `{format_seconds(used)}` of `{format_seconds(avail)}` "
                f"(`{used / avail:.1%}`) of the total available data range."
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
            "Span": format_seconds((index_end - index_start).total_seconds()),
            "End": index_end,
            # "Size": format_bytes(df.memory_usage(deep=True, index=True).sum(), decimals=1),
        }
        st.dataframe(
            pd.Series(summary).to_frame().T,
            hide_index=True,
            width="stretch",
            selection_mode="single-column",
        )
