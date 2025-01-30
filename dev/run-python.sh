#!/bin/bash

set -eux

set -a
source "$(dirname "$0")/.env"
DATASETS_CONFIG_PATH="dev/data/local-datasets.toml"
set +a

poetry run streamlit run app.py --server.headless true
