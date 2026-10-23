# Nigeria Health Dashboard

An interactive dashboard that tracks how Nigeria is doing on **maternal and child health, malaria, vaccines and tuberculosis**, and compares it with neighbouring countries. Built with **Python, pandas, SQL (SQLite), Plotly and Streamlit**.

![Tests](https://github.com/Darcey001/NigeriaHealthDashboard/actions/workflows/tests.yml/badge.svg)

** Live dashboard:** [nigeria-health-dashboard.onrender.com](https://nigeria-health-dashboard.onrender.com) (the free server sleeps when unused, so the first visit can take about a minute)

## Why I built this

Before studying computer science, I trained in medicine. Nigeria carries some of the world's heaviest burdens of preventable maternal and child deaths, and I wanted to see the trends clearly: where things have improved, where they have stalled, and how far there is to go. This project turns the latest official World Bank, UN and WHO data into something anyone can explore.

## Key findings

| | Nigeria | What it means |
|---|---|---|
| **Maternal deaths** | 993 per 100,000 live births (2023) | The highest of the 7 countries compared and **2.2 times** the Sub-Saharan average. It fell 23% since 1990, but at that pace reaching the UN target of 70 would take centuries. |
| **Child deaths** | 116 per 1,000 births (2024) | Down 44% since 1990, but about **1 in 9 children** still die before age five. |
| **Malaria** | 184,933 deaths (2024) | **30% of all malaria deaths in the world.** |
| **Vaccines** | 67% DTP3 coverage (2024) | Up from 56% in 1990, but still **the lowest** in the group. The WHO goal is 90%. |
| **Tuberculosis** | 79% of cases found (2024) | **A real success:** up from 9% in 2000. |
| **Life expectancy** | 54.6 years (2024) | About **8 years below** the Sub-Saharan average and 19 below the world average. |

The dashboard works these out from the data rather than hard-coding them, so they update when the data does.

##  Features

- **Headline numbers** for Nigeria, with the change since the first year of data
- **Key findings** generated from the data, including the yearly rate of decline and the years needed to reach the UN 2030 targets at that pace
- **Always up to date:** data comes straight from the World Bank and WHO APIs
- **Interactive charts:** compare Nigeria with Ghana, Niger, Cameroon, Kenya, Ethiopia, South Africa, Sub-Saharan Africa and the world, and filter by year
- **Rankings** of each country's latest value
- **Data & SQL tab** showing the SQL behind the dashboard, the full dataset, and a CSV download
- Works in **light and dark mode** and **on phones**

## Tech stack

| Part | Tools |
|---|---|
| Data pipeline | Python, pandas, World Bank and WHO REST APIs |
| Analysis | SQL (SQLite): window functions, CTEs, joins |
| Charts | Plotly |
| Web app | Streamlit |
| Testing | pytest, Streamlit AppTest, GitHub Actions |
| Hosting | Render |

##  How it works

```
World Bank API + WHO API
        │  pipeline/build_dataset.py  ← downloads, filters, tidies
        ▼
data/health_indicators.csv          ← one row per country, year, indicator
        │  dashboard/analysis.py     ← loads into SQLite and runs SQL queries
        ▼
app.py (Streamlit + Plotly)         ← the interactive dashboard
```

An example of the SQL, finding each country's most recent value with a window function:

```sql
SELECT country, year, value
FROM (
    SELECT country, year, value,
           ROW_NUMBER() OVER (PARTITION BY country ORDER BY year DESC) AS rn
    FROM health
    WHERE indicator = :indicator
)
WHERE rn = 1
ORDER BY value
```

##  Run it locally

You need Python 3.11 or newer.

```bash
pip install -r requirements.txt
streamlit run app.py          # opens http://localhost:8501
```

To download the latest data again:

```bash
python pipeline/build_dataset.py
```

This also happens automatically: a GitHub Action (`build-data.yml`) reruns the pipeline and commits the updated dataset whenever the pipeline or the list of indicators changes.

## Tests

```bash
pytest
```

16 tests check that the dataset is complete and valid (no gaps, duplicates or impossible values), that the API responses are parsed correctly, that the SQL queries and calculations are correct, that chart labels never overlap, and that the whole app runs without errors, including when every filter is cleared. They run automatically on every push.

## Data sources

| Indicator | Source |
|---|---|
| Maternal mortality ratio | UN Maternal Mortality Estimation Inter-agency Group, via the World Bank |
| Under-five mortality | UN Inter-agency Group for Child Mortality Estimation, via the World Bank |
| Malaria deaths | WHO World Malaria Report, via the WHO Global Health Observatory |
| DTP3 and measles vaccine coverage | WHO and UNICEF immunization estimates, via the World Bank |
| TB case detection | WHO Global Tuberculosis Report, via the World Bank |
| Life expectancy | UN World Population Prospects, via the World Bank |

The most recent year differs by indicator (2023 or 2024), and each number on the dashboard shows the year it comes from. These are modelled estimates, and national averages hide big differences between Nigerian states.

##  What's next

- [x] Use the latest WHO and World Bank data
- [ ] Add state-level data (Nigeria Demographic and Health Survey)
- [ ] Show uncertainty ranges on the charts

## Author

**Praise Emmanuel** · [GitHub](https://github.com/Darcey001) · [LinkedIn](https://www.linkedin.com/in/praise-emmanuel-894047223/)
