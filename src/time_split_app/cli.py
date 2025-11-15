"""CLI entrypoint."""

import logging
import os
import re
import stat
import subprocess
import typing as _t
from pathlib import Path

import click
import pandas as pd
from rics.click import _alias_command_group

from time_split_app import config

LOGGER = logging.getLogger(__name__)


@click.group("app", cls=_alias_command_group.AliasedCommandGroup)
def main() -> None:
    """Start the explorer app or create your own."""


@main.command(name="get-path")
def get_path() -> None:
    """Echo path to the application script.

    Mean for use in Docker images, e.g.

    ```bash
    streamlit run $(python -m time_split app get-path)
    ```
    """
    print(_get_app_path(), end="")


@main.command(name="start")
@click.option("--port", default=8501, help="Bind port.", show_default=True)
def start(port: int) -> None:
    """Start the application."""
    address = "localhost"
    cmd = ["streamlit", "run", f"--server.port={port}", f"--server.address={address}", str(_get_app_path())]

    click.secho(" ".join(cmd), fg="green")
    subprocess.run(  # noqa: S603
        cmd,
        check=False,
        env={**os.environ, "PERMALINK_BASE_URL": f"http://{address}:{port}/"},
    )


@main.command(name="new")
@click.option(
    "--out",
    default="my-time-split-app",
    type=str,
    help="Output directory.",
)
def new(out: str) -> None:
    """Create app from template."""
    files = ["Dockerfile", "entrypoint.sh", "my_extensions.py", "README.md", "start-dev.sh"]

    root = Path(out)
    root.mkdir(exist_ok=False, parents=True)

    for f in files:
        src = Path(__file__).parent.joinpath("new", f)
        dst = root.joinpath(f)

        dst.write_bytes(src.read_bytes())
        dst.chmod(src.stat().st_mode | stat.S_IWUSR)

    click.secho(f"Project directory '{out}' created. See the README to get started.", fg="green")


def _get_app_path() -> Path:
    return Path(__file__).parent / "app.py"


@main.command()
@click.option(
    "--no-sort",
    is_flag=True,
    help="Disable sorting of config options by name.",
)
@click.option(
    "--no-values",
    is_flag=True,
    help="Do not show current config values.",
)
def print_config(no_sort: bool, no_values: bool) -> None:
    """Print config options."""
    with Path(config.__file__).open() as f:
        lines = f.read().splitlines()

    def get_value(name: str) -> _t.Any:
        value = getattr(config, name)
        if value == "":
            return "<not set>"

        if isinstance(value, str):
            return repr(value)

        return value

    records: list[tuple[str, str, str]] = []
    current: tuple[str, str] | None = None

    pattern: re.Pattern[str] = re.compile("([A-Z_]+): ([a-z]+)")
    for line in lines:
        if current is None:
            match = pattern.match(line)
            if match is None:
                continue

            current = match.group(1), match.group(2)
        else:
            record = *current, line.removeprefix('"""').removesuffix('"""')
            records.append(record)
            current = None

    df = pd.DataFrame(records, columns=["Name", "Type", "Description"])
    df = df.set_index("Name")

    if not no_values:
        df["Value"] = df.index.map(get_value)
        df = df[["Type", "Value", "Description"]]

    if not no_sort:
        df = df.sort_index()

    click.secho(df.to_string())


if __name__ == "__main__":
    main()
