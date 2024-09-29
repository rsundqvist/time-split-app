"""Widget enumeration types.

Typically used as the return type for user controls.
"""

import dataclasses as _dataclasses
import datetime as _datetime
import typing as _t
from enum import StrEnum as _StrEnum

import pandas as _pd
from rics import paths as _paths

from time_fold_explorer import config as _c


class DataSource(_StrEnum):
    """Data source type choices."""

    GENERATE = ":magic_wand: Generate sample data"
    USER_UPLOAD = ":arrow_up: Upload dataset"
    BUNDLED = ":gift: Select bundled dataset"


class ScheduleType(_StrEnum):
    """Input choices for schedule widgets."""

    CRON = "Cron :calendar:"
    DURATION = "Duration :stopwatch:"
    FREE_FORM = "Free form :memo:"


class Filters(_t.NamedTuple):
    """Schedule/fold filtering parameters."""

    limit: int
    step: int


class SpanType(_StrEnum):
    """Input choices for span `(i.e. before/after)` widgets."""

    """Schedule input types."""

    STEP = "Step :ladder:"
    DURATION = "Duration :stopwatch:"
    ALL = "All data :100:"
    FREE_FORM = "Free form :memo:"


class ExpandLimitsType(_StrEnum):
    """Input choices for limits expansion widgets."""

    AUTO = "Automatic :left_right_arrow:"
    DISABLED = "Disabled :no_entry_sign:"
    FREE_FORM = "Free form :memo:"


class BarLabels(_StrEnum):
    """Bar label preference in figures."""

    DAYS = ":calendar: Days"
    HOURS = ":alarm_clock: Hours"
    ROWS = ":bar_chart: Row count"
    DISABLED = ":ghost: Hide"


class RemovedFolds(_StrEnum):
    """Display filtered folds in figures."""

    SHOW = ":ghost: Show"
    HIDE = ":no_entry_sign: Hide"


class TypePreference(_StrEnum):
    """Copy-paste type preference."""

    STRING = ":abcd: Plain strings"
    PYTHON = ":snake: Built-in Python types"
    PANDAS = ":panda_face: Pandas types"


@_dataclasses.dataclass(frozen=True, kw_only=True)
class DatasetConfig:
    """A preconfigured dataset."""

    label: str
    path: str
    index: str
    aggregations: dict[str, str] = _dataclasses.field(default_factory=dict)
    description: str = ""
    read_function_kwargs: dict[str, _t.Any] = _dataclasses.field(default_factory=dict)
    _section: str | None = None

    @classmethod
    def load_if_exists(cls, path: _paths.AnyPath = _c.DATASETS_CONFIG_PATH) -> tuple[_t.Self, ...] | None:
        """Read a configuration file, returning ``None`` if it does not exist."""
        try:
            return cls.load(path)
        except FileNotFoundError:
            from time_fold_explorer._logging import LOGGER

            if _c.REQUIRE_DATASETS:
                from os import _exit as force_exit

                LOGGER.critical(f"Failed to load {path=}. Refusing to start since REQUIRE_DATASETS=True.")
                force_exit(52)  # regular exit will not halt the underlying server.

            LOGGER.warning(f"Dataset {path=} does not exist. No datasets will be loaded.")
            return None

    @classmethod
    def load(cls, file: _paths.AnyPath = _c.DATASETS_CONFIG_PATH) -> tuple[_t.Self, ...]:
        """Read a configuration file, returning a list of config objects."""
        import tomllib
        from pathlib import Path

        def check_config(path: Path) -> None:
            if not path.is_file():
                raise FileNotFoundError

        with _paths.any_path_to_path(file, postprocessor=check_config).open("rb") as f:
            raw = tomllib.load(f)

        configs = []
        config: dict[str, _t.Any]
        for section, config in raw.items():
            config.setdefault("label", section)

            try:
                cfg = cls(**config, _section=f"[{section}]")
            except Exception as e:
                e.add_note(f"{section=}")
                e.add_note(f"{config=}")
                e.add_note(f"{file=}")
                raise
            configs.append(cfg)

        return tuple(configs)

    def __post_init__(self) -> None:
        if self.path in _CHECKED_CONFIG_PATHS:
            return

        _CHECKED_CONFIG_PATHS.add(self.path)

        assert self.path, f"{self.path=}"
        assert self.index, f"{self.index=}"
        assert self.label, f"{self.label=}"

        if not self.description:
            import warnings

            msg = f"Description missing: {self}."
            warnings.warn(msg, stacklevel=2)


@_dataclasses.dataclass(frozen=True, kw_only=True)
class Dataset(DatasetConfig):
    """A loaded preconfigured dataset."""

    df: _pd.DataFrame

    @classmethod
    def from_config(cls, df: _pd.DataFrame, config: DatasetConfig) -> _t.Self:
        """Create from config object."""
        return cls(df=df, **_dataclasses.asdict(config))

    def __post_init__(self) -> None:
        for column, aggregation in self.aggregations.items():
            assert column in self.df.columns
            series = self.df[column].head()
            series.agg(aggregation)


_CHECKED_CONFIG_PATHS: set[str] = set()


