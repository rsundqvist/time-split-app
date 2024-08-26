from pprint import pformat
from typing import Never

import pandas as pd
import streamlit as st
from time_split.types import DatetimeIndexSplitterKwargs

from time_fold_explorer import config
from time_fold_explorer.widgets.display._code import CodeWidget


def enforce_max_splits(
    all_splits: int, kwargs: DatetimeIndexSplitterKwargs, limits: tuple[pd.Timestamp, pd.Timestamp]
) -> None:
    """Check the number of splits against the configured limit, rising if exceeded."""
    if all_splits > config.MAX_SPLITS:
        _too_many_splits(all_splits, kwargs, limits)


@st.dialog("🚨 Too many splits")
def _too_many_splits(
    all_splits: int,
    kwargs: DatetimeIndexSplitterKwargs,
    limits: tuple[pd.Timestamp, pd.Timestamp],
) -> Never:
    st.error(f"Maximum number of splits ({config.MAX_SPLITS}) exceeded.", icon="🚨")
    st.write("Number of splits is restricted for performance reasons.")
    strings = CodeWidget("string").convert({**kwargs, "available": limits})
    st.code("kwargs = " + pformat(strings, indent=0, width=40, depth=2))
    st.write(
        f"The arguments above produces `len(splits)={all_splits} > {config.MAX_SPLITS}=MAX_SPLITS`."
        " Try using different parameters to reduce the number of folds."
    )
    st.stop()


def get_about() -> str:
    from time_split import __version__

    return f"""## Time Fold Explorer
This applications is designed to help experiment with `time-split` splitting parameters.

See https://time-split.readthedocs.io/ for library documentation.

#### 🚀 Getting started
1. Use the `⚙️ Configure data` menu to select a datetime range or a dataset.
2. Use the sidebar widgets to control how the data is split.
3. Use the `📊 Folds` and `📈 Aggregations per fold` tabs to explore the effects.

Please visit the [GitHub page](https://github.com/rsundqvist/time-split) for questions or feedback.

#### ⚙️ Server configuration
These values cannot be changed.

{config.get_server_config_info()}

See https://hub.docker.com/repository/docker/rsundqvist/time-split/ to spawn custom servers.

### Server `time-split` version
The server is using version `{__version__}`. To install this version, run

```bash
pip install time-split=={__version__}
```

in your favorite terminal. You may then copy one of the snippets from the `📊 Folds` tab to get started.
"""  # noqa: S608  # This is not SQL.
