#!/bin/bash

set -eux

docker build . -t time-split:dev

dir=$(dirname "$0")
cd "$dir"
docker compose up "${@:2}"
