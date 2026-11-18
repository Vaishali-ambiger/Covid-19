"""Statistical view using Seaborn and Matplotlib."""
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import streamlit as st

from utils import metrics, ui

ui.setup("Statistical View", "📊")
df, meta = ui.get_data()
ui.sidebar_info(meta)
ui.page_header("Statistical View", "Distributions and relationships across countries (Seaborn / Matplotlib).")

base = df[df["who_region"] != metrics.NON_COUNTRY]
snap = metrics.snapshot(base, meta["date_max"])
sns.set_theme(style="whitegrid", rc={"axes.edgecolor": "#C9D6E3", "grid.color": "#E3EBF3"})
PALETTE = ["#0B3A6F", "#1D6FDB", "#5AA2EA", "#2AB7A9", "#7FD1C6", "#A9C6E8"]

min_cases = st.sidebar.slider("Minimum confirmed cases for rate comparisons", 1_000, 500_000, 10_000, step=1_000)
rated = snap[snap["confirmed"] >= min_cases]

ui.section("Death rate distribution by WHO region", f"Countries with at least {min_cases:,} confirmed cases ({len(rated)} countries). Each dot is one country.")
fig, ax = plt.subplots(figsize=(10, 4.6))
order = rated.groupby("who_region", observed=True)["death_rate"].median().sort_values(ascending=False).index
sns.boxplot(data=rated, x="death_rate", y="who_region", order=order, color="#D6E6F8", fliersize=0, ax=ax)
sns.stripplot(data=rated, x="death_rate", y="who_region", order=order, palette=PALETTE[: len(order)], hue="who_region", legend=False, size=5, alpha=0.8, ax=ax)
ax.set_xlabel("Reported death rate (% of confirmed cases)")
ax.set_ylabel("")
st.pyplot(fig)
plt.close(fig)

ui.section("How confirmed cases per capita are distributed", "Countries above 1 million population. Log scale because values span several orders of magnitude.")
pc = snap[(snap["population"] > 1_000_000) & (snap["confirmed_per_100k"] > 0)]
fig, ax = plt.subplots(figsize=(10, 4))
sns.histplot(np.log10(pc["confirmed_per_100k"]), bins=25, color="#1D6FDB", edgecolor="white", ax=ax)
ax.set_xlabel("log10 of confirmed cases per 100,000 people")
ax.set_ylabel("Number of countries")
st.pyplot(fig)
plt.close(fig)

ui.section("Correlation between indicators", "Spearman rank correlation across countries (population above 1 million). Descriptive only: correlation does not show cause.")
corr_data = snap[(snap["population"] > 1_000_000) & (snap["confirmed"] > 0) & (snap["deaths"] > 0)][["population", "confirmed_per_100k", "deaths_per_100k", "death_rate"]].dropna()
corr_data.columns = ["Population", "Cases / 100k", "Deaths / 100k", "Death rate %"]
fig, ax = plt.subplots(figsize=(6.5, 4.6))
sns.heatmap(corr_data.corr(method="spearman"), annot=True, fmt=".2f", cmap=sns.light_palette("#1D6FDB", as_cmap=True), vmin=-1, vmax=1, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
ax.set_xlabel("")
ax.set_ylabel("")
st.pyplot(fig)
plt.close(fig)
st.caption(f"Based on {len(corr_data)} countries.")
