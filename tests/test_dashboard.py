import math

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard import analysis
from dashboard.charts import spread_labels
from dashboard.indicators import COUNTRIES, INDICATORS
from pipeline.build_dataset import dataset_url, load_indicator


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

def test_dataset_url_is_encoded():
    url = dataset_url("Malaria deaths - IHME (2016)")
    assert url.endswith("/Malaria%20deaths%20-%20IHME%20%282016%29/Malaria%20deaths%20-%20IHME%20%282016%29.csv")


def test_load_indicator_keeps_only_our_countries_and_years():
    spec = INDICATORS["dtp3_coverage"]
    raw = pd.DataFrame(
        {
            "Entity": ["Nigeria", "Nigeria", "France", "Ghana"],
            "Year": [1985, 2000, 2000, 2001],
            spec["column"]: [10, 30, 95, None],
        }
    )
    tidy = load_indicator("dtp3_coverage", spec, {spec["dataset"]: raw})
    assert tidy.to_dict("records") == [
        {"country": "Nigeria", "year": 2000, "value": 30, "indicator": "dtp3_coverage"}
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
    assert len(findings) == 5
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
    assert len(app.metric) == 5


def test_app_handles_an_empty_selection():
    app = AppTest.from_file("../app.py", default_timeout=60).run()
    app.multiselect[0].set_value([]).run()
    app.slider[0].set_value((2016, 2018)).run()
    assert not app.exception
