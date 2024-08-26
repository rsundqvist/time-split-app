import os
import sys
from dataclasses import asdict
from pathlib import Path

import pandas as pd

try:
    import tomli_w
    from tqdm.auto import tqdm
except ModuleNotFoundError:
    raise ImportError("Run `pip install tomli-w tqdm` to execute this script.")

from time_split.streamlit.widgets.data import SampleDataWidget
from time_split.streamlit.widgets.types import DatasetConfig

ROOT = Path(__file__).parent
assert len(sys.argv) in {2, 3}
assert sys.argv[1].lower().startswith(("r", "l"))
LOCAL = sys.argv[1].lower()[0] == "l"

if LOCAL:
    data_root = ROOT / "data/"
    data_root.mkdir(parents=True, exist_ok=True)
else:
    envs = {
        "AWS_ENDPOINT_URL_S3": "http://localhost:9000",
        "AWS_ACCESS_KEY_ID": "minioadmin",
        "AWS_SECRET_ACCESS_KEY": "minioadmin",
    }
    os.environ.update(envs)

    data_root = "s3://my-bucket/data"

root = f"{data_root}/data.{{}}"

WRITERS = {
    "csv": pd.DataFrame.to_csv,
    "json": pd.DataFrame.to_json,
    # "parq": pd.DataFrame.to_parquet,
    "parquet": pd.DataFrame.to_parquet,
    "feather": pd.DataFrame.to_feather,
    # "ftr": pd.DataFrame.to_feather,
    # "orc": pd.DataFrame.to_orc,
}

df = SampleDataWidget.load_sample_data(end="2019-05-11 20:30", n_rows=10000).reset_index()

DESCRIPTION = """Written by `{writer.__name__}()`.

This is a multiline description. The dataset has `shape={df.shape}` and is located at path=`'{file}'`.
"""

configs = []
for suf, writer in tqdm(WRITERS.items()):
    if len(sys.argv) == 3:
        compression = sys.argv[2]
        suf = suf + "." + compression.removeprefix(".")

    path = root.format(suf)

    try:
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

out = ROOT.joinpath(f"data/{'local' if LOCAL else 'remote'}-datasets.toml")
toml = tomli_w.dumps({c.label: {k: v for k, v in asdict(c).items() if v} for c in configs}, multiline_strings=True)
out.write_text(toml)

print(f"Wrote TOML:\n\n    {toml!r}\n")
summary = pd.Series({"file": out.absolute(), "data_root": data_root}).astype(str).map(repr).to_string()
print("-" * max(map(len, summary.splitlines())))
print(summary)
