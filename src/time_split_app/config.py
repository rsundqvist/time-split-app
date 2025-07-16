"""Configuration namespace.

Values in this module are treated as hard limits by the server.
"""

from rics.env import read as env

# Configurable by application users
PLOT_RAW_TIMESERIES: bool = env.read_bool("PLOT_AGGREGATIONS_PER_FOLD", True)
"""Enable plot in the `🔍 Show raw data` tab."""
PLOT_AGGREGATIONS_PER_FOLD: bool = env.read_bool("PLOT_AGGREGATIONS_PER_FOLD", True)
"""Enable plots in the `📈 Aggregations per fold` tab."""
FIGURE_DPI: int = env.read_int("FIGURE_DPI", 200)
"""Controls figure fidelity. Higher values look better, but is a lot slower."""
MAX_SPLITS = env.read_int("MAX_SPLITS", 100)
"""Upper fold count limit. Prevents figures from getting too large."""

# Server configuration
RAW_DATA_SAMPLES: int = env.read_int("RAW_DATA_SAMPLES", 1000)
"""Maximum number of display and plot in `🔍 Show raw data` tab."""
DATASETS_CONFIG_PATH: str = env.read_str("DATASETS_CONFIG_PATH", "datasets.toml")
"""Determines where to look for the dataset configuration TOML. Disable the dataset view if not found."""
REQUIRE_DATASETS: bool = env.read_bool("REQUIRE_DATASETS", False)
"""If set, the server will refuse to start if not the ``DATASETS_CONFIG_PATH`` file does not exist."""
DATASET_CONFIG_CACHE_TTL: int = env.read_int("DATASET_CONFIG_CACHE_TTL", 30)
"""Frequency with which the ``DATASETS_CONFIGS_PATH`` is read."""
DATASET_CACHE_TTL: int = env.read_int("DATASET_CACHE_TTL", 12 * 60 * 60)
"""Cache timeout in seconds. Default is one hour."""
DATASET_RADIO_LIMIT: int = env.read_int("DATASET_RADIO_LIMIT", 3)
"""Maximum number of dataset options to show as radio buttons.

Radio buttons are shown with one-line descriptions and all options visible at once. If this limit is exceeded, the UI
shows a label-only dropdown menu instead."""
ENABLE_DATA_GENERATOR: bool = env.read_bool("ENABLE_DATA_GENERATOR", True)
"""Set to ``False`` to disable the built-in dataset generator."""

PROCESS_QUERY_PARAMS: bool = env.read_bool("PROCESS_QUERY_PARAMS", True)
"""Abort if parameters are given when ``False``. See :class:`~.widgets.types.QueryParams` for details."""
PERMALINK_BASE_URL: str = env.read_str("PERMALINK_BASE_URL")
"""Public base address for the application. Used to create permalinks."""
USE_CUSTOM_CSS: bool = env.read_bool("USE_CUSTOM_CSS", True)
"""Disable to use the default Streamlit styling."""
PERFORMANCE_LOG_LEVEL: int = env.read_int("DISABLE_PERFORMANCE_LOGGING", 20)
"""Set to modify log level for the `time_split_app.performance` logger. The default is logging.INFO=20."""

# Image extensions.
DATASET_LOADER: str = env.read_str("DATASET_LOADER")
"""A customer loader implementation.

Type: time_split.widgets.DataLoaderWidget
Format: `path.to.module:ClassName`.
"""

SPLIT_SELECT_FN: str = env.read_str("SPLIT_SELECT_FN")
"""Custom split parameters selection function.

Type: `() -> DatetimeIndexSplitterKwargs`.
Format: `path.to.module:func_name`.

To access query params produced by create_explorer_link(), use
>>> from time_split_app.widgets.types import QueryParams
>>> QueryParams.get()
"""

PLOT_FN: str = env.read_str("PLOT_FN")
"""A custom plotting function; same interface as ``time_split.plot()``.

Type: `(...) -> Axes`.
Format: `path.to.module:func_name`.

To access query params produces by create_explorer_link(), use
>>> from time_split_app.widgets.types import QueryParams
>>> query_params = QueryParams.get()
Of course, you may also choose to handle this yourself using ``st.query_params``.
"""

LINK_FN: str = env.read_str("LINK_FN")
"""A custom link factory function; same interface as ``time_split.app.create_explorer_link()``.

Type: `(...) -> str`.
Format: `path.to.module:func_name`.

This is experimental; will probably break the QueryParams class.
"""

DEBUG: bool = env.read_bool("DEBUG", False)
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
