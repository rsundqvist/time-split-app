#!/bin/bash

set -eux

set -a
source "$(dirname "$0")/common.env"
export DATASETS_CONFIG_PATH="dev/data/local-datasets.toml"
set +a

uv run python "$(dirname "$0")/update-datasets.py" --no-remote

# python -c "import time_split; print(time_split.__path__[0])") # https://github.com/streamlit/streamlit/issues/9655
uv run streamlit run app.py --server.headless true
