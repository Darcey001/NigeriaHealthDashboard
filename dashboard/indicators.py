"""The health indicators in the dashboard: what each one measures and where it comes from.

All sources are published by Our World in Data (OWID) on GitHub, which redistributes data
from the WHO, the UN Inter-agency Group for Child Mortality Estimation and IHME.
"""

OWID_BASE = "https://raw.githubusercontent.com/owid/owid-datasets/master/datasets"

# Nigeria plus neighbours and peers for comparison
COUNTRIES = [
    "Nigeria",
    "Ghana",
    "Niger",
    "Cameroon",
    "Kenya",
    "Ethiopia",
    "South Africa",
    "Sub-Saharan Africa",
    "World",
]

# Note: life expectancy was left out on purpose. The available source (Gapminder/IHME)
# puts Nigeria about 10 years higher than UN estimates, so it could mislead.

FOCUS = "Nigeria"
START_YEAR = 1990

INDICATORS = {
    "maternal_mortality": {
        "label": "Maternal mortality ratio",
        "unit": "deaths per 100,000 live births",
        "better": "lower",
        "dataset": "Maternal Mortality Ratio (Gapminder (2010), WHO (2019) and OECD (2022))",
        "column": "maternal_mortality_rate_who_2019",
        "source": "WHO, UNICEF, UNFPA, World Bank and UN (2019), via Our World in Data",
        "target": 70,
        "target_label": "SDG 2030 target: below 70",
    },
    "under5_mortality": {
        "label": "Under-five mortality rate",
        "unit": "deaths per 1,000 live births",
        "better": "lower",
        "dataset": "Child Mortality Estimates - CME Info (2018)",
        "column": "Child Mortality Estimates (CME Info (2016))",
        "source": "UN Inter-agency Group for Child Mortality Estimation (2018), via Our World in Data",
        "target": 25,
        "target_label": "SDG 2030 target: 25 or lower",
    },
    "malaria_deaths": {
        "label": "Malaria deaths",
        "unit": "deaths per year",
        "better": "lower",
        "dataset": "Malaria deaths - IHME (2016)",
        "column": "Deaths from malaria (IHME 2016)",
        "source": "IHME Global Burden of Disease (2016), via Our World in Data",
        "target": None,
        "target_label": None,
    },
    "dtp3_coverage": {
        "label": "DTP3 vaccine coverage",
        "unit": "% of 1-year-olds",
        "better": "higher",
        "dataset": "Vaccine Coverage and Disease Burden - WHO (2017)",
        "column": "DTP3 immunization coverage among 1-year-olds (WHO 2017)",
        "source": "WHO (2017), via Our World in Data",
        "target": 90,
        "target_label": "WHO goal: 90% national coverage",
    },
    "measles_coverage": {
        "label": "Measles vaccine coverage",
        "unit": "% of 1-year-olds",
        "better": "higher",
        "dataset": "Vaccine Coverage and Disease Burden - WHO (2017)",
        "column": "Measles (MCV) immunization coverage among 1-year-olds (WHO 2017)",
        "source": "WHO (2017), via Our World in Data",
        "target": 90,
        "target_label": "WHO goal: 90% national coverage",
    },
    "tb_treatment_coverage": {
        "label": "TB treatment coverage",
        "unit": "% of estimated TB cases detected and treated",
        "better": "higher",
        "dataset": "Global Tuberculosis Report! TB burden estimates - WHO (2019)",
        "column": "Case detection rate (all forms) [also known as TB treatment coverage], percent (c_cdr)",
        "source": "WHO Global Tuberculosis Report (2019), via Our World in Data",
        "target": 90,
        "target_label": "End TB Strategy: at least 90%",
    },
}
