"""Tasks for maintaining the project.

Execute 'invoke --list' for guidance on using Invoke.
"""

import platform
from pathlib import Path

from invoke import call, task
from invoke.context import Context
from invoke.runners import Result

ROOT_DIR = Path(__file__).parent
SOURCE_DIR = ROOT_DIR.joinpath("src/time_fold_explorer")
TEST_DIR = ROOT_DIR.joinpath("tests")
PYTHON_TARGETS = [
    ROOT_DIR / "app.py",
    SOURCE_DIR,
    TEST_DIR,
    Path(__file__),
]
PYTHON_TARGETS_STR = " ".join([str(p) for p in PYTHON_TARGETS])


def _run(c: Context, command: str) -> Result:
    print(f"Command: {command}")
    return c.run(command, pty=platform.system() != "Windows")


@task
def clean_build(c: Context) -> None:
    """Clean up files from package building."""
    _run(c, "rm -fr build/")
    _run(c, "rm -fr dist/")
    _run(c, "rm -fr .eggs/")
    _run(c, "find . -name '*.egg-info' -exec rm -fr {} +")
    _run(c, "find . -name '*.egg' -exec rm -f {} +")


@task
def clean_python(c: Context) -> None:
    """Clean up python file artifacts."""
    _run(c, "find . -name '*.pyc' -exec rm -f {} +")
    _run(c, "find . -name '*.pyo' -exec rm -f {} +")
    _run(c, "find . -name '*~' -exec rm -f {} +")
    _run(c, "find . -name '__pycache__' -exec rm -fr {} +")


@task
def clean_tests(c: Context) -> None:
    """Clean up files from testing."""
    _run(c, "rm -fr .pytest_cache")


@task
def clean_ruff(c: Context) -> None:
    """Clean ruff cache (linter)."""
    _run(c, "ruff clean")


@task(pre=[clean_build, clean_python, clean_ruff, clean_tests])
def clean(_: Context) -> None:
    """Run all clean sub-tasks."""


@task(name="format")
def format_(c: Context, check: bool = False) -> None:
    """Format code."""
    format_options = ["--check", "--diff"] if check else []
    _run(c, f"poetry run ruff format {' '.join(format_options)} {PYTHON_TARGETS_STR}")
    if not check:
        _run(c, f"poetry run ruff check --fix-only {' '.join(format_options)} {PYTHON_TARGETS_STR}")


@task
def flake8(c: Context, check: bool = False) -> None:
    """Run flake8."""
    lint_options = ["--no-fix"] if check else []
    _run(c, f"poetry run ruff check {' '.join(lint_options)} {PYTHON_TARGETS_STR}")


@task
def spelling(c: Context) -> None:
    """Run spell check."""
    _run(c, f"poetry run codespell {PYTHON_TARGETS_STR}")


@task
def safety(c: Context) -> None:
    """Run safety."""
    ignores = [
        70612,  # CVE-2019-8341
    ]

    _run(
        c,
        f"poetry export --format=requirements.txt --without-hashes "
        f"| poetry run safety check --stdin --full-report -i {','.join(map(str, ignores))}",
    )


@task(pre=[safety, call(flake8, check=True), call(format_, check=True), spelling])
def lint(_: Context) -> None:
    """Run all linting."""


@task
def mypy(c: Context) -> None:
    """Run mypy."""
    _run(c, f"poetry run mypy {SOURCE_DIR} {TEST_DIR}")


@task
def tests(c: Context) -> None:
    """Run tests."""
    _run(c, f"poetry run pytest {TEST_DIR} {SOURCE_DIR}")


@task(
    help={
        "part": "Part of the version to be bumped.",
        "dry_run": "Don't write any files, just pretend. (default: False)",
    }
)
def version(c: Context, part: str, dry_run: bool = False) -> None:
    """Bump version."""
    bump_options = ["--dry-run"] if dry_run else []
    _run(c, f"poetry run bump2version {' '.join(bump_options)} {part}")

    if not dry_run and part != "dev":
        print("Add dev suffix..")

        no_dev = ["CHANGELOG.md"]

        part = "dev"
        _run(
            c,
            f"poetry run bump2version {' '.join(bump_options)} {part} --commit-args='--no-verify'",
        )
        print(f"Undo changes to release-only files: {' '.join(map(repr, no_dev))}")
        _run(
            c,
            f"git checkout HEAD^ -- {' '.join(no_dev)} && git commit --amend --no-edit --no-verify --quiet",
        )


@task
def pyupgrade(c: Context, check: bool = False) -> None:
    """Apply ``pyupgrade`` to all .py-files in ``PYTHON_TARGETS``."""
    flags = ["--py311-plus"]
    if not check:
        flags.append("--exit-zero-even-if-changed")

    def apply(*paths: Path) -> None:
        for path in paths:
            if path.is_file() and path.suffix == ".py":
                _run(c, f"pyupgrade {' '.join(flags)} {path}")
            elif path.is_dir():
                apply(*path.rglob("*/*.py"))

    apply(*PYTHON_TARGETS)
