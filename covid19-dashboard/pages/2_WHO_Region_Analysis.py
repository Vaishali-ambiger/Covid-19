"""WHO region analysis: cases, deaths and recoveries by region."""
import pandas as pd
import streamlit as st

from utils import charts, metrics, ui

ui.setup("WHO Region Analysis", "🗺️")
df, meta = ui.get_data()
ui.sidebar_info(meta)
ui.page_header("WHO Region Analysis", "Compare the six WHO regions: cases, deaths, recoveries and trends.")

reg = metrics.region_summary(df, meta)
cut = meta["recovered_cutoff"]

ui.note("Country-to-region assignment comes from <b>data/who_region_mapping.csv</b>, compiled from WHO's regional groupings. "
        "Cruise ships, event entries and Antarctica are not assigned to a region and are excluded here.")

ui.section("Confirmed cases and deaths by region", f"Totals as of {meta['date_max']:%d %b %Y} (ACTUAL).")
a, b = st.columns(2)
with a:
    st.plotly_chart(charts.grouped_bars(reg, "who_region", {"Confirmed": "confirmed"}, "Confirmed cases by WHO region"), width="stretch")
with b:
    st.plotly_chart(charts.grouped_bars(reg, "who_region", {"Deaths": "deaths"}, "Deaths by WHO region"), width="stretch")

a, b = st.columns(2)
with a:
    st.plotly_chart(charts.donut(reg["who_region"], reg["deaths"], "Share of deaths by region"), width="stretch")
with b:
    d = reg.sort_values("death_rate")
    st.plotly_chart(charts.bar_ranking(d, "death_rate", "who_region", "Death rate by region (% of confirmed, DERIVED)", charts.NAVY, "Death rate (%)"), width="stretch")

# ---------- Recovered ----------
ui.section("Recovered cases by region", "Recoveries are only available up to a fixed date and not for every country.")
if "recovered" in reg and reg["recovered"].notna().any():
    ui.note(f"Values are as of <b>{cut:%d %b %Y}</b>, the last date recoveries were published, and include only countries that reported them. "
            "Regions are therefore <b>not directly comparable</b> with the confirmed totals above (for example, the Americas exclude the United States, which did not report recoveries).")
    st.plotly_chart(charts.grouped_bars(reg.dropna(subset=["recovered"]), "who_region", {"Recovered": "recovered"}, f"Recovered cases by region (as of {cut:%d %b %Y})"), width="stretch")
    show = reg[["who_region", "recovered", "recovered_countries", "countries"]].copy()
    show["Recovery rate % (reporting countries)"] = reg["recovery_rate_reporting"]
    show.columns = ["WHO region", "Recovered", "Countries reporting", "Countries in region", "Recovery rate % (reporting countries)"]
    st.dataframe(show, hide_index=True, width="stretch", column_config={"Recovered": st.column_config.NumberColumn(format="%d"),
                 "Recovery rate % (reporting countries)": st.column_config.NumberColumn(format="%.1f")})
else:
    st.info("Recovered data is not available.")

# ---------- Trend by region ----------
ui.section("Trend by region", "Choose a measure and a date range.")
c1, c2 = st.columns([1, 2])
with c1:
    measure = st.radio("Measure", ["Cumulative confirmed", "Cumulative deaths", "New cases (7-day average)", "New deaths (7-day average)"])
with c2:
    d0, d1 = st.slider("Date range", meta["date_min"].date(), meta["date_max"].date(), (meta["date_min"].date(), meta["date_max"].date()))
col = {"Cumulative confirmed": "confirmed", "Cumulative deaths": "deaths", "New cases (7-day average)": "new_confirmed", "New deaths (7-day average)": "new_deaths"}[measure]
base = df[(df["who_region"] != metrics.NON_COUNTRY)]
trend = base.groupby(["date", "who_region"], observed=True)[col].sum().reset_index()
if "7-day" in measure:
    trend[col] = trend.groupby("who_region", observed=True)[col].transform(lambda s: s.rolling(7, min_periods=7).mean())
trend = trend[(trend["date"] >= pd.Timestamp(d0)) & (trend["date"] <= pd.Timestamp(d1))].rename(columns={"who_region": "country"})
st.plotly_chart(charts.multi_country_lines(trend, col, measure, measure), width="stretch")
