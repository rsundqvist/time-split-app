"""CLI entrypoint."""

import logging
import stat
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


@main.command(name="new")
@click.option(
    "--out",
    default="my-time-split-app",
    type=str,
    help="Output directory.",
)
def new(out: str) -> None:
    """Create app from template."""
    files = ["Dockerfile", "entrypoint.sh", "my_extensions.py", "README.md"]

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


if __name__ == "__main__":
    main()
