"""Configuration namespace.

Values in this module are treated as hard limits by the server.
"""

from rics.env import read as _env

# Configurable by application users
PLOT_RAW_TIMESERIES: bool = _env.read_bool("PLOT_AGGREGATIONS_PER_FOLD", True)
"""Enable plot in the `🔍 Show raw data` tab."""
PLOT_AGGREGATIONS_PER_FOLD: bool = _env.read_bool("PLOT_AGGREGATIONS_PER_FOLD", True)
"""Enable plots in the `📈 Aggregations per fold` tab."""
FIGURE_DPI: int = _env.read_int("FIGURE_DPI", 200)
"""Controls figure fidelity. Higher values look better, but is a lot slower."""
MAX_SPLITS = _env.read_int("MAX_SPLITS", 100)
"""Upper fold count limit. Prevents figures from getting too large."""

# Server configuration
RAW_DATA_SAMPLES: int = _env.read_int("RAW_DATA_SAMPLES", 1000)
"""Maximum number of display and plot in `🔍 Show raw data` tab."""
DATASETS_CONFIG_PATH: str = _env.read_str("DATASETS_CONFIG_PATH", "datasets.toml")
"""Dataset configuration TOML path. Disable the dataset view if not found.

May be remote, e.g. ``s3://my-bucket/data/datasets.toml`` for AWS blob storage.
"""
REQUIRE_DATASETS: bool = _env.read_bool("REQUIRE_DATASETS", False)
"""If set, refuse to start if the :attr:`DATASETS_CONFIG_PATH` file cannot be read or is invalid."""
DATASET_CONFIG_CACHE_TTL: int = _env.read_int("DATASET_CONFIG_CACHE_TTL", 30)
"""Frequency with which the :attr:`DATASETS_CONFIG_PATH` is read."""
DATASET_CACHE_TTL: int = _env.read_int("DATASET_CACHE_TTL", 12 * 60 * 60)
"""Cache timeout in seconds. Default is twelve hours."""
DATASET_RADIO_LIMIT: int = _env.read_int("DATASET_RADIO_LIMIT", 3)
"""Maximum number of dataset options to show as radio buttons.

Radio buttons are shown with one-line descriptions and all options visible at once. If this limit is exceeded, the UI
shows a label-only dropdown menu instead. Set to zero to always use the dropdown menu.
"""
ENABLE_DATA_GENERATOR: bool = _env.read_bool("ENABLE_DATA_GENERATOR", True)
"""Set to ``False`` to disable the built-in dataset generator."""
DATA_GENERATOR_INITIAL_RANGE_FN: str = _env.read_str("DATA_GENERATOR_INITIAL_RANGE_FN")
"""Initial range callback for generated data.

* Type: ``() -> (start, end)``.
* Format: ``path.to.module:func_name``.
"""

PROCESS_QUERY_PARAMS: bool = _env.read_bool("PROCESS_QUERY_PARAMS", True)
"""Abort if URL parameters are given when ``False``."""
PERMALINK_BASE_URL: str = _env.read_str("PERMALINK_BASE_URL")
"""Public base address for the application. Used to create permalinks."""
USE_CUSTOM_CSS: bool = _env.read_bool("USE_CUSTOM_CSS", True)
"""Disable to use the default Streamlit styling."""

CONFIGURE_PLOTTING = _env.read_bool("CONFIGURE_PLOTTING", True)
"""Set to ``False`` to disable the default plotting style setup."""
CONFIGURE_LOGGING = _env.read_bool("CONFIGURE_LOGGING", True)
"""Set to ``False`` to disable the default logging setup."""
PERFORMANCE_LOG_LEVEL: int = _env.read_int("PERFORMANCE_LOG_LEVEL", 20)
"""Level for the `time_split_app.performance` logger. Default is ``logging.INFO=20``."""

DATE_ONLY: bool = _env.read_bool("DATE_ONLY", True)
"""If ``True``, lock set the app in `date_only` mode wherever possible."""

# Image extensions.
DATASET_LOADER: list[str] = _env.read_str("DATASET_LOADER", split=",")
"""A custom loader implementation.

* Type: :class:`.DataLoaderWidget`
* Format: ``path.to.module:ClassName`` (or an instance thereof).

Use comma-separated specs to use multiple custom loaders.
"""

SPLIT_SELECT_FN: str = _env.read_str("SPLIT_SELECT_FN")
"""Custom splitting parameters selection function.

* Type: ``() -> DatetimeIndexSplitterKwargs``.
* Format: ``path.to.module:func_name``.

To read params produced by :func:`.create_explorer_link()`, use

>>> from time_split_app.widgets.types import QueryParams
>>> QueryParams.get()

Of course, you may also choose to handle this yourself using ``st.query_params``.
"""

PLOT_FN: str = _env.read_str("PLOT_FN")
"""A custom plotting function; same interface as :func:`time_split.plot()`.

* Type: ``(...) -> Axes``.
* Format: ``path.to.module:func_name``.
"""

LINK_FN: str = _env.read_str("LINK_FN")
"""A custom link function; same interface as :func:`.create_explorer_link()`.

* Type: ``(...) -> str``.
* Format: ``path.to.module:func_name``.

May break the :class:`.QueryParams` class.
"""

DEBUG: bool = _env.read_bool("DEBUG", False)
"""Enable to show debug information in the UI."""


def get_values() -> dict[str, int | bool]:
    """Get config values as a dict."""
    return {
        "FIGURE_DPI": FIGURE_DPI,
        "PLOT_RAW_TIMESERIES": PLOT_RAW_TIMESERIES,
        "PLOT_AGGREGATIONS_PER_FOLD": PLOT_AGGREGATIONS_PER_FOLD,
        "MAX_SPLITS": MAX_SPLITS,
    }


def get_descriptions() -> dict[str, str]:
    """Get config key descriptions."""
    return {
        "FIGURE_DPI": "Controls figure fidelity. Higher values look better, but are slower to draw.",
        "PLOT_RAW_TIMESERIES": "Enable plot in the `🔍 Show raw data` tab.",
        "PLOT_AGGREGATIONS_PER_FOLD": "Enable plots in the `📈 Aggregations per fold` tab.",
        "MAX_SPLITS": "Upper fold count limit. Prevents figures from getting too large.",
    }


def get_server_config_info() -> str:
    """Get the readonly server configuration."""
    description = get_descriptions()

    return f"""
* `{MAX_SPLITS=}`: {description["MAX_SPLITS"]}
* `{PLOT_RAW_TIMESERIES=}`: {description["PLOT_RAW_TIMESERIES"]}
* `{PLOT_AGGREGATIONS_PER_FOLD=}`: {description["PLOT_AGGREGATIONS_PER_FOLD"]}
* `{FIGURE_DPI=}`: {description["FIGURE_DPI"]}
"""
