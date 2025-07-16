#!/bin/bash

set -eux


docker build . -t time-split:dev


dir=$(dirname "$0")
docker run \
  --rm \
  -p 8501:8501 \
  --network=host \
  --env-file "$dir/.env" \
  --env EXTRA_PIP_PACKAGES="s3fs mplcyberpunk" \
  -v "$dir/data/remote-datasets.toml:/home/streamlit/datasets.toml:ro" \
  -v ./app_extensions.py:/home/streamlit/app_extensions.py:ro \
  time-split:dev
