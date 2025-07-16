"""Nox sessions."""

import platform
import tempfile
from typing import Any

import nox
from nox.sessions import Session

nox.options.sessions = ["tests", "mypy"]
python_versions = ["3.11", "3.12", "3.13"]


def install_with_constraints(session: Session, *args: str, **kwargs: Any) -> None:
    """Install packages constrained by Poetry's lock file.

    This function is a wrapper for nox.sessions.Session.install. It
    invokes pip to install packages inside of the session's virtualenv.
    Additionally, pip is passed a constraints file generated from
    Poetry's lock file, to ensure that the packages are pinned to the
    versions specified in poetry.lock. This allows you to manage the
    packages as Poetry development dependencies.

    Args:
        session: The Session object.
        args: Command-line arguments for pip.
        kwargs: Additional keyword arguments for Session.install.

    """
    with tempfile.NamedTemporaryFile(delete=False) as requirements:
        session.run(
            "poetry",
            "export",
            "--without-hashes",
            f"--output={requirements.name}",
            external=True,
        )
        session.install("-r", requirements.name, *args, **kwargs)


def install_with_project_extras(session: Session) -> None:
    """Install the project using poetry."""
    session.run_always("poetry", "install", "--no-interaction", "--all-extras", external=True)
    session.install(".")


@nox.session(python=python_versions)
def tests(session: Session) -> None:
    """Run the test suite."""
    install_with_project_extras(session)
    install_with_constraints(session, "invoke", "pytest", "xdoctest", "coverage", "pytest-cov")
    try:
        session.run(
            "inv",
            "tests",
            env={
                "COVERAGE_FILE": f".coverage.{platform.system()}.{platform.python_version()}",
            },
        )
    finally:
        if session.interactive:
            session.notify("coverage")


@nox.session
def coverage(session: Session) -> None:
    """Produce the coverage report."""
    args = session.posargs if session.posargs and len(session._runner.manifest) == 1 else []
    install_with_constraints(session, "invoke", "coverage")
    session.run("inv", "coverage", *args)


@nox.session(python=python_versions)
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    install_with_project_extras(session)
    install_with_constraints(session, "invoke", "mypy")
    session.run("inv", "mypy")


@nox.session(python="3.12")
def safety(session: Session) -> None:
    """Scan dependencies for insecure packages."""
    install_with_constraints(session, "invoke", "safety")
    session.run("inv", "safety")
