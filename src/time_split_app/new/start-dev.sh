#!/usr/bin/env bash
set -eux

# Streamlit will add the app script path - not the CWD - to the to the
# interpreter path. Add CWD expose my_extensions.py as a module.
script_dir=$(dirname -- "${BASH_SOURCE[0]}")
export PYTHONPATH="$script_dir"

export DATASET_LOADER=my_extensions:MyDatasetLoader
export SPLIT_SELECT_FN=my_extensions:my_select_fn
export PLOT_FN=my_extensions:my_plot_fn
export LINK_FN=my_extensions:my_link_fn

app_path=$(python -m time_split app get-path)
streamlit run "$app_path"
