"""Downloads the source datasets and builds one tidy table: data/health_indicators.csv

Each row is one measurement: country, year, indicator, value.

Run from the project root:
    python pipeline/build_dataset.py
"""

import sys
from pathlib import Path
from urllib.parse import quote

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dashboard.indicators import COUNTRIES, INDICATORS, OWID_BASE, START_YEAR  # noqa: E402

OUTPUT = ROOT / "data" / "health_indicators.csv"


def dataset_url(name: str) -> str:
    """OWID stores each dataset as datasets/<name>/<name>.csv"""
    encoded = quote(name)
    return f"{OWID_BASE}/{encoded}/{encoded}.csv"


def load_indicator(key: str, spec: dict, cache: dict) -> pd.DataFrame:
    """Returns one indicator as tidy rows, keeping only our countries and years."""
    name = spec["dataset"]
    if name not in cache:
        print(f"Downloading: {name}")
        cache[name] = pd.read_csv(dataset_url(name))
    raw = cache[name]

    if spec["column"] not in raw.columns:
        raise KeyError(f"Column {spec['column']!r} not found in {name!r}")

    df = raw[["Entity", "Year", spec["column"]]].rename(
        columns={"Entity": "country", "Year": "year", spec["column"]: "value"}
    )
    df = df[df["country"].isin(COUNTRIES) & (df["year"] >= START_YEAR)]
    df = df.dropna(subset=["value"])
    df["indicator"] = key
    return df


def build() -> pd.DataFrame:
    cache: dict = {}
    frames = [load_indicator(key, spec, cache) for key, spec in INDICATORS.items()]
    tidy = pd.concat(frames, ignore_index=True)

    tidy["year"] = tidy["year"].astype(int)
    tidy["value"] = tidy["value"].astype(float).round(2)
    tidy = tidy[["country", "year", "indicator", "value"]]
    tidy = tidy.drop_duplicates(subset=["country", "year", "indicator"])
    return tidy.sort_values(["indicator", "country", "year"]).reset_index(drop=True)


def main() -> None:
    tidy = build()
    OUTPUT.parent.mkdir(exist_ok=True)
    tidy.to_csv(OUTPUT, index=False)
    print(f"\nSaved {len(tidy):,} rows to {OUTPUT.relative_to(ROOT)}")
    summary = tidy.groupby("indicator")["year"].agg(["min", "max", "count"])
    print(summary.to_string())


if __name__ == "__main__":
    main()
