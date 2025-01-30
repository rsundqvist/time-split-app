#!/bin/bash

set -eux

docker build . -t time-split:dev

# python dev/update-datasets.py remote .gzip
dir=$(dirname "$0")
docker run --network=host \
  --env-file "$dir/.env" \
  --env EXTRA_PIP_PACKAGES=s3fs \
  --env DATASETS_CONFIG_PATH="/home/streamlit/datasets.toml" \
  -v "$dir/data/remote-datasets.toml:/home/streamlit/datasets.toml" \
  time-split:dev
