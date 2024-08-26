#!/bin/bash

set -e

set -a
source "$(dirname "$0")/.env"
DATASETS_CONFIG_PATH="dev/data/local-datasets.toml"
set +a

echo $

# python dev/update-dataset.py local .gzip
poetry run streamlit run app.py --server.headless true
