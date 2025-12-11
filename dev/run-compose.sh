#!/bin/bash

set -eux

docker build . -t time-split:dev

dir=$(dirname "$0")
cd "$dir"

poetry run python update-datasets.py --no-local &
docker compose up "${@:2}"
