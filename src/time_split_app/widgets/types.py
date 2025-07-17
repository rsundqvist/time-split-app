"""Widget enumeration types.

Typically used as the return type for user controls.
"""

from base64 import b16decode
from dataclasses import asdict, dataclass
from datetime import datetime, UTC, timedelta
from enum import StrEnum
from typing import NamedTuple, Callable, Any, Self, TYPE_CHECKING

if TYPE_CHECKING:
    try:
        from matplotlib.pyplot import Axes  # type: ignore[attr-defined]
    except ModuleNotFoundError:
        Axes = Any  # type: ignore[misc, assignment]

from time_split.types import DatetimeIndexSplitterKwargs

SelectSplitParams = Callable[[], DatetimeIndexSplitterKwargs]
"""A callable ``() -> DatetimeIndexSplitterKwargs``; see :func:`time_split.split`."""
PlotFn = Callable[..., "Axes"]
"""A callable that mimics interface of :func:`time_split.plot`."""
LinkFn = Callable[..., str]
"""A callable that mimics interface of :func:`time_split.app.create_explorer_link`."""


class DataSource(StrEnum):
    """Data source type choices."""

    GENERATE = "SampleDataWidget.get_title()"
    USER_UPLOAD = ":arrow_up: Upload"
    BUNDLED = ":gift: Select dataset"
    CUSTOM_DATASET_LOADER = "AbstractDataGeneratorWidget.get_title()"


class ScheduleType(StrEnum):
    """Input choices for schedule widgets."""

    CRON = "Cron :calendar:"
    DURATION = "Duration :stopwatch:"
    FREE_FORM = "Free form :memo:"


class Filters(NamedTuple):
    """Schedule/fold filtering parameters."""

    limit: int
    step: int


class SpanType(StrEnum):
    """Input choices for span `(i.e. before/after)` widgets."""

    """Schedule input types."""

    STEP = "Step 🪜"
    DURATION = "Duration :stopwatch:"
    ALL = "All data :100:"
    FREE_FORM = "Free form :memo:"


class ExpandLimitsType(StrEnum):
    """Input choices for limits expansion widgets."""

    AUTO = "Automatic :left_right_arrow:"
    DISABLED = "Disabled :no_entry_sign:"
    FREE_FORM = "Free form :memo:"


class BarLabels(StrEnum):
    """Bar label preference in figures."""

    DAYS = ":calendar: Days"
    HOURS = ":alarm_clock: Hours"
    ROWS = ":bar_chart: Row count"
    DISABLED = ":ghost: Hide"


class RemovedFolds(StrEnum):
    """Display filtered folds in figures."""

    SHOW = ":ghost: Show"
    HIDE = ":no_entry_sign: Hide"


class TypePreference(StrEnum):
    """Copy-paste type preference."""

    STRING = ":abcd: Plain strings"
    PYTHON = ":snake: Built-in Python types"
    PANDAS = ":panda_face: Pandas types"


@dataclass(frozen=True, kw_only=True)
class QueryParams:
    """Parameters which may be passed as arguments in the URL.

    For example http://localhost:8501/?n_splits=3&step=3&show_removed=true will give

    .. code-block::

       QueryParams(step=3, n_splits=3, show_removed=True, ...)

    The params are later used to set the initial values in various widgets.
    """

    schedule: str | None = None
    step: int | None = None
    n_splits: int | None = None
    before: str | None = None
    after: str | None = None
    expand_limits: bool | str | None = None

    show_removed: bool | None = None
    data: int | str | bytes | tuple[datetime, datetime] | None = None
    """Data selection.
    
    Built-in data loaders:
        If an ``int`` or ``str``, it is assumed to refer to a :attr:`.DatasetConfig.label`, either by index or by the
        label itself. Labels are normalized using :meth:`normalize_dataset`.
    
        May also be a tuple of UNIX timestamps, specified on the form ``<start>-<stop>``, e.g. ``1556668800-1557606600``
        for a range ``('2019-05-01T00:00:00z', '2019-05-11T20:30:00z')``. Tuples are converted using 
        :meth:`convert_timestamps`. Note that timestamps are coerced into 5-minute increments as naive UTC timestamps.
        
        This is managed automatically when using the bundled functions.
    
    Custom data loaders:
        If ``bytes``, these are assumed by the the parameters of a custom :class:`.DataLoaderWidget`; the bytes will be
        forwarded to the ``load()``-method of the implementation as-is.
        
        The ``bytes`` data is round tripped (as a base 16 string prefixed by `0x`) when using permalinks; serialization,
        deserialization and validation of the actual content is the responsibility of the implementation.
        
    See Also:
        The :func:`.create_explorer_link` function.
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
    ) -> tuple[datetime, datetime]:
        """Convert a pair of UNIX timestamps into datetime instances.

        Args:
            start: Start of the range.
            end: End of the range.
            utc: If ``True``, tz-aware UTC instances are returned.

        Returns:
            A tuple of two timestamps.
        """
        tz = UTC if utc else None

        def _convert(ts: int) -> datetime:
            dt = datetime.fromtimestamp(ts, tz)

            # Round to nearest multiple of 5 minutes = 300 seconds
            seconds = 60.0 * dt.minute + dt.second + dt.microsecond / 1000000.0
            delta = timedelta(seconds=round(seconds / 300.0) * 300.0)
            return dt.replace(minute=0, second=0, microsecond=0) + delta

        return _convert(start), _convert(end)

    @classmethod
    def get(cls) -> Self:
        """Get the session query parameters object."""
        from streamlit import session_state

        if "query" not in session_state:
            cls.set()

        return session_state["query"]  # type: ignore[no-any-return]

    @classmethod
    def set(cls) -> Self:
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
        d = asdict(self)
        if filter:
            d = {k: v for k, v in d.items() if v is not None}
        if prefix:
            d = {prefix + k: v for k, v in d.items()}
        return d

    @classmethod
    def make(cls, **kwargs: Any) -> Self:
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
                assert isinstance(expand_limits, str)
                if expand_limits.lower() == "auto":
                    expand_limits = True
            kwargs["expand_limits"] = expand_limits

        if "data" in kwargs:
            value = kwargs["data"]

            if isinstance(value, str) and value.startswith("0x"):
                kwargs["data"] = b16decode(value.removeprefix("0x"))
            elif (as_range := cls._as_range(value)) is None:
                try:
                    kwargs["data"] = int(value)
                except ValueError:
                    pass  # Dataset label
            else:
                start, end = cls.convert_timestamps(*as_range, utc=True)
                kwargs["data"] = start.replace(tzinfo=None), end.replace(tzinfo=None)

        return cls(**kwargs)

    @classmethod
    def _as_bool(cls, kwargs: dict[str, Any], parameter: str) -> None | bool:
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
