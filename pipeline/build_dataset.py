"""Downloads the latest data from the World Bank and WHO APIs and builds one tidy table:
data/health_indicators.csv

Each row is one measurement: country, year, indicator, value.

Run from the project root:
    python pipeline/build_dataset.py
"""

import json
import sys
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dashboard.indicators import (  # noqa: E402
    INDICATORS,
    PLACES,
    START_YEAR,
    WHO_API,
    WORLD_BANK_API,
)

OUTPUT = ROOT / "data" / "health_indicators.csv"
WORLD_BANK_CODES = [code for code in PLACES if code not in ("AFR", "GLOBAL")]
WHO_CODES = [code for code in PLACES if code not in ("SSF", "WLD")]


def get_json(url: str, retries: int = 3):
    """Downloads JSON, retrying a couple of times if the API is slow or busy."""
    for attempt in range(retries):
        try:
            request = Request(url, headers={"User-Agent": "nigeria-health-dashboard"})
            with urlopen(request, timeout=60) as response:
                return json.load(response)
        except OSError:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))


# ---------- World Bank ----------

def world_bank_url(code: str, page: int = 1) -> str:
    countries = ";".join(WORLD_BANK_CODES)
    return (
        f"{WORLD_BANK_API}/country/{countries}/indicator/{code}"
        f"?format=json&per_page=1000&page={page}&date={START_YEAR}:2030"
    )


def parse_world_bank(pages: list) -> pd.DataFrame:
    """Turns World Bank API responses ([meta, rows] per page) into country/year/value rows."""
    records = []
    for page in pages:
        for row in page[1] or []:
            if row["value"] is None or row["countryiso3code"] not in PLACES:
                continue
            records.append(
                {
                    "country": PLACES[row["countryiso3code"]],
                    "year": int(row["date"]),
                    "value": float(row["value"]),
                }
            )
    return pd.DataFrame(records, columns=["country", "year", "value"])


def fetch_world_bank(code: str) -> pd.DataFrame:
    first = get_json(world_bank_url(code))
    pages = [first]
    for page in range(2, first[0]["pages"] + 1):
        pages.append(get_json(world_bank_url(code, page)))
    return parse_world_bank(pages)


# ---------- WHO Global Health Observatory ----------

def who_url(code: str) -> str:
    places = ",".join(f"'{c}'" for c in WHO_CODES)
    query = f"SpatialDim in ({places}) and TimeDim ge {START_YEAR}"
    return f"{WHO_API}/{code}?$filter={quote(query)}"


def parse_who(response: dict) -> pd.DataFrame:
    """Turns a WHO GHO API response into country/year/value rows (totals only, no breakdowns)."""
    records = []
    for row in response.get("value", []):
        if row.get("NumericValue") is None or row["SpatialDim"] not in PLACES:
            continue
        if row.get("Dim1") is not None:  # skip breakdowns by sex, age, etc.
            continue
        records.append(
            {
                "country": PLACES[row["SpatialDim"]],
                "year": int(row["TimeDim"]),
                "value": float(row["NumericValue"]),
            }
        )
    return pd.DataFrame(records, columns=["country", "year", "value"])


def fetch_who(code: str) -> pd.DataFrame:
    return parse_who(get_json(who_url(code)))


# ---------- build the table ----------

FETCHERS = {"worldbank": fetch_world_bank, "who": fetch_who}


def tidy(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Combines one DataFrame per indicator into the final tidy table."""
    parts = [df.assign(indicator=key) for key, df in frames.items() if not df.empty]
    table = pd.concat(parts, ignore_index=True)
    table = table[table["year"] >= START_YEAR]
    table["value"] = table["value"].round(2)
    table = table[["country", "year", "indicator", "value"]]
    table = table.drop_duplicates(subset=["country", "year", "indicator"])
    return table.sort_values(["indicator", "country", "year"]).reset_index(drop=True)


def build() -> pd.DataFrame:
    frames = {}
    for key, spec in INDICATORS.items():
        print(f"Downloading {key} ({spec['api']}: {spec['code']})")
        frames[key] = FETCHERS[spec["api"]](spec["code"])
        if frames[key].empty:
            raise RuntimeError(f"No data returned for {key}")
    return tidy(frames)


def main() -> None:
    table = build()
    OUTPUT.parent.mkdir(exist_ok=True)
    table.to_csv(OUTPUT, index=False)
    print(f"\nSaved {len(table):,} rows to {OUTPUT.relative_to(ROOT)}")
    print(table.groupby("indicator")["year"].agg(["min", "max", "count"]).to_string())


if __name__ == "__main__":
    main()
