"""Configuration namespace.

Values in this module are treated as hard limits by the server.
"""

from os import environ as _environ


def _read_bool(key: str, default: bool) -> bool:
    value = _environ.get(key, "").lower()
    return value != "false" if default is True else value == "true"


def _read_int(key: str, default: int) -> int:
    value = _environ.get(key)
    return default if value is None else int(value)


# Configurable by application users
PLOT_RAW_TIMESERIES: bool = _read_bool("PLOT_AGGREGATIONS_PER_FOLD", True)
"""Enable plot in the `🔍 Show raw data` tab."""
PLOT_AGGREGATIONS_PER_FOLD: bool = _read_bool("PLOT_AGGREGATIONS_PER_FOLD", True)
"""Enable plots in the `📈 Aggregations per fold` tab."""
FIGURE_DPI: int = _read_int("FIGURE_DPI", 200)
"""Controls figure fidelity. Higher values look better, but is a lot slower."""
MAX_SPLITS = _read_int("MAX_SPLITS", 100)
"""Upper fold count limit. Prevents figures from getting too large."""

# Server configuration
RAW_DATA_SAMPLES: int = _read_int("RAW_DATA_SAMPLES", 1000)
"""Maximum number of display and plot in `🔍 Show raw data` tab."""
DATASETS_CONFIG_PATH: str = _environ.get("DATASETS_CONFIG_PATH") or "datasets.toml"
"""Determines where to look for the dataset configuration TOML. Disable the dataset view if not found."""
REQUIRE_DATASETS: bool = _read_bool("REQUIRE_DATASETS", False)
"""If set, the server will refuse to start if not the ``DATASETS_CONFIG_PATH`` file does not exist."""
DATASET_CONFIG_CACHE_TTL: int = _read_int("DATASET_CONFIG_CACHE_TTL", 30)
"""Frequency with which the ``DATASETS_CONFIGS_PATH`` is read."""
DATASET_CACHE_TTL: int = _read_int("DATASET_CACHE_TTL", 12 * 60 * 60)
"""Cache timeout in seconds. Default is one hour."""
DATASET_RADIO_LIMIT: int = _read_int("DATASET_RADIO_LIMIT", 3)
"""Maximum number of dataset options to show as radio buttons.

Radio buttons are shown with one-line descriptions and all options visible at once. If this limit is exceeded, the UI
shows a label-only dropdown menu instead."""
PROCESS_QUERY_PARAMS: bool = _environ.get("PROCESS_QUERY_PARAMS", "").lower() != "false"
"""Abort if parameters are given when ``False``. See :class:`~.widgets.types.QueryParams` for details."""
PERMALINK_BASE_URL: str = _environ.get("PERMALINK_BASE_URL", "")
"""Public base address for the application. Used to create permalinks."""


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
