"""The health indicators in the dashboard: what each one measures and where it comes from.

Data comes straight from two official APIs:
- the World Bank's World Development Indicators (which republish UN and WHO estimates)
- the WHO Global Health Observatory (for malaria deaths)
"""

WORLD_BANK_API = "https://api.worldbank.org/v2"
WHO_API = "https://ghoapi.azureedge.net/api"

# Display name for each country or region, keyed by the code the APIs use
PLACES = {
    "NGA": "Nigeria",
    "GHA": "Ghana",
    "NER": "Niger",
    "CMR": "Cameroon",
    "KEN": "Kenya",
    "ETH": "Ethiopia",
    "ZAF": "South Africa",
    "SSF": "Sub-Saharan Africa",  # World Bank region
    "WLD": "World",  # World Bank
    "AFR": "WHO Africa region",  # WHO region
    "GLOBAL": "World",  # WHO
}

COUNTRIES = list(dict.fromkeys(PLACES.values()))
REGIONS = ["Sub-Saharan Africa", "WHO Africa region", "World"]

FOCUS = "Nigeria"
START_YEAR = 1990

INDICATORS = {
    "maternal_mortality": {
        "label": "Maternal mortality ratio",
        "unit": "deaths per 100,000 live births",
        "better": "lower",
        "api": "worldbank",
        "code": "SH.STA.MMRT",
        "source": "UN Maternal Mortality Estimation Inter-agency Group, via the World Bank",
        "target": 70,
        "target_label": "SDG 2030 target: below 70",
    },
    "under5_mortality": {
        "label": "Under-five mortality rate",
        "unit": "deaths per 1,000 live births",
        "better": "lower",
        "api": "worldbank",
        "code": "SH.DYN.MORT",
        "source": "UN Inter-agency Group for Child Mortality Estimation, via the World Bank",
        "target": 25,
        "target_label": "SDG 2030 target: 25 or lower",
    },
    "malaria_deaths": {
        "label": "Malaria deaths",
        "unit": "deaths per year",
        "better": "lower",
        "api": "who",
        "code": "MALARIA_EST_DEATHS",
        "source": "WHO World Malaria Report, via the WHO Global Health Observatory",
        "target": None,
        "target_label": None,
    },
    "dtp3_coverage": {
        "label": "DTP3 vaccine coverage",
        "unit": "% of children aged 12–23 months",
        "better": "higher",
        "api": "worldbank",
        "code": "SH.IMM.IDPT",
        "source": "WHO and UNICEF immunization estimates, via the World Bank",
        "target": 90,
        "target_label": "WHO goal: 90% national coverage",
    },
    "measles_coverage": {
        "label": "Measles vaccine coverage",
        "unit": "% of children aged 12–23 months",
        "better": "higher",
        "api": "worldbank",
        "code": "SH.IMM.MEAS",
        "source": "WHO and UNICEF immunization estimates, via the World Bank",
        "target": 90,
        "target_label": "WHO goal: 90% national coverage",
    },
    "tb_treatment_coverage": {
        "label": "TB case detection",
        "unit": "% of estimated TB cases found and notified",
        "better": "higher",
        "api": "worldbank",
        "code": "SH.TBS.DTEC.ZS",
        "source": "WHO Global Tuberculosis Report, via the World Bank",
        "target": 90,
        "target_label": "End TB Strategy: at least 90%",
    },
    "life_expectancy": {
        "label": "Life expectancy at birth",
        "unit": "years",
        "better": "higher",
        "api": "worldbank",
        "code": "SP.DYN.LE00.IN",
        "source": "UN World Population Prospects, via the World Bank",
        "target": None,
        "target_label": None,
    },
}
