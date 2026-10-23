"""Nigeria Health Dashboard: a Streamlit app.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st

from dashboard import analysis
from dashboard.charts import ranking_chart, trend_chart
from dashboard.indicators import COUNTRIES, FOCUS, INDICATORS, REGIONS

st.set_page_config(page_title="Nigeria Health Dashboard", page_icon="🩺", layout="wide")


@st.cache_resource
def get_connection():
    return analysis.connect()


conn = get_connection()
first_year, last_year = analysis.query(conn, "SELECT MIN(year), MAX(year) FROM health").iloc[0]
first_year, last_year = int(first_year), int(last_year)

# ---------- sidebar filters ----------

with st.sidebar:
    st.header("Filters")
    others = [c for c in COUNTRIES if c != FOCUS]
    compare = st.multiselect(
        "Compare Nigeria with",
        others,
        default=["Ghana", "Niger", "Kenya", "Sub-Saharan Africa"],
        help="Regional averages appear on charts where the source publishes them.",
    )
    years = st.slider("Years", first_year, last_year, (first_year, last_year))
    st.divider()
    st.caption(
        "Built by **Praise Emmanuel** · "
        "[GitHub](https://github.com/Darcey001) · "
        "[LinkedIn](https://www.linkedin.com/in/praise-emmanuel-894047223/)"
    )

shown = [FOCUS, *compare]

# ---------- header ----------

st.title("🩺 Nigeria Health Dashboard")
st.markdown(
    "How is Nigeria doing on **maternal and child health, malaria, vaccines and tuberculosis**, "
    "and how does it compare with its neighbours? Every number below is calculated with SQL "
    "from the latest World Bank and WHO data."
)
st.caption(f"📈 Long-term trends, {first_year}–{last_year} · each figure shows the year it comes from")

# ---------- headline numbers ----------

TILES = [
    ("maternal_mortality", "Maternal deaths", "per 100,000 births", ",.0f"),
    ("under5_mortality", "Under-5 deaths", "per 1,000 births", ".0f"),
    ("malaria_deaths", "Malaria deaths", "per year", ",.0f"),
    ("dtp3_coverage", "DTP3 vaccine", "of young children", ".0f"),
    ("tb_treatment_coverage", "TB cases found", "of estimated cases", ".0f"),
    ("life_expectancy", "Life expectancy", "years at birth", ".1f"),
]

cols = st.columns(len(TILES))
for col, (key, label, suffix, fmt) in zip(cols, TILES):
    spec = INDICATORS[key]
    ch = analysis.change(conn, key, FOCUS)
    is_pct = spec["unit"].startswith("%")
    value = format(ch["last_value"], fmt) + ("%" if is_pct else "")
    since = int(ch["first_year"])
    if ch["change"] == 0:
        delta = "no change"
    elif is_pct:
        delta = f"{ch['change']:+.0f} pts"  # percentage points
    elif spec["unit"] == "years":
        delta = f"{ch['change']:+.1f} years"
    else:
        delta = f"{ch['pct_change']:+.0f}%"
    if ch["change"] == 0:
        delta_color = "off"  # no change: show it in grey, not as good or bad
    else:
        delta_color = "inverse" if spec["better"] == "lower" else "normal"
    col.metric(
        label,
        value,
        delta,
        delta_color=delta_color,
        help=f"{spec['label']}, {spec['unit']}. Source: {spec['source']}.",
    )
    col.caption(f"{suffix} · {int(ch['last_year'])}  \nchange since {since}")

# ---------- key findings ----------

with st.container(border=True):
    st.subheader("Key findings")
    for finding in analysis.key_findings(conn, FOCUS):
        st.markdown(f"- {finding}")


# ---------- one section per indicator ----------

def indicator_section(key: str, value_format: str = ",.0f") -> None:
    spec = INDICATORS[key]
    data = analysis.series(conn, key, *years)
    data = data[data["country"].isin(shown)]

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(f"**{spec['label']}** · {spec['unit']}")
        if spec["target_label"]:
            st.caption(f"Dotted line = {spec['target_label']}")
        if data.empty:
            st.info("No data for these years. Try widening the year range.")
        else:
            fig = trend_chart(
                data,
                FOCUS,
                spec["unit"],
                spec["target"],
                value_format=value_format,
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    with right:
        latest = analysis.latest(conn, key)
        latest = latest[latest["country"].isin(shown)]
        if spec["unit"] == "deaths per year":
            # Raw counts (like total deaths) aren't comparable with whole regions
            latest = latest[~latest["country"].isin(REGIONS)]
        st.markdown(f"**Latest value** · {'lower' if spec['better'] == 'lower' else 'higher'} is better")
        fig = ranking_chart(latest, FOCUS, spec["unit"], spec["better"], value_format)
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.caption(f"Source: {spec['source']}")


tabs = st.tabs(
    [
        "👩🏾‍🍼 Mothers & children",
        "🦟 Malaria",
        "💉 Vaccines",
        "🫁 Tuberculosis",
        "❤️ Life expectancy",
        "🗄️ Data & SQL",
    ]
)

with tabs[0]:
    indicator_section("maternal_mortality")
    st.divider()
    indicator_section("under5_mortality", ".0f")

with tabs[1]:
    share = analysis.malaria_share(conn)
    share = share[share["year"].between(*years)]
    st.markdown("**Nigeria's share of all malaria deaths in the world** · %")
    if not share.empty:
        fig = trend_chart(
            share.rename(columns={"share_pct": "value"}).assign(country=FOCUS),
            FOCUS,
            "% of the world's malaria deaths",
            value_format=".1f",
        )
        fig.update_yaxes(range=[0, 50])
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
    st.divider()
    indicator_section("malaria_deaths")

with tabs[2]:
    indicator_section("dtp3_coverage", ".0f")
    st.divider()
    indicator_section("measles_coverage", ".0f")

with tabs[3]:
    indicator_section("tb_treatment_coverage", ".0f")

with tabs[4]:
    indicator_section("life_expectancy", ".1f")

with tabs[5]:
    st.markdown(
        "The cleaned dataset has one row per **country, year and indicator**. "
        "It's loaded into SQLite, and these queries power the dashboard:"
    )
    for title, sql in [
        ("Trend over time", analysis.SERIES_SQL),
        ("Each country's latest value (window function)", analysis.LATEST_SQL),
        ("Change since the first year (CTE + self-join)", analysis.CHANGE_SQL),
        ("Nigeria's share of the world's malaria deaths (join)", analysis.MALARIA_SHARE_SQL),
    ]:
        with st.expander(title):
            st.code(sql.strip(), language="sql")

    df = analysis.query(conn, "SELECT * FROM health ORDER BY indicator, country, year")
    st.dataframe(df, width="stretch", hide_index=True, height=300)
    st.download_button(
        "Download the data (CSV)",
        df.to_csv(index=False),
        file_name="nigeria_health_indicators.csv",
        mime="text/csv",
    )

# ---------- footer ----------

st.divider()
st.caption(
    "**Sources:** [World Bank World Development Indicators](https://data.worldbank.org) (UN and "
    "WHO estimates) and the [WHO Global Health Observatory](https://www.who.int/data/gho). "
    "**Notes:** these are modelled estimates with uncertainty ranges not shown here, and national "
    "averages hide big differences between Nigerian states. The latest year varies by indicator."
)
