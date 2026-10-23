"""The analysis behind the dashboard, written in SQL.

The tidy CSV is loaded into an in-memory SQLite database, and every number the
dashboard shows comes from one of the queries below.
"""

import math
import sqlite3
from pathlib import Path

import pandas as pd

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "health_indicators.csv"


def connect(csv_path: Path = DATA_FILE) -> sqlite3.Connection:
    """Loads the dataset into a fresh in-memory SQLite database."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    pd.read_csv(csv_path).to_sql("health", conn, index=False)
    conn.execute("CREATE INDEX idx_health ON health (indicator, country, year)")
    return conn


def query(conn: sqlite3.Connection, sql: str, params: dict | None = None) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn, params=params or {})


# ---------- the queries ----------

SERIES_SQL = """
-- One indicator over time, for the chosen countries and years
SELECT country, year, value
FROM health
WHERE indicator = :indicator
  AND year BETWEEN :start AND :end
ORDER BY country, year
"""

LATEST_SQL = """
-- Each country's most recent value for one indicator
SELECT country, year, value
FROM (
    SELECT country, year, value,
           ROW_NUMBER() OVER (PARTITION BY country ORDER BY year DESC) AS rn
    FROM health
    WHERE indicator = :indicator
)
WHERE rn = 1
ORDER BY value
"""

CHANGE_SQL = """
-- First and latest value for one country and indicator
WITH bounds AS (
    SELECT MIN(year) AS first_year, MAX(year) AS last_year
    FROM health
    WHERE indicator = :indicator AND country = :country
)
SELECT b.first_year,
       f.value AS first_value,
       b.last_year,
       l.value AS last_value
FROM bounds b
JOIN health f ON f.indicator = :indicator AND f.country = :country AND f.year = b.first_year
JOIN health l ON l.indicator = :indicator AND l.country = :country AND l.year = b.last_year
"""

MALARIA_SHARE_SQL = """
-- Nigeria's share of all malaria deaths in Sub-Saharan Africa, by year
SELECT n.year,
       n.value AS nigeria_deaths,
       s.value AS region_deaths,
       ROUND(100.0 * n.value / s.value, 1) AS share_pct
FROM health n
JOIN health s
  ON s.year = n.year
 AND s.indicator = n.indicator
 AND s.country = 'Sub-Saharan Africa'
WHERE n.indicator = 'malaria_deaths'
  AND n.country = 'Nigeria'
ORDER BY n.year
"""


# ---------- helpers built on the queries ----------

def series(conn, indicator: str, start: int, end: int) -> pd.DataFrame:
    return query(conn, SERIES_SQL, {"indicator": indicator, "start": start, "end": end})


def latest(conn, indicator: str) -> pd.DataFrame:
    return query(conn, LATEST_SQL, {"indicator": indicator})


def change(conn, indicator: str, country: str = "Nigeria") -> dict | None:
    df = query(conn, CHANGE_SQL, {"indicator": indicator, "country": country})
    if df.empty:
        return None
    row = df.iloc[0].to_dict()
    row["change"] = row["last_value"] - row["first_value"]
    row["pct_change"] = 100 * row["change"] / row["first_value"] if row["first_value"] else None
    return row


def malaria_share(conn) -> pd.DataFrame:
    return query(conn, MALARIA_SHARE_SQL)


def annual_rate_of_reduction(first: float, last: float, years: int) -> float:
    """Average yearly % decline, as used by the UN for mortality rates."""
    if years <= 0 or first <= 0 or last <= 0:
        return 0.0
    return 100 * (1 - (last / first) ** (1 / years))


def years_to_target(current: float, target: float, arr_pct: float) -> float | None:
    """Years until `current` falls to `target` if it keeps falling at `arr_pct` % per year."""
    if current <= target:
        return 0.0
    if arr_pct <= 0:
        return None  # not falling, so never at this rate
    return math.log(target / current) / math.log(1 - arr_pct / 100)


# ---------- key findings, worked out from the data ----------

def _rank(conn, indicator: str, country: str, better: str) -> tuple[int, int]:
    """Nigeria's position among countries (regions excluded), 1 = best."""
    df = latest(conn, indicator)
    df = df[~df["country"].isin(["World", "Sub-Saharan Africa"])]
    df = df.sort_values("value", ascending=(better == "lower")).reset_index(drop=True)
    position = int(df.index[df["country"] == country][0]) + 1
    return position, len(df)


def key_findings(conn, country: str = "Nigeria") -> list[str]:
    findings = []

    mmr = change(conn, "maternal_mortality", country)
    if mmr:
        years = int(mmr["last_year"] - mmr["first_year"])
        arr = annual_rate_of_reduction(mmr["first_value"], mmr["last_value"], years)
        to_go = years_to_target(mmr["last_value"], 70, arr)
        rank, total = _rank(conn, "maternal_mortality", country, "lower")
        text = (
            f"**Maternal deaths:** {mmr['last_value']:,.0f} women die per 100,000 live births "
            f"({int(mmr['last_year'])}), the {_ordinal(total - rank + 1)}highest of the "
            f"{total} countries compared. It fell {abs(mmr['pct_change']):.0f}% since "
            f"{int(mmr['first_year'])}, about {arr:.1f}% a year"
        )
        if to_go:
            text += f". At that pace, reaching the SDG target of 70 would take about {to_go:,.0f} years."
        findings.append(text)

    u5 = change(conn, "under5_mortality", country)
    if u5:
        per_children = 1000 / u5["last_value"]
        findings.append(
            f"**Child deaths:** under-five mortality more than halved since {int(u5['first_year'])}, "
            f"from {u5['first_value']:.0f} to {u5['last_value']:.0f} per 1,000 births, "
            f"but about 1 in {per_children:.0f} children still die before turning five."
        )

    share = malaria_share(conn)
    if not share.empty:
        last = share.iloc[-1]
        findings.append(
            f"**Malaria:** Nigeria accounted for {last['share_pct']:.0f}% of all malaria deaths in "
            f"Sub-Saharan Africa in {int(last['year'])} ({last['nigeria_deaths']:,.0f} deaths), "
            f"up from {share.iloc[0]['share_pct']:.0f}% in {int(share.iloc[0]['year'])}."
        )

    dtp = change(conn, "dtp3_coverage", country)
    if dtp:
        rank, total = _rank(conn, "dtp3_coverage", country, "higher")
        position = "the lowest" if rank == total else f"number {rank} out of {total}"
        findings.append(
            f"**Vaccines:** {dtp['last_value']:.0f}% of 1-year-olds got the DTP3 vaccine in "
            f"{int(dtp['last_year'])}, {'the same as' if dtp['change'] == 0 else 'compared with'} "
            f"{dtp['first_value']:.0f}% in {int(dtp['first_year'])}, {position} among the countries "
            f"compared. The WHO goal is 90%."
        )

    tb = change(conn, "tb_treatment_coverage", country)
    if tb:
        missed = 100 - tb["last_value"]
        findings.append(
            f"**Tuberculosis:** only {tb['last_value']:.0f}% of estimated TB cases were found and "
            f"treated in {int(tb['last_year'])}, so roughly {missed:.0f}% were missed."
        )

    return findings


def _ordinal(n: int) -> str:
    if n == 1:
        return ""
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix} "
