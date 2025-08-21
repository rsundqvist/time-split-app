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

The **Time Split** application
(available [here](https://time-split.streamlit.app/?data=1554942900-1557610200&schedule=0+0+%2A+%2A+MON%2CFRI&n_splits=2&step=2&show_removed=True))
is designed to help evaluate the effects of different
[parameters](https://time-split.readthedocs.io/en/stable/#parameter-overview).
To start it locally, run
```sh
docker run -p 8501:8501 rsundqvist/time-split
```
or 
```bash
pip install time-split[app]
python -m time_split app start
```
in the terminal. You may use
[create_explorer_link()](https://time-split.readthedocs.io/en/stable/api/time_split.app.html#time_split.app.create_explorer_link)
to build application URLs with preselected splitting parameters.

# Documentation
Click [here](https://time-split.readthedocs.io/en/stable/api/time_split.app.reexport.html) for documentation of the most
important types, functions and classes used by the application.

# Custom dataset loaders
Dataset loaders are a flexible way to load or create datasets that requires user input. The existing images (`>=0.7.0`)
can be extended to use custom loaders:

```Dockerfile
FROM python:3.13

RUN pip install --no-cache --compile time-split[app]
RUN pip install --no-cache --compile your-dependencies

ENV DATASET_LOADER=custom_dataset_loader:CustomDatasetLoader
COPY custom_dataset_loader.py .

# Entrypoint etc.
```

Loaders must implement the 
[DataLoaderWidget](https://time-split.readthedocs.io/en/stable/api/time_split.app.reexport.html#time_split.app.reexport.DataLoaderWidget)
interface. You may use
```bash
python -m time_split app new
```
to create a template project to get you started.

# Custom datasets
To bundle datasets, specify a configuration file (e.g. `DATASETS_CONFIG_PATH='s3://my-bucket/data/datasets.toml'`)
with the following keys:

| Key                    | Type             | Required | Description                                                                   |
|------------------------|------------------|----------|-------------------------------------------------------------------------------|
| `label`                | `string`         |          | Name shown in the UI. Defaults to section header (i.e. *"my-dataset"* below). |
| `path`                 | `string`         | Required | First argument to the `pandas` read function.                                 |
| `index`                | `string`         | Required | Datetime-like column. Will be converted using [pandas.to_datetime()].         |
| `aggregations`         | `dict[str, str]` |          | Determines function to use in the `📈 Aggregations per fold` tab.             |
| `description`          | `string`         |          | Markdown. The first line will be used as the summary in the UI.               |
| `read_function_kwargs` | `dict[str, Any]` |          | Keyword arguments for the `pandas` read function used.                        |

[pandas.to_datetime()]: https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.to_datetime.html

> ℹ️ The read function is chosen automatically based on the path.

> ℹ️ Additional dependencies are required for remote filesystems.
> You may use `EXTRA_PIP_PACKAGES=s3fs` to install dependencies for the S3 paths used below.

See the
[DatasetConfig](https://time-split.readthedocs.io/en/stable/api/time_split.app.reexport.html#time_split.app.reexport.DatasetConfig)
class for internal representation.

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
# Valid options depend on the read function used (pandas.read_csv, in this case).
```

Multiple datasets may be configured in their own top-level sections. Labels must be unique.

## Updating datasets
Datasets may be updated while the app is running. This is best done by changing the datasets config TOML file (e.g. by)
writing a timestamp, as above.

Default timings:
* The dataframes returned by the dataset loader are cached for `config.DATASET_CACHE_TTL` seconds (default = 12 hours).
* The dataset configuration file is read every `config.DATASET_CONFIG_CACHE_TTL` seconds (default = 30 seconds).

All datasets are reloaded immediately if the configuration changes, ignoring comments and formatting.

# Environment variables
See [config.py](src/time_split_app/config.py) for configurable values.

## User choice
Users may *lower* some configured values by using the Performance tweaker widget in the `❔ About tab` of application. To 
set a lower default, add a `DEFAULT_`-prefix to the regular name.
```bash
PLOT_AGGREGATIONS_PER_FOLD=true
DEFAULT_PLOT_AGGREGATIONS_PER_FOLD=false
```
This will disable the (expensive) per-column fold aggregation figures, but users who need them can turn them back on.
