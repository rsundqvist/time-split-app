"""CLI entrypoint."""

import logging
import subprocess
from pathlib import Path

import click

LOGGER = logging.getLogger(__name__)


@click.group("app")
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
def start() -> None:
    """Start the application."""
    cmd = ["streamlit", "run", str(_get_app_path())]

    click.secho(" ".join(cmd), fg="green")
    subprocess.run(cmd, check=False)  # noqa: S603


def _get_app_path() -> Path:
    return Path(__file__).parent / "app.py"


if __name__ == "__main__":
    main()
