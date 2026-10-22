#!/bin/bash

set -eux

if command -v docker >/dev/null; then
  docker=docker
else
  docker=podman
fi

$docker build . -t time-split:dev

dir=$(dirname "$0")
cd "$dir"

uv run python update-datasets.py --no-local &
$docker compose up "$@"
