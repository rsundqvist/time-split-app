#!/usr/bin/env bash
set -ex

# Streamlit will add the app script path - not the CWD - to the interpreter
# path. Add CWD to PYTHONPATH for convenience.
script_dir=$(dirname -- "${BASH_SOURCE[0]}")
export PYTHONPATH="$PYTHONPATH:$script_dir/extensions"
set -u

source extensions.env

app_path=$(python -m time_split app get-path)
streamlit run "$app_path" --server.address=localhost  --server.headless=true
