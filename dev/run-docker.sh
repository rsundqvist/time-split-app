#!/bin/bash

set -eux


docker build . -t time-split:dev


dir=$(dirname "$0")
docker run \
  --rm \
  --network=host \
  --env-file "$dir/.env" \
  --env EXTRA_PIP_PACKAGES="s3fs mplcyberpunk" \
  --env REQUIRE_DATASETS=true \
  --env DATASETS_CONFIG_PATH="s3://my-bucket/data/remote-datasets.toml" \
  --env DEBUG=0 \
  -v ./app_extensions.py:/home/streamlit/app_extensions.py:ro \
  time-split:dev
