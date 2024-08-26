#!/usr/bin/env bash

set -e

if [ ! -z "$EXTRA_PIP_PACKAGES" ]; then
  echo "+pip install $EXTRA_PIP_PACKAGES"
  pip install $EXTRA_PIP_PACKAGES
fi

exec streamlit run app.py \
  --server.address=0.0.0.0 --server.port=8501 \
  --server.headless=true \
  --server.fileWatcherType=none
