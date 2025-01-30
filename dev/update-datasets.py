import os
import sys
from dataclasses import asdict
from pathlib import Path
from time import perf_counter

import click
import pandas as pd
import tomli_w
from rics.logs import disable_temporarily

with disable_temporarily("streamlit.runtime.caching.cache_data_api"):
    from time_fold_explorer.widgets.data import SampleDataWidget
    from time_fold_explorer.widgets.types import DatasetConfig

ROOT = Path(__file__).parent
WRITERS = {
    "csv": pd.DataFrame.to_csv,
    "json": pd.DataFrame.to_json,
    # "parq": pd.DataFrame.to_parquet,
    "parquet": pd.DataFrame.to_parquet,
    "feather": pd.DataFrame.to_feather,
    # "ftr": pd.DataFrame.to_feather,
    # "orc": pd.DataFrame.to_orc,
}


@click.command()
@click.option(
    "--remote/--no-remote",
    is_flag=True,
    show_default=True,
    default=True,
    help="Upload files to a local S3 server.",
)
@click.option(
    "--local/--no-local",
    is_flag=True,
    show_default=True,
    default=True,
    help="Store files locally.",
)
@click.option(
    "--compression",
    "-c",
    type=click.Choice(["none", "zip", "gzip"]),
    default="none",
    show_default=True,
    help="Compression type to use, if any.",
)
def main(remote: bool, local: bool, compression: str) -> None:
    df = SampleDataWidget.load_sample_data(end="2019-05-11 20:30", n_rows=10000).reset_index()

    compression = None if compression == "none" else compression
    if local:
        upload_local(df, compression)

    if remote:
        try:
            upload_remote(df, compression)
        except Exception as e:
            click.secho(f"Remote upload failed: {e}", fg="red")
            sys.exit(1)


def upload_local(df: pd.DataFrame, compression: str | None) -> None:
    data_root = ROOT / "data/"
    data_root.mkdir(parents=True, exist_ok=True)
    upload(df, str(data_root), "local", compression)


def upload_remote(df: pd.DataFrame, compression: str | None) -> None:
    envs = {
        "AWS_ENDPOINT_URL_S3": "http://localhost:9000",
        "AWS_ACCESS_KEY_ID": "minioadmin",
        "AWS_SECRET_ACCESS_KEY": "minioadmin",
        "AWS_MAX_ATTEMPTS": "2",
    }
    os.environ.update(envs)
    data_root = "s3://my-bucket/data"
    upload(df, data_root, "remote", compression)


def upload(df: pd.DataFrame, data_root: str, name: str, compression: str | None) -> None:
    start = perf_counter()

    configs = []
    for suf, writer in WRITERS.items():
        suffix = f"{suf}.{compression}" if compression else suf

        path = f"{data_root}/data.{suffix}"

        try:
            try:
                writer(df, path, index=False)
            except TypeError:
                writer(df, path)
        except Exception as e:
            e.add_note(f"{path=}")
            raise

        cfg = DatasetConfig(
            label=f"`{path.rpartition('/')[-1]}`",
            index="timestamp",
            path=path,
            description=DESCRIPTION.format(writer=writer, df=df, file=path),
        )
        configs.append(cfg)

    out = ROOT.joinpath(f"data/{name}-datasets.toml")
    toml = tomli_w.dumps({c.label: {k: v for k, v in asdict(c).items() if v} for c in configs}, multiline_strings=True)
    out.write_text(toml)

    click.secho(
        f"Uploaded {len(configs)} {name} datasets in {perf_counter() - start:.2f} seconds. Datasets file: '{out.relative_to(Path.cwd())}'",
        fg="green",
    )


DESCRIPTION = """Written by `{writer.__name__}()`.

This is a multiline description. The dataset has `shape={df.shape}` and is located at path=`'{file}'`.
"""

if __name__ == "__main__":
    main()
