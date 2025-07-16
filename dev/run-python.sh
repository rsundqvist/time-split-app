#!/bin/bash

set -eux

set -a
source "$(dirname "$0")/.env"
export DATASETS_CONFIG_PATH="dev/data/local-datasets.toml"
set +a

# python -c "import time_split; print(time_split.__path__[0])") # https://github.com/streamlit/streamlit/issues/9655
poetry run streamlit run app.py --server.headless true