@_dataclasses.dataclass(frozen=True, kw_only=True)
class QueryParams:
    """Parameters which may be passed as arguments in the URL.

    For example http://localhost:8501/?n_splits=3&step=3&show_removed=true will give

    >>> QueryParams(step=3, n_splits=3, show_removed=True)

    http://localhost:8501/?n_splits=3&step=3&show_removed=true&dataset=data.json.gzip

    These are later used to set the initial values in various widgets.
    """

    schedule: str | None = None
    step: int | None = None
    n_splits: int | None = None
    before: str | None = None
    after: str | None = None
    expand_limits: bool | str | None = None

    show_removed: bool | None = None
    data: int | str | tuple[_datetime.datetime, _datetime.datetime] | None = None
    """Data selection.

    If an ``int`` or ``str``, it is assumed to refer to a :attr:`DatasetConfig.label`, either by index or by the label
    itself. Labels are normalized using :meth:`normalize_dataset`.

    May also be a tuple of UNIX timestamps, specified on the form ``<start>-<stop>``, e.g. ``1556668800-1557606600``
    for a range ``('2019-05-01T00:00:00z', '')``. Tuples are converted using :meth:`convert_timestamps`. Note that
    timestamps are coerced into 5-minute increments as naive UTC timestamps.
    """

    @classmethod
    def normalize_dataset(cls, data: str) -> str:
        """Normalize a dataset label."""
        # Remove stars/backticks (Markdown bold/monospace), white and force lower case.
        return data.replace("*", "").replace("`", "").replace(" ", "").lower()

    @classmethod
    def convert_timestamps(
        cls,
        start: int,
        end: int,
        *,
        utc: bool = False,
    ) -> tuple[_datetime.datetime, _datetime.datetime]:
        """Convert a pair of UNIX timestamps into datetime instances.

        Args:
            start: Start of the range.
            end: End of the range.
            utc: If ``True``, tz-aware UTC instances are returned.

        Returns:
            A tuple of two timestamps.
        """
        tz = _datetime.timezone.utc if utc else None

        def _convert(ts: int) -> _datetime.datetime:
            dt = _datetime.datetime.fromtimestamp(ts, tz)

            # Round to nearest multiple of 5 minutes = 300 seconds
            seconds = 60.0 * dt.minute + dt.second + dt.microsecond / 1000000.0
            timedelta = _datetime.timedelta(seconds=round(seconds / 300.0) * 300.0)
            return dt.replace(minute=0, second=0, microsecond=0) + timedelta

        return _convert(start), _convert(end)

    @classmethod
    def get(cls) -> _t.Self:
        """Get the session query parameters object."""
        from streamlit import session_state

        if "query" not in session_state:
            cls.set()

        return session_state["query"]  # type: ignore[no-any-return]

    @classmethod
    def set(cls) -> _t.Self:
        """Set the session query parameters object."""
        from streamlit import session_state, query_params

        qp = cls.make(**query_params)
        session_state["query"] = qp

        return qp

    def to_dict(self, prefix: str = "", filter: bool = True) -> dict[str, int | bool | str]:
        """Return self as a dict with ``None`` values.

        Args:
            prefix: Key prefix.
            filter: If ``True``, remove ``None`` values.

        Returns:
            String representation of ``self``.
        """
        d = _dataclasses.asdict(self)
        if filter:
            d = {k: v for k, v in d.items() if v is not None}
        if prefix:
            d = {prefix + k: v for k, v in d.items()}
        return d

    @classmethod
    def make(cls, **kwargs: _t.Any) -> _t.Self:
        """Construct a new instance keyword arguments."""

        # TODO what happens if someone sends a query string with millions of zeros?

        for parameter in "step", "n_splits":
            if (value := kwargs.get(parameter)) is not None:
                kwargs[parameter] = int(value)

        for parameter in ("show_removed",):
            if b := cls._as_bool(kwargs, parameter) is not None:
                kwargs[parameter] = b

        expand_limits: bool | str | None
        if (expand_limits := kwargs.get("expand_limits")) is not None:
            try:
                expand_limits = cls._as_bool(kwargs, "expand_limits")
            except ValueError:
                if expand_limits.lower() == "auto":
                    expand_limits = True
            kwargs["expand_limits"] = expand_limits

        if "data" in kwargs:
            value = kwargs["data"]
            if (as_range := cls._as_range(value)) is None:
                try:
                    kwargs["data"] = int(value)
                except ValueError:
                    pass  # Dataset label
            else:
                start, end = cls.convert_timestamps(*as_range, utc=True)
                kwargs["data"] = start.replace(tzinfo=None), end.replace(tzinfo=None)

        return cls(**kwargs)

    @classmethod
    def _as_bool(cls, kwargs: dict[str, _t.Any], parameter: str) -> None | bool:
        if (value := kwargs.get(parameter)) is None:
            return None

        lower = value.lower()
        if lower in {"1", "true"}:
            return True
        elif lower in {"0", "false"}:
            return False

        raise ValueError(f"Bad {value=} for {parameter=}")

    @classmethod
    def _as_range(cls, value: str) -> None | tuple[int, int]:
        if value.count("-") != 1:
            return None

        left, _, right = value.partition("-")

        try:
            start = int(left)
        except Exception:
            return None
        try:
            end = int(right)
        except Exception:
            return None

        min_timestamp = 631152000  # timestamp of 1990-01-01, minimum date in select_datetime()
        return (start, end) if (start >= min_timestamp and end >= min_timestamp) else None
