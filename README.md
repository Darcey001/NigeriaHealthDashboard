# 🩺 Nigeria Health Dashboard

An interactive dashboard that tracks how Nigeria is doing on **maternal and child health, malaria, vaccines and tuberculosis**, and compares it with neighbouring countries. Built with **Python, pandas, SQL (SQLite), Plotly and Streamlit**.

![Tests](https://github.com/Darcey001/nigeria-health-dashboard/actions/workflows/tests.yml/badge.svg)

**🔗 Live dashboard:** [nigeria-health-dashboard.onrender.com](https://nigeria-health-dashboard.onrender.com) (the free server sleeps when unused, so the first visit can take about a minute)

## Why I built this

Before studying computer science, I trained in medicine. Nigeria carries some of the world's heaviest burdens of preventable maternal and child deaths, and I wanted to see the trends clearly: where things have improved, where they have stalled, and how far there is to go. This project turns public WHO, UN and IHME data into something anyone can explore.

## 🔍 Key findings

| | Nigeria | What it means |
|---|---|---|
| **Maternal deaths** | 917 per 100,000 live births (2017) | The highest of the 7 countries compared. It fell 24% since 2000, but at that pace reaching the UN target of 70 would take about **160 years**. |
| **Child deaths** | 100 per 1,000 births (2017) | More than halved since 1990 (212), but about **1 in 10 children** still die before age five. |
| **Malaria** | 231,579 deaths (2016) | **36% of all malaria deaths** in Sub-Saharan Africa, up from 31% in 1990. |
| **Vaccines** | 56% DTP3 coverage (2015) | **The same as in 1990**, and the lowest in the group. The WHO goal is 90%. |
| **Tuberculosis** | 24% of cases treated (2018) | Roughly **3 in 4 TB cases are missed**. |

The dashboard works these out from the data rather than hard-coding them.

## ✨ Features

- **Headline numbers** for Nigeria, with the change since the first year of data
- **Key findings** generated from the data, including the yearly rate of decline and the years needed to reach the UN 2030 targets at that pace
- **Interactive charts:** compare Nigeria with Ghana, Niger, Cameroon, Kenya, Ethiopia, South Africa, Sub-Saharan Africa and the world, and filter by year
- **Rankings** of each country's latest value
- **Data & SQL tab** showing the SQL behind the dashboard, the full dataset, and a CSV download
- Works in **light and dark mode** and **on phones**

## 🛠️ Tech stack

| Part | Tools |
|---|---|
| Data pipeline | Python, pandas |
| Analysis | SQL (SQLite): window functions, CTEs, joins |
| Charts | Plotly |
| Web app | Streamlit |
| Testing | pytest, Streamlit AppTest, GitHub Actions |
| Hosting | Render |

## 🏗️ How it works

```
Our World in Data (WHO, UN, IHME)
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

## 🚀 Run it locally

You need Python 3.11 or newer.

```bash
pip install -r requirements.txt
streamlit run app.py          # opens http://localhost:8501
```

To rebuild the dataset from the original sources:

```bash
python pipeline/build_dataset.py
```

This also happens automatically: a GitHub Action (`build-data.yml`) reruns the pipeline and commits the updated dataset whenever the pipeline or the list of indicators changes.

## 🧪 Tests

```bash
pytest
```

14 tests check that the dataset is complete and valid (no gaps, duplicates or impossible values), that the SQL queries and calculations are correct, that chart labels never overlap, and that the whole app runs without errors, including when every filter is cleared. They run automatically on every push.

## 📚 Data sources and limitations

| Indicator | Source |
|---|---|
| Maternal mortality ratio | WHO, UNICEF, UNFPA, World Bank and UN (2019) |
| Under-five mortality | UN Inter-agency Group for Child Mortality Estimation (2018) |
| Malaria deaths | IHME Global Burden of Disease (2016) |
| DTP3 and measles vaccine coverage | WHO (2017) |
| TB treatment coverage | WHO Global Tuberculosis Report (2019) |

All data comes via [Our World in Data](https://github.com/owid/owid-datasets).

**Limitations to keep in mind:**
- The most recent figures in these sources are from **2015–2018**, so the dashboard shows long-term trends, not today's situation.
- These are **modelled estimates** with uncertainty ranges that aren't shown.
- **National averages hide big differences** between Nigerian states, for example between the north and south.
- **Life expectancy was left out on purpose:** the available source puts Nigeria about 10 years higher than UN estimates, so it could mislead.

## 🗺️ What's next

- [ ] Update to the latest WHO and World Bank data
- [ ] Add state-level data (Nigeria Demographic and Health Survey)
- [ ] Show uncertainty ranges on the charts

## 👩🏾‍💻 Author

**Praise Emmanuel** · [GitHub](https://github.com/Darcey001) · [LinkedIn](https://www.linkedin.com/in/praise-emmanuel-894047223/)
