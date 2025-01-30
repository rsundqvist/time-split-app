# Time Split  <!-- omit in toc -->
Time-based k-fold validation splits for heterogeneous data.

-----------------
[![PyPI - Version](https://img.shields.io/pypi/v/time-split.svg)](https://pypi.python.org/pypi/time-split)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/time-split.svg)](https://pypi.python.org/pypi/time-split)
[![Tests](https://github.com/rsundqvist/time-split/workflows/tests/badge.svg)](https://github.com/rsundqvist/time-split/actions?workflow=tests)
[![Codecov](https://codecov.io/gh/rsundqvist/time-split/branch/master/graph/badge.svg)](https://codecov.io/gh/rsundqvist/time-split)
[![Read the Docs](https://readthedocs.org/projects/time-split/badge/)](https://time-split.readthedocs.io/)
[![PyPI - License](https://img.shields.io/pypi/l/time-split.svg)](https://pypi.python.org/pypi/time-split)
[![Docker Image Size (tag)](https://img.shields.io/docker/image-size/rsundqvist/time-split/latest?logo=docker&label=time-split)](https://hub.docker.com/r/rsundqvist/time-split/)

<div align="center">
  <img alt="Plotted folds on a two-by-two grid." 
       title="Examples" height="300" width="1200" 
  src="https://raw.githubusercontent.com/rsundqvist/time-split/master/docs/2x2-examples.jpg"><br>
</div>

Folds plotted on a two-by-two grid. See the
[examples](https://time-split.readthedocs.io/en/stable/auto_examples/index.html) page for more.

# About this image
The **Time Fold Explorer** application
(available [here](https://time-split.streamlit.app/?data=1554942900-1557610200&schedule=0+0+%2A+%2A+MON%2CFRI&n_splits=2&step=2&show_removed=True))
is designed to help evaluate the effects of different
[parameters](https://time-split.readthedocs.io/en/stable/#parameter-overview).
To start it locally using
[![Docker Image Size (tag)](https://img.shields.io/docker/image-size/rsundqvist/time-split/latest?logo=docker&label=time-split)](https://hub.docker.com/r/rsundqvist/time-split/)
Docker, run
```sh
docker run -p 8501:8501 rsundqvist/time-split
```
in the terminal. You may use
[`create_explorer_link()`](https://time-split.readthedocs.io/en/stable/generated/time_split.support.html#time_split.support.create_explorer_link)
to build application URLs with preselected splitting parameters.

# Custom datasets
To bundle datasets, mount a configuration file (determined by 
[`DATASETS_CONFIG_PATH='/home/streamlit/datasets.toml'`](https://time-split.readthedocs.io/en/stable/generated/time_split.streamlit.config.html#time_split.streamlit.config.DATASETS_CONFIG_PATH)
). The `DatasetConfig` struct has the following keys:

* `label`: Optional. Name shown in the UI. Defaults to section header (i.e. *"my-dataset"* below).
* `path`: Required. First argument to the `pandas` read function.
* `index`: Required. Must be datetime-like.
* `aggregations`: Optional. Determines function to use in the `📈 Aggregations per fold` tab.
* `description`: Optional. The first line will be used as the summary in the UI.
* `read_function_kwargs`: Keyword arguments for the `pandas` read function used (as determined by the `path`).

Additional dependencies are required for remote filesystems. You may use `EXTRA_PIP_PACKAGES=s3fs` to install
dependencies for the S3 paths used below.

```toml
[my-dataset]
label = "Dataset name"
path = "s3://my-bucket/data/title_basics.csv"
index = "from"
aggregations = { runtimeMinutes = "min", isAdult = "mean" }
description = """This is the summary.

Simplified version of the
[Title basics](https://developer.imdb.com/non-commercial-datasets/#titlebasicstsvgz) IMDB
dataset. The description supports Markdown syntax.

Last updated: `2019-05-11T20:30:00+00:00'
"""
[my-dataset.read_function_kwargs]
# Valid options depend on the read function used.
```

Multiple datasets may be configured in their own top-level sections. Labels must be unique.

## Mounted datasets
A convenient way to keep datasets up-to-date without relying on network storage is to mount a dataset folder on a local
machine, using e.g. a CRON job to update the data. To start the image with datasets mounted, run:

```bash
docker run \
  -p 8501:8501 \
  -v ./data:/home/streamlit/data:ro \
  -v ./datasets.toml:/home/streamlit/datasets.toml:ro \
  -e REQUIRE_DATASETS=true \
  rsundqvist/time-split 
```

in the terminal. Paths in `datasets.toml` should be absolute, or relative to `/home/streamlit/`. 

## Dataset caching
* The dataframes returned by the dataset loader are cached for `config.DATASET_CACHE_TTL` seconds (default = 12 hours).
* Dataset configuration (`/home/streamlit/datasets.toml` above) is verified every `config.DATASET_CONFIG_CACHE_TTL`
  seconds (default = 30 seconds).

Datasets are fully reloaded if the dataset configuration file changes in any way. Including the current time when
generating a new `datasets.toml` is enough, e.e. running
```bash
printf "\n# Updated: %s\n" "$(date)" >> datasets.toml
```
as a postprocessing step. To write TOML files, you may want to use the https://pypi.org/project/tomli-w/ package.

# Environment variables
See [config.py](src/time_fold_explorer/config.py) for configurable values. Use `true|false` for boolean variables. 
Documentation for the underlying framework (Streamlit) is available 
[here](https://docs.streamlit.io/develop/concepts/configuration/options/).

## User choice
Users may *lower* some configured values by using the Performance tweaker widget in the `❔ About tab` of application. To 
set a lower default, add a `DEFAULT_`-prefix to the regular name.
```bash
PLOT_AGGREGATIONS_PER_FOLD=true
DEFAULT_PLOT_AGGREGATIONS_PER_FOLD=false
```
This will disable the (expensive) per-column fold aggregation figures, but users who need them can turn them back on.
