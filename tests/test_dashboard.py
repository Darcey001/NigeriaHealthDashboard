import math

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard import analysis
from dashboard.charts import spread_labels
from dashboard.indicators import COUNTRIES, INDICATORS
from pipeline import build_dataset


@pytest.fixture(scope="module")
def conn():
    return analysis.connect()


@pytest.fixture(scope="module")
def data():
    return pd.read_csv(analysis.DATA_FILE)


# ---------- the dataset ----------

def test_dataset_has_the_expected_shape(data):
    assert list(data.columns) == ["country", "year", "indicator", "value"]
    assert data.notna().all().all()
    assert not data.duplicated(subset=["country", "year", "indicator"]).any()
    assert set(data["indicator"]) == set(INDICATORS)
    assert set(data["country"]) <= set(COUNTRIES)


def test_every_indicator_has_nigeria(data):
    for key in INDICATORS:
        assert ((data["indicator"] == key) & (data["country"] == "Nigeria")).sum() >= 10, key


def test_values_are_in_sensible_ranges(data):
    for key, spec in INDICATORS.items():
        values = data.loc[data["indicator"] == key, "value"]
        assert (values >= 0).all(), key
        if spec["unit"].startswith("%"):
            assert (values <= 100).all(), key


# ---------- the pipeline (no network needed) ----------

# Small samples in the exact shape the real APIs return
WORLD_BANK_SAMPLE = [
    [{"page": 1, "pages": 1, "per_page": 1000, "total": 3}, [
        {"countryiso3code": "NGA", "date": "2023", "value": 993},
        {"countryiso3code": "SSF", "date": "2023", "value": 448},
        {"countryiso3code": "NGA", "date": "2024", "value": None},
    ]],
]

WHO_SAMPLE = {
    "value": [
        {"SpatialDim": "NGA", "TimeDim": 2024, "Dim1": None, "NumericValue": 184933.0},
        {"SpatialDim": "GLOBAL", "TimeDim": 2024, "Dim1": None, "NumericValue": 609930.0},
        {"SpatialDim": "NGA", "TimeDim": 2024, "Dim1": "SEX_FMLE", "NumericValue": 1.0},
        {"SpatialDim": "FRA", "TimeDim": 2024, "Dim1": None, "NumericValue": 0.0},
    ]
}


def test_parse_world_bank_names_places_and_skips_gaps():
    df = build_dataset.parse_world_bank(WORLD_BANK_SAMPLE)
    assert df.to_dict("records") == [
        {"country": "Nigeria", "year": 2023, "value": 993.0},
        {"country": "Sub-Saharan Africa", "year": 2023, "value": 448.0},
    ]


def test_parse_who_keeps_only_totals_for_our_places():
    df = build_dataset.parse_who(WHO_SAMPLE)
    assert df.to_dict("records") == [
        {"country": "Nigeria", "year": 2024, "value": 184933.0},
        {"country": "World", "year": 2024, "value": 609930.0},
    ]


def test_api_urls():
    wb = build_dataset.world_bank_url("SH.STA.MMRT")
    assert wb.startswith("https://api.worldbank.org/v2/country/NGA;")
    assert "indicator/SH.STA.MMRT?format=json" in wb
    who = build_dataset.who_url("MALARIA_EST_DEATHS")
    assert who.startswith("https://ghoapi.azureedge.net/api/MALARIA_EST_DEATHS?$filter=")
    assert "%27NGA%27" in who and "%27GLOBAL%27" in who


def test_tidy_combines_and_cleans():
    frames = {
        "maternal_mortality": pd.DataFrame(
            {"country": ["Nigeria", "Nigeria", "Nigeria"], "year": [1985, 2023, 2023], "value": [1.234, 993.456, 993.456]}
        ),
        "life_expectancy": pd.DataFrame(columns=["country", "year", "value"]),
    }
    table = build_dataset.tidy(frames)
    assert table.to_dict("records") == [
        {"country": "Nigeria", "year": 2023, "indicator": "maternal_mortality", "value": 993.46}
    ]


# ---------- the analysis ----------

def test_latest_returns_each_countrys_most_recent_year(conn, data):
    latest = analysis.latest(conn, "maternal_mortality")
    nigeria = latest[latest["country"] == "Nigeria"].iloc[0]
    expected_year = data[(data["indicator"] == "maternal_mortality") & (data["country"] == "Nigeria")]["year"].max()
    assert nigeria["year"] == expected_year
    assert latest["country"].is_unique


def test_change_compares_first_and_last_year(conn):
    ch = analysis.change(conn, "under5_mortality")
    assert ch["first_year"] < ch["last_year"]
    assert ch["change"] == pytest.approx(ch["last_value"] - ch["first_value"])
    assert analysis.change(conn, "under5_mortality", "Atlantis") is None


def test_malaria_share_is_a_percentage(conn):
    share = analysis.malaria_share(conn)
    assert not share.empty
    assert share["share_pct"].between(0, 100).all()


def test_annual_rate_of_reduction():
    # Halving over 10 years is about 6.7% a year
    assert analysis.annual_rate_of_reduction(200, 100, 10) == pytest.approx(6.7, abs=0.05)
    assert analysis.annual_rate_of_reduction(100, 100, 10) == 0
    assert analysis.annual_rate_of_reduction(100, 50, 0) == 0


def test_years_to_target():
    assert analysis.years_to_target(50, 70, 2) == 0
    assert analysis.years_to_target(100, 70, 0) is None
    # Falling 10% a year from 100, it takes log(0.5)/log(0.9) ≈ 6.6 years to reach 50
    assert analysis.years_to_target(100, 50, 10) == pytest.approx(math.log(0.5) / math.log(0.9))


def test_key_findings_are_generated(conn):
    findings = analysis.key_findings(conn)
    assert len(findings) == len(INDICATORS) - 1  # measles is shown in charts only
    assert all(f.startswith("**") for f in findings)


# ---------- the charts ----------

def test_spread_labels_never_overlap():
    labels = [{"y": 50}, {"y": 51}, {"y": 52}, {"y": 90}]
    placed = spread_labels(labels, min_gap=5)
    ys = [label["y"] for label in placed]
    assert all(b - a >= 5 for a, b in zip(ys, ys[1:]))
    assert ys[-1] == 90  # labels that weren't crowded stay where they were


# ---------- the app itself ----------

def test_app_runs_without_errors():
    app = AppTest.from_file("../app.py", default_timeout=60).run()
    assert not app.exception
    assert app.title[0].value.endswith("Nigeria Health Dashboard")
    assert len(app.metric) == 6


def test_app_handles_an_empty_selection():
    app = AppTest.from_file("../app.py", default_timeout=60).run()
    app.multiselect[0].set_value([]).run()
    app.slider[0].set_value((2016, 2018)).run()
    assert not app.exception
