"""Interactive world map and monthly heatmap."""
import pandas as pd
import streamlit as st

from utils import charts, metrics, ui

ui.setup("Maps and Heatmaps", "🗺️")
df, meta = ui.get_data()
ui.sidebar_info(meta)
ui.page_header("Maps and Heatmaps", "See where the pandemic hit hardest, and when.")

base = df[df["who_region"] != metrics.NON_COUNTRY]
OPTIONS = {
    "Confirmed cases": ("confirmed", "Confirmed", True),
    "Deaths": ("deaths", "Deaths", True),
    "Death rate (% of confirmed)": ("death_rate", "Death rate %", False),
    "Confirmed cases per 100,000 people": ("confirmed_per_100k", "Cases per 100k", False),
    "Deaths per 100,000 people": ("deaths_per_100k", "Deaths per 100k", False),
}

ui.section("World map")
c1, c2, c3 = st.columns([2, 2, 1])
with c1:
    choice = st.selectbox("Map metric", list(OPTIONS))
with c2:
    as_of = st.slider("Data as of", meta["date_min"].date(), meta["date_max"].date(), meta["date_max"].date())
metric, label, is_count = OPTIONS[choice]
with c3:
    log_color = st.checkbox("Log colour scale", value=is_count, help="Counts vary enormously between countries. A log scale makes smaller countries visible.")

snap = metrics.snapshot(base, pd.Timestamp(as_of))
if metric == "death_rate":
    snap = snap[snap["confirmed"] >= 1000]
    ui.note("Death rate is shown only for countries with at least 1,000 confirmed cases, because tiny counts give unstable percentages.")
st.plotly_chart(charts.world_map(snap, metric, label, log_color=log_color and is_count), width="stretch")
missing = snap[snap["iso3"].isna()]["country"].tolist()
if missing:
    st.caption("Not drawn on the map (no country code): " + ", ".join(missing))

ui.section("Monthly heatmap", "Each cell is the total number of new cases (or deaths) in that month. Darker means more.")
c1, c2 = st.columns(2)
with c1:
    n = st.slider("Countries to show (largest by confirmed cases)", 8, 30, 15)
with c2:
    what = st.radio("Value", ["New confirmed cases", "New deaths"], horizontal=True)
value = "new_confirmed" if what == "New confirmed cases" else "new_deaths"
top = list(metrics.snapshot(base, meta["date_max"]).nlargest(n, "confirmed")["country"])
pv = metrics.monthly_heatmap_data(base, top, value)
st.plotly_chart(charts.heatmap(pv, f"{what} per month", height=max(420, 26 * n + 150)), width="stretch")
ui.note("Monthly totals are DERIVED from daily differences. Countries differ in how and when they tested and reported, so colours are not a measure of true infection levels.")
