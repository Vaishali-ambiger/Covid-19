"""Global Overview page (opened first by app.py)."""
import streamlit as st

from utils import charts, metrics, ui

ui.setup("Global Overview", "🌍")
df, meta = ui.get_data()
ui.sidebar_info(meta)

ui.page_header("COVID-19 Global Data Analysis Dashboard", "Worldwide cases, deaths and recoveries across countries and WHO regions.")
ui.data_banner(meta)

k = metrics.global_kpis(df, meta)

# ---------- A. KPI cards ----------
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    ui.kpi("Confirmed cases", ui.big(k["confirmed"]), f"{k['confirmed']:,.0f} as of {k['date']:%d %b %Y}", "actual", charts.BLUE)
with c2:
    ui.kpi("Deaths", ui.big(k["deaths"]), f"{k['deaths']:,.0f} as of {k['date']:%d %b %Y}", "actual", charts.NAVY)
with c3:
    ui.kpi("Global death rate", f"{k['death_rate']:.2f}%", "Deaths ÷ confirmed cases (reported ratio, not true mortality)", "derived", "#5AA2EA")
with c4:
    if "recovered" in k:
        ui.kpi("Recovered", ui.big(k["recovered"]), f"As of {k['recovered_date']:%d %b %Y}, the last date recoveries were published. "
               f"{k['recovered_countries']} reporting countries, covering {k['coverage_confirmed_share']:.0f}% of confirmed cases. "
               f"Not included: {', '.join(k['excluded_top'])}.", "actual", charts.TEAL)
    else:
        ui.kpi("Recovered", "n/a", "Not available in this dataset", "actual", charts.TEAL)
with c5:
    if "active" in k:
        ui.kpi("Active cases", ui.big(k["active"]), f"As of {k['recovered_date']:%d %b %Y}. Confirmed − deaths − recovered, for reporting countries only.", "derived", charts.SOFT_TEAL)
    else:
        ui.kpi("Active cases", "n/a", "Cannot be calculated reliably", "derived", charts.SOFT_TEAL)

ui.note("<b>Why recovered and active cases show an older date:</b> the data source stopped publishing recoveries in August 2021, and some countries, including the United States, "
        "did not report them through August 2021. To avoid misleading totals, those figures are shown only where the data is real.")

# ---------- Region split and top 10 ----------
snap = metrics.snapshot(df, meta["date_max"])
snap = snap[snap["who_region"] != metrics.NON_COUNTRY]
reg = metrics.region_summary(df, meta)

left, right = st.columns(2)
with left:
    ui.section("Share of confirmed cases by WHO region")
    st.plotly_chart(charts.donut(reg["who_region"], reg["confirmed"], ""), width="stretch")
with right:
    ui.section("Top 10 countries by confirmed cases")
    top10 = snap.nlargest(10, "confirmed")
    st.plotly_chart(charts.bar_ranking(top10, "confirmed", "country", "", charts.BLUE, "Confirmed cases"), width="stretch")

# ---------- Global trend ----------
ts = metrics.aggregate_by_date(df[df["who_region"] != metrics.NON_COUNTRY])
ui.section("Global trend (7-day average of daily new values)", "Daily values are calculated from differences in the cumulative totals.")
a, b = st.columns(2)
with a:
    st.plotly_chart(charts.line_chart(ts, "date", {"New confirmed cases": "new_confirmed_7d"}, "New confirmed cases per day", height=340), width="stretch")
with b:
    st.plotly_chart(charts.line_chart(ts, "date", {"New deaths": "new_deaths_7d"}, "New deaths per day", height=340), width="stretch")

# ---------- Insights ----------
ui.section("Key insights", "Calculated live from the data shown above.")
for text in metrics.generate_insights(df, meta):
    st.markdown(f"- {text}")

with st.expander("How to read this dashboard: actual vs derived values"):
    st.markdown(
        "- **ACTUAL**: numbers reported by the data source (confirmed, deaths, recovered).\n"
        "- **DERIVED**: numbers calculated here (death rate, active cases, daily new values, 7-day averages, per-100,000 values).\n"
        "- Missing values are left empty. They are never estimated or filled in.\n"
        "- Open the **Data Quality & About** page for the full cleaning log and limitations."
    )
