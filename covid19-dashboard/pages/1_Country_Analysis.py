"""Country-wise analysis: rankings, comparison charts and interactive country selection."""
import pandas as pd
import streamlit as st

from utils import charts, metrics, ui

ui.setup("Country Analysis", "🌐")
df, meta = ui.get_data()
ui.sidebar_info(meta)
ui.page_header("Country-Wise Analysis", "Rank countries, then compare any selection side by side.")

countries_df = df[df["who_region"] != metrics.NON_COUNTRY]
METRICS = {
    "Confirmed cases": ("confirmed", "Confirmed cases"),
    "Deaths": ("deaths", "Deaths"),
    "Death rate (% of confirmed)": ("death_rate", "Death rate (%)"),
    "Confirmed cases per 100,000 people": ("confirmed_per_100k", "Cases per 100,000"),
    "Deaths per 100,000 people": ("deaths_per_100k", "Deaths per 100,000"),
}

with st.sidebar:
    st.subheader("Filters")
    as_of = st.date_input("Data as of", value=meta["date_max"].date(), min_value=meta["date_min"].date(), max_value=meta["date_max"].date())
    regions = st.multiselect("WHO regions", sorted(countries_df["who_region"].unique()), default=sorted(countries_df["who_region"].unique()))
    metric_name = st.selectbox("Ranking metric", list(METRICS))
    top_n = st.slider("Number of countries in ranking", 5, 25, 10)

metric, label = METRICS[metric_name]
snap = metrics.snapshot(countries_df, pd.Timestamp(as_of))
snap = snap[snap["who_region"].isin(regions)]

# ---------- Ranking ----------
ui.section(f"Top {top_n} countries: {metric_name.lower()}", f"As of {as_of:%d %b %Y}.")
ranked = snap
if metric == "death_rate":
    min_cases = st.slider("Minimum confirmed cases (avoids misleading rates from tiny counts)", 100, 1_000_000, 10_000, step=100)
    ranked = snap[snap["confirmed"] >= min_cases]
elif metric.endswith("per_100k"):
    ui.note("Per-100,000 values use population from the source lookup table (DERIVED). Countries without population data are left out.")
ranked = ranked.dropna(subset=[metric]).nlargest(top_n, metric)
if ranked.empty:
    st.info("No countries match the current filters.")
else:
    st.plotly_chart(charts.bar_ranking(ranked, metric, "country", "", charts.BLUE, label, height=max(360, 30 * top_n + 120)), width="stretch")

# ---------- Comparison ----------
ui.section("Compare countries", "Pick any countries to see how their curves differ.")
default = list(snap.nlargest(5, "confirmed")["country"])
chosen = st.multiselect("Countries", sorted(countries_df["country"].unique()), default=default)
c1, c2, c3 = st.columns(3)
with c1:
    view = st.radio("Measure", ["Cumulative confirmed", "Cumulative deaths", "New cases (7-day average)", "New deaths (7-day average)"])
with c2:
    per_capita = st.checkbox("Per 100,000 people", help="Divides by population so countries of different size can be compared.")
with c3:
    log_y = st.checkbox("Logarithmic scale")

col = {"Cumulative confirmed": "confirmed", "Cumulative deaths": "deaths", "New cases (7-day average)": "new_confirmed", "New deaths (7-day average)": "new_deaths"}[view]
if not chosen:
    st.info("Select at least one country.")
else:
    d = countries_df[countries_df["country"].isin(chosen)].sort_values(["country", "date"]).copy()
    if "7-day" in view:
        d[col] = d.groupby("country")[col].transform(lambda s: s.rolling(7, min_periods=7).mean())
    if per_capita:
        d = d[d["population"] > 0]
        d[col] = d[col] / d["population"] * 100_000
        missing = set(chosen) - set(d["country"])
        if missing:
            st.warning("No population data for: " + ", ".join(sorted(missing)))
    suffix = " per 100,000" if per_capita else ""
    if d.empty:
        st.info("Nothing to plot for this selection.")
    else:
        st.plotly_chart(charts.multi_country_lines(d, col, f"{view}{suffix}", view + suffix, log_y=log_y), width="stretch")

    # Side-by-side table (latest chosen date)
    tbl = snap[snap["country"].isin(chosen)][["country", "who_region", "confirmed", "deaths", "death_rate", "confirmed_per_100k", "deaths_per_100k"]]
    tbl = tbl.rename(columns={"country": "Country", "who_region": "WHO region", "confirmed": "Confirmed", "deaths": "Deaths", "death_rate": "Death rate %",
                              "confirmed_per_100k": "Cases / 100k", "deaths_per_100k": "Deaths / 100k"})
    st.dataframe(tbl.sort_values("Confirmed", ascending=False), hide_index=True, width="stretch",
                 column_config={"Confirmed": st.column_config.NumberColumn(format="%d"), "Deaths": st.column_config.NumberColumn(format="%d"),
                                "Death rate %": st.column_config.NumberColumn(format="%.2f"), "Cases / 100k": st.column_config.NumberColumn(format="%.0f"),
                                "Deaths / 100k": st.column_config.NumberColumn(format="%.1f")})

# ---------- Scatter ----------
ui.section("Confirmed cases vs deaths", "Each dot is a country. Points above the general pattern have a higher reported death rate.")
st.plotly_chart(charts.scatter_log(snap, ""), width="stretch")
