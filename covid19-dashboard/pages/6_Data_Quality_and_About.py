"""Data source, cleaning log, definitions and limitations."""
import pandas as pd
import streamlit as st

from utils import ui
from utils.data_loader import COUNTRY_NAME_FIXES

ui.setup("Data Quality and About", "🧪")
df, meta = ui.get_data()
ui.sidebar_info(meta)
ui.page_header("Data Quality and About", "Where the data comes from, how it was cleaned, and what it cannot tell you.")
log = meta["log"]

ui.section("Source and coverage")
st.markdown(
    f"- **Source:** {meta['source']}\n"
    f"- **Files used:** confirmed, deaths and recovered global time series, plus the UID/ISO lookup table (country codes and population).\n"
    f"- **Date coverage:** {meta['date_min']:%d %B %Y} to {meta['date_max']:%d %B %Y} ({(meta['date_max'] - meta['date_min']).days + 1:,} days).\n"
    f"- **Entries:** {meta['n_countries']} countries/regions (includes a few non-country entries such as cruise ships).\n"
    f"- **Recoveries last published:** {meta['recovered_cutoff']:%d %B %Y}.\n"
    "- The source stopped updating after the last date shown, so this is a historical dataset."
)

ui.section("Cleaning and validation log", "Results of the automatic checks run when the data was loaded.")
rows = [
    ("Raw rows read (confirmed / deaths / recovered)", f"{log['confirmed_rows_raw']} / {log['deaths_rows_raw']} / {log['recovered_rows_raw']}", "Rows are provinces or states plus countries."),
    ("Duplicate rows removed", log["confirmed_duplicate_rows_removed"] + log["deaths_duplicate_rows_removed"] + log["recovered_duplicate_rows_removed"], "Same province and country appearing twice."),
    ("Non-numeric cells found", log["confirmed_non_numeric_cells"] + log["deaths_non_numeric_cells"] + log["recovered_non_numeric_cells"], "Checked by converting every value to a number."),
    ("Provinces combined into countries", f"{log['countries_total']} countries", "Values summed per country."),
    ("Country names standardised", log["country_names_standardised"], "For example US -> United States, Burma -> Myanmar."),
    ("Countries not assigned a WHO region", log["countries_unassigned_region"], "Cruise ships, event entries and Antarctica."),
    ("Countries without map code / population", f"{log['countries_without_iso3']} / {log['countries_without_population']}", "Left empty, never guessed."),
    ("Countries with usable recovered data", log["countries_reporting_recovered"], f"{log['countries_never_reported_recovered']} never reported recoveries and {log['countries_stopped_reporting_recovered_early']} stopped reporting early. All {log['countries_not_reporting_recovered']} are left empty."),
    ("Downward corrections in cumulative confirmed / deaths", f"{log['confirmed_downward_corrections']} / {log['deaths_downward_corrections']}", "Cumulative totals sometimes decrease when the source corrects them. Daily values are floored at zero in charts."),
    ("Negative active-case values removed", log["active_negative_values_removed"], "Where recovered exceeded confirmed minus deaths, active is left empty."),
]
st.dataframe(pd.DataFrame(rows, columns=["Check", "Result", "What it means"]).astype(str), hide_index=True, width="stretch")

ui.section("Actual vs derived values")
st.table(pd.DataFrame([
    ("Confirmed cases, deaths, recovered", "ACTUAL", "Reported by the source (cumulative)."),
    ("Death rate", "DERIVED", "Deaths ÷ confirmed cases. A reported ratio, not true mortality."),
    ("Active cases", "DERIVED", "Confirmed − deaths − recovered. Only where recovered was reported and the result is not negative."),
    ("Daily new cases / deaths / recoveries", "DERIVED", "Difference between consecutive cumulative values."),
    ("7-day average", "DERIVED", "Rolling mean of daily values."),
    ("Per-100,000 values", "DERIVED", "Value ÷ population × 100,000, using population from the source lookup table."),
    ("WHO region", "REFERENCE", "From data/who_region_mapping.csv, compiled from WHO's regional groupings."),
], columns=["Measure", "Type", "How it is obtained"]))

ui.section("Limitations")
st.markdown(
    "- **Recovered and active cases are incomplete.** The source stopped publishing recoveries in August 2021, and some countries (including the United States, Belgium and Serbia) stopped reporting earlier or never reported. Those countries are left out of recovered and active totals for all dates so the totals stay comparable over time.\n"
    "- **Reported cases are not true infections.** Testing capacity and reporting rules differ between countries and over time.\n"
    "- **Death rates are reported ratios** and depend on testing, reporting delays and population age structure.\n"
    "- **Population is a single fixed value** per country, so per-100,000 values are approximate.\n"
    "- **WHO region mapping is a reference table** maintained in this project. A few entries (for example Kosovo, Taiwan, Holy See) are not WHO member states and are placed by WHO convention or geography, noted in the CSV."
)

with st.expander("Country name standardisation"):
    st.dataframe(pd.DataFrame(list(COUNTRY_NAME_FIXES.items()), columns=["Name in source", "Name used here"]), hide_index=True, width="stretch")

no_rec = meta["recovered_excluded"].copy()
no_rec["last_reported"] = no_rec["last_reported"].dt.strftime("%d %b %Y").fillna("Never reported")
with st.expander(f"Countries left out of recovered and active totals ({len(no_rec)})"):
    st.dataframe(no_rec.rename(columns={"country": "Country", "who_region": "WHO region", "last_reported": "Last date recoveries were reported"}), hide_index=True, width="stretch")

with st.expander("Preview of the cleaned dataset"):
    st.dataframe(df[df["date"] == meta["date_max"]].drop(columns=["country_raw", "recovered_reported"]).head(50), hide_index=True, width="stretch")
