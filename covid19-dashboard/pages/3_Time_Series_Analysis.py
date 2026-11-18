"""Time-series analysis with interactive date filters."""
import pandas as pd
import streamlit as st

from utils import charts, metrics, ui

ui.setup("Time-Series Analysis", "📈")
df, meta = ui.get_data()
ui.sidebar_info(meta)
ui.page_header("Time-Series Analysis", "Daily and monthly trends for cases, deaths and recoveries.")

base = df[df["who_region"] != metrics.NON_COUNTRY]
cut = meta["recovered_cutoff"]

with st.sidebar:
    st.subheader("Filters")
    scope = st.radio("Scope", ["Global", "WHO region", "Country"])
    selection = None
    if scope == "WHO region":
        selection = st.selectbox("WHO region", sorted(base["who_region"].unique()))
    elif scope == "Country":
        selection = st.multiselect("Countries (totals are summed)", sorted(base["country"].unique()), default=["India"])
        if not selection:
            st.info("Select at least one country in the sidebar.")
            st.stop()
    d0, d1 = st.slider("Date range", meta["date_min"].date(), meta["date_max"].date(), (meta["date_min"].date(), meta["date_max"].date()))
    granularity = st.radio("Granularity", ["Daily", "Monthly"], horizontal=True)
    mode = st.radio("Show", ["New per period", "Cumulative"], horizontal=True)
    smooth = st.checkbox("7-day average (daily only)", value=True)
    log_y = st.checkbox("Logarithmic scale")

subset = metrics.filter_scope(base, scope, selection)
ts = metrics.aggregate_by_date(subset)
ts = ts[(ts["date"] >= pd.Timestamp(d0)) & (ts["date"] <= pd.Timestamp(d1))]
if ts.empty:
    st.warning("No data in this date range.")
    st.stop()

title_scope = "Worldwide" if scope == "Global" else (selection if scope == "WHO region" else ", ".join(selection))
if granularity == "Monthly":
    m = metrics.to_monthly(ts)
    x = "date"
    new_cols = {"confirmed": "new_confirmed", "deaths": "new_deaths", "recovered": "new_recovered"}
    cum_cols = {"confirmed": "confirmed_cum", "deaths": "deaths_cum", "recovered": "recovered_cum"}
    data = m
else:
    x = "date"
    data = ts
    new_cols = {k: (f"new_{k}_7d" if smooth else f"new_{k}") for k in ("confirmed", "deaths", "recovered")}
    cum_cols = {"confirmed": "confirmed", "deaths": "deaths", "recovered": "recovered"}
cols = new_cols if mode == "New per period" else cum_cols
unit = "per month" if granularity == "Monthly" else ("per day (7-day average)" if smooth else "per day")
suffix = f"new {unit}" if mode == "New per period" else "cumulative"

# Summary numbers for the selected range
k1, k2, k3 = st.columns(3)
with k1:
    ui.kpi("New confirmed cases in range", ui.big(ts["new_confirmed"].sum()), f"{d0:%d %b %Y} to {d1:%d %b %Y}", "derived", charts.BLUE)
with k2:
    ui.kpi("New deaths in range", ui.big(ts["new_deaths"].sum()), "Sum of daily differences", "derived", charts.NAVY)
with k3:
    peak = ts.loc[ts["new_confirmed_7d"].idxmax()] if ts["new_confirmed_7d"].notna().any() else None
    ui.kpi("Peak 7-day average (cases)", ui.big(peak["new_confirmed_7d"]) if peak is not None else "n/a", f"Around {peak['date']:%d %b %Y}" if peak is not None else "Range too short", "derived", "#5AA2EA")

if mode == "New per period":
    ui.note("Daily values are differences between consecutive cumulative totals. Small downward corrections in the source are shown as zero, not as negative cases.")

tab1, tab2, tab3 = st.tabs(["Cases", "Deaths", "Recoveries"])
with tab1:
    st.plotly_chart(charts.line_chart(data, x, {"Confirmed": cols["confirmed"]}, f"{title_scope}: confirmed cases, {suffix}", log_y=log_y) if granularity == "Daily"
                    else charts.grouped_bars(data, x, {"Confirmed": cols["confirmed"]}, f"{title_scope}: confirmed cases, {suffix}"), width="stretch")
with tab2:
    st.plotly_chart(charts.line_chart(data, x, {"Deaths": cols["deaths"]}, f"{title_scope}: deaths, {suffix}", log_y=log_y) if granularity == "Daily"
                    else charts.grouped_bars(data, x, {"Deaths": cols["deaths"]}, f"{title_scope}: deaths, {suffix}"), width="stretch")
with tab3:
    rec_col = cols["recovered"]
    in_range = data[data[rec_col].notna()] if rec_col in data else data.iloc[0:0]
    if in_range.empty:
        st.info(f"No recovery data for this selection. The source published recoveries only until {cut:%d %b %Y}, and some countries (for example the United States) stopped reporting them earlier or never did.")
    else:
        ui.note(f"Recoveries are available only until <b>{cut:%d %b %Y}</b> and only for countries that reported them. Later dates are left empty on purpose.")
        st.plotly_chart(charts.line_chart(in_range, x, {"Recovered": rec_col}, f"{title_scope}: recovered, {suffix}", log_y=log_y) if granularity == "Daily"
                        else charts.grouped_bars(in_range, x, {"Recovered": rec_col}, f"{title_scope}: recovered, {suffix}"), width="stretch")
        if mode == "Cumulative" and ts["active"].notna().any():
            st.plotly_chart(charts.line_chart(ts, "date", {"Active (derived)": "active"}, "Active cases (derived: confirmed − deaths − recovered, reporting countries)"), width="stretch")

with st.expander("Show the numbers"):
    st.dataframe(data, hide_index=True, width="stretch")
