from click.testing import CliRunner

from time_split_app import cli


def test_new(tmp_path):
    """Test case used mocked requests responses."""

    out = tmp_path / "time-split-app-for-test"

    args = ["new", f"--out={out}"]
    CliRunner(catch_exceptions=False).invoke(cli.main, args)

    result = [str(path.relative_to(out)) for path in out.rglob("*") if path.is_file()]
    assert sorted(result) == [
        "Dockerfile",
        "README.md",
        "datasets/covid19.csv",
        "datasets/datasets.toml",
        "entrypoint.sh",
        "extensions.env",
        "extensions/__init__.py",
        "extensions/my_dataset_loader.py",
        "extensions/my_kwargs_type.py",
        "extensions/my_plot_fn.py",
        "extensions/my_select_fn.py",
        "start-dev.sh",
    ]
