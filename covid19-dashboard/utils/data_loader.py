"""
Data loading, cleaning and validation.

Pipeline (see the "Data Quality" page for the results):
 1. Read the JHU CSSE time-series files (confirmed, deaths, recovered) and the lookup table.
 2. Clean: trim names, drop duplicate rows, coerce numbers, standardise country names.
 3. Aggregate provinces/states to country level.
 4. Reshape wide -> long (one row per country per date).
 5. Add WHO region (data/who_region_mapping.csv), ISO3 code and population (lookup table).
 6. Handle recovered data honestly (it was discontinued) and derive daily values.

Nothing is invented: values that are not reported stay empty (NaN).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FILES = {
    "confirmed": "time_series_covid19_confirmed_global.csv",
    "deaths": "time_series_covid19_deaths_global.csv",
    "recovered": "time_series_covid19_recovered_global.csv",
    "lookup": "UID_ISO_FIPS_LookUp_Table.csv",
    "regions": "who_region_mapping.csv",
}

# Inconsistent / awkward source names -> clear display names
COUNTRY_NAME_FIXES = {
    "US": "United States",
    "Korea, South": "South Korea",
    "Korea, North": "North Korea",
    "Taiwan*": "Taiwan",
    "Burma": "Myanmar",
    "Congo (Brazzaville)": "Republic of the Congo",
    "Congo (Kinshasa)": "DR Congo",
    "Cote d'Ivoire": "Côte d'Ivoire",
    "Holy See": "Vatican City",
    "West Bank and Gaza": "Palestine (West Bank and Gaza)",
    "Czechia": "Czech Republic",
}

SOURCE_TEXT = (
    "Johns Hopkins University CSSE COVID-19 Data Repository "
    "(github.com/CSSEGISandData/COVID-19, licence CC BY 4.0)"
)


class DataNotFoundError(Exception):
    """Raised when a required data file is missing or unreadable."""


def _read_csv(key: str) -> pd.DataFrame:
    path = DATA_DIR / FILES[key]
    if not path.exists():
        raise DataNotFoundError(
            f"Missing data file: {path.name}\n\n"
            "Fix: open a terminal in the project folder and run:\n    python utils/download_data.py"
        )
    try:
        return pd.read_csv(path)
    except Exception as err:  # corrupt or empty file
        raise DataNotFoundError(f"Could not read {path.name}: {err}") from err


def _tidy_wide(raw: pd.DataFrame, value_name: str, log: dict) -> pd.DataFrame:
    """Clean one wide time-series table and return a long table (country, date, value)."""
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df["Country/Region"] = df["Country/Region"].astype(str).str.strip()
    log[f"{value_name}_rows_raw"] = len(df)

    # Remove duplicate (province, country) rows
    dup = df.duplicated(subset=["Province/State", "Country/Region"], keep="first")
    log[f"{value_name}_duplicate_rows_removed"] = int(dup.sum())
    df = df.loc[~dup]

    date_cols = [c for c in df.columns if c not in ("Province/State", "Country/Region", "Lat", "Long")]
    values = df[date_cols].apply(pd.to_numeric, errors="coerce")  # validate numbers
    log[f"{value_name}_non_numeric_cells"] = int(values.isna().sum().sum())
    values = values.fillna(0).clip(lower=0)  # non-numeric -> 0 only for cumulative sums (counted above)

    by_country = values.groupby(df["Country/Region"]).sum()
    long = by_country.stack().rename(value_name).reset_index()
    long.columns = ["country_raw", "date_str", value_name]
    long["date"] = pd.to_datetime(long["date_str"], format="%m/%d/%y")
    return long.drop(columns="date_str")


@st.cache_data(show_spinner="Loading and cleaning data...")
def load_data() -> dict:
    """Returns {'df': long table, 'meta': dict}. Cached so it only runs once per session."""
    log: dict = {}
    confirmed = _tidy_wide(_read_csv("confirmed"), "confirmed", log)
    deaths = _tidy_wide(_read_csv("deaths"), "deaths", log)
    recovered = _tidy_wide(_read_csv("recovered"), "recovered", log)

    df = confirmed.merge(deaths, on=["country_raw", "date"], how="outer").merge(
        recovered, on=["country_raw", "date"], how="outer"
    )
    df = df.sort_values(["country_raw", "date"]).reset_index(drop=True)
    log["countries_total"] = int(df["country_raw"].nunique())

    # ---- Recovered data: discontinued by the source, so treat later zeros as "not reported" ----
    daily_global_rec = df.groupby("date")["recovered"].sum()
    reported = daily_global_rec[daily_global_rec > 0]
    recovered_cutoff = reported.index.max() if len(reported) else pd.NaT
    log["recovered_last_reported_date"] = recovered_cutoff

    # A country counts as a "recovered reporter" only if it was still publishing recoveries at the cut-off
    # (last positive value within 7 days of it). Countries that never reported, or stopped earlier, are left empty
    # for ALL dates so that regional and global totals are built from the same group of countries over time.
    last_positive = df[df["recovered"] > 0].groupby("country_raw")["date"].max()
    if pd.notna(recovered_cutoff):
        reporters = last_positive[last_positive >= recovered_cutoff - pd.Timedelta(days=7)].index
    else:
        reporters = pd.Index([])
    df["recovered_reported"] = df["country_raw"].isin(reporters)
    all_countries = df["country_raw"].unique()
    excluded = pd.DataFrame({"country_raw": [c for c in all_countries if c not in set(reporters)]})
    excluded["last_reported"] = excluded["country_raw"].map(last_positive)
    log["countries_reporting_recovered"] = int(len(reporters))
    log["countries_never_reported_recovered"] = int(excluded["last_reported"].isna().sum())
    log["countries_stopped_reporting_recovered_early"] = int(excluded["last_reported"].notna().sum())
    log["countries_not_reporting_recovered"] = int(len(excluded))

    ok = df["recovered_reported"] & (df["date"] <= recovered_cutoff)
    df.loc[~ok, "recovered"] = np.nan

    # ---- Derived: active cases (only where recovered is reported and the result is not negative) ----
    active = df["confirmed"] - df["deaths"] - df["recovered"]
    log["active_negative_values_removed"] = int((active < 0).sum())
    df["active"] = active.where(active >= 0)

    # ---- Cumulative-series corrections (decreases) and daily values ----
    g = df.groupby("country_raw")
    for col in ("confirmed", "deaths"):
        diff = g[col].diff().fillna(df[col])
        log[f"{col}_downward_corrections"] = int((diff < 0).sum())
        df[f"new_{col}_raw"] = diff
        df[f"new_{col}"] = diff.clip(lower=0)  # charts use non-negative daily values
    rec_diff = g["recovered"].diff()
    df["new_recovered"] = rec_diff.clip(lower=0)

    # ---- Names, WHO region, ISO code, population ----
    df["country"] = df["country_raw"].replace(COUNTRY_NAME_FIXES)
    log["country_names_standardised"] = int(sum(n in COUNTRY_NAME_FIXES for n in df["country_raw"].unique()))

    regions = _read_csv("regions")[["country_raw", "who_region"]]
    regions["country_raw"] = regions["country_raw"].str.strip()
    df = df.merge(regions, on="country_raw", how="left")
    df["who_region"] = df["who_region"].fillna("Unassigned")
    log["countries_unassigned_region"] = int(df.loc[df["who_region"] == "Unassigned", "country_raw"].nunique())

    lookup = _read_csv("lookup")
    lookup = lookup[lookup["Province_State"].isna() & lookup["Admin2"].isna()]
    lookup = lookup.drop_duplicates("Country_Region")[["Country_Region", "iso3", "Population"]]
    lookup.columns = ["country_raw", "iso3", "population"]
    df = df.merge(lookup, on="country_raw", how="left")
    log["countries_without_iso3"] = int(df.loc[df["iso3"].isna(), "country_raw"].nunique())
    log["countries_without_population"] = int(df.loc[df["population"].isna(), "country_raw"].nunique())

    df["who_region"] = df["who_region"].astype("category")  # smaller memory footprint

    excluded["country"] = excluded["country_raw"].replace(COUNTRY_NAME_FIXES)
    excluded = excluded.merge(df[["country_raw", "who_region"]].drop_duplicates(), on="country_raw", how="left")
    meta = {
        "recovered_excluded": excluded[["country", "who_region", "last_reported"]].sort_values("country").reset_index(drop=True),
        "source": SOURCE_TEXT,
        "date_min": df["date"].min(),
        "date_max": df["date"].max(),
        "recovered_cutoff": recovered_cutoff,
        "n_countries": log["countries_total"],
        "log": log,
    }
    return {"df": df, "meta": meta}
