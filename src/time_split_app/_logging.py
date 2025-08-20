import logging
from typing import Any

import pandas as pd
import streamlit as st
from rics.collections.dicts import flatten_dict
from rics.logs import basic_config
from streamlit.runtime.scriptrunner import get_script_run_ctx

from time_split_app import config
from time_split_app.widgets.types import QueryParams

LOGGER = logging.getLogger("time_split_app")


def log_perf(
    message: str,
    df: pd.DataFrame | dict[str, pd.DataFrame],
    seconds: float,
    *,
    extra: dict[str, Any],
    level: int = logging.DEBUG,
) -> str:
    if isinstance(df, dict):
        frames: dict[str, Any] = {key: _get_frame_extras(df) for key, df in df.items()}
        frames["__sum__"] = pd.DataFrame.from_dict(frames, orient="index").sum().to_dict()
        frames["n_frames"] = len(df)
        frame_extras = flatten_dict(frames)
    else:
        frame_extras = _get_frame_extras(df)

    remote_ip, session_id = get_session_data()

    extra = extra | {
        "session_id": session_id,
        "remote_ip": remote_ip,
        "duration_ms": int(1000 * seconds),
        **frame_extras,
        **config.get_values(),
        **QueryParams.get().to_dict(prefix="query."),
    }
    message = message.format_map(extra)
    LOGGER.log(level, message.replace("`", "") + f" | {extra=}", extra=extra)
    return message


def _get_frame_extras(df: pd.DataFrame) -> dict[str, int]:
    return {"size": df.size, "rows": len(df), "columns": len(df.columns)}


class StreamlitLoggingHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()

        if record.levelno >= logging.ERROR:
            st.error(message, icon="🚨")
        elif record.levelno >= logging.WARNING:
            st.warning(message, icon="⚠️")
        elif record.levelno >= logging.INFO:
            st.info(message, icon="ℹ️")
        else:
            st.code(record.levelname + ": " + record.getMessage())


def get_session_data() -> tuple[str, str]:
    ctx = get_script_run_ctx(suppress_warning=True)
    if ctx is None or ctx.session_id is None:
        return "", ""

    return _get_session_data(ctx.session_id), ctx.session_id


def _get_session_data(session_id: str) -> str:
    from streamlit.runtime import get_instance

    client = get_instance().get_client(session_id)
    if (request := getattr(client, "request", None)) is None:
        return ""

    return request.remote_ip  # type: ignore[no-any-return]


def configure_logging() -> None:
    basic_config(force=False)
    LOGGER.setLevel(config.PERFORMANCE_LOG_LEVEL)
