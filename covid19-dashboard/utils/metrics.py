"""Calculations used by the dashboard pages. Every function documents whether values are ACTUAL (reported) or DERIVED."""
import numpy as np
import pandas as pd

NON_COUNTRY = "Unassigned"  # cruise ships, event entries, Antarctica


def snapshot(df: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
    """One row per country on a given date.
    ACTUAL: confirmed, deaths, recovered.  DERIVED: active, death_rate, per-100k values."""
    s = df[df["date"] == date].copy()
    s["who_region"] = s["who_region"].astype(str)  # plain text avoids unused-category side effects
    s["death_rate"] = np.where(s["confirmed"] > 0, s["deaths"] / s["confirmed"] * 100, np.nan)
    pop = s["population"].where(s["population"] > 0)
    s["confirmed_per_100k"] = s["confirmed"] / pop * 100_000
    s["deaths_per_100k"] = s["deaths"] / pop * 100_000
    return s.reset_index(drop=True)


def global_kpis(df: pd.DataFrame, meta: dict) -> dict:
    """Global headline numbers.
    - confirmed / deaths: ACTUAL, latest date, all entries in the source.
    - death_rate: DERIVED = deaths / confirmed.
    - recovered: ACTUAL but only for countries that reported it, as of the last date recovered was published.
    - active: DERIVED (confirmed - deaths - recovered) for those same countries."""
    last = meta["date_max"]
    cut = meta["recovered_cutoff"]
    latest = df[df["date"] == last]
    out = {
        "date": last,
        "confirmed": float(latest["confirmed"].sum()),
        "deaths": float(latest["deaths"].sum()),
        "recovered_date": cut,
    }
    out["death_rate"] = out["deaths"] / out["confirmed"] * 100 if out["confirmed"] else np.nan

    if pd.notna(cut):
        c = df[(df["date"] == cut)]
        rep = c[c["recovered_reported"]]
        out["recovered"] = float(rep["recovered"].sum())
        act = rep["active"].dropna()
        out["active"] = float(act.sum())
        out["active_countries"] = int(act.shape[0])
        out["recovered_countries"] = int(rep.shape[0])
        out["coverage_confirmed_share"] = float(rep["confirmed"].sum() / c["confirmed"].sum() * 100)
        # Largest countries that are NOT included (by confirmed cases at the cut-off)
        left_out = c[~c["recovered_reported"] & (c["who_region"] != NON_COUNTRY)].nlargest(3, "confirmed")
        out["excluded_top"] = [n for n, v in zip(left_out["country"], left_out["confirmed"]) if v > 0]
    return out


def region_summary(df: pd.DataFrame, meta: dict) -> pd.DataFrame:
    """Totals by WHO region (excludes 'Unassigned').
    confirmed/deaths at the latest date; recovered at the recovered cut-off date (reporting countries only)."""
    last, cut = meta["date_max"], meta["recovered_cutoff"]
    latest = df[(df["date"] == last) & (df["who_region"] != NON_COUNTRY)]
    reg = latest.groupby("who_region", observed=True).agg(confirmed=("confirmed", "sum"), deaths=("deaths", "sum"), countries=("country", "nunique"))
    reg["death_rate"] = reg["deaths"] / reg["confirmed"] * 100
    reg["share_of_confirmed"] = reg["confirmed"] / reg["confirmed"].sum() * 100

    if pd.notna(cut):
        c = df[(df["date"] == cut) & (df["who_region"] != NON_COUNTRY)]
        rep = c[c["recovered_reported"]]
        r = rep.groupby("who_region", observed=True).agg(recovered=("recovered", "sum"), recovered_countries=("country", "nunique"), confirmed_reporting=("confirmed", "sum"))
        reg = reg.join(r)
        reg["recovery_rate_reporting"] = reg["recovered"] / reg["confirmed_reporting"] * 100
    return reg.reset_index().sort_values("confirmed", ascending=False)


def filter_scope(df: pd.DataFrame, scope: str, selection) -> pd.DataFrame:
    """scope: 'Global', 'WHO region' or 'Country'. selection: region name or list of countries."""
    if scope == "WHO region":
        return df[df["who_region"] == selection]
    if scope == "Country":
        return df[df["country"].isin(selection)]
    return df


def aggregate_by_date(d: pd.DataFrame) -> pd.DataFrame:
    """Sum countries per date. Recovered columns stay empty (NaN) where nobody reported (min_count=1)."""
    g = d.groupby("date")
    out = g[["confirmed", "deaths", "new_confirmed", "new_deaths"]].sum()
    out["recovered"] = g["recovered"].sum(min_count=1)
    out["new_recovered"] = g["new_recovered"].sum(min_count=1)
    out["active"] = g["active"].sum(min_count=1)
    out = out.reset_index()
    for col in ("new_confirmed", "new_deaths", "new_recovered"):
        out[f"{col}_7d"] = out[col].rolling(7, min_periods=7).mean()  # DERIVED: 7-day moving average
    return out


def to_monthly(ts: pd.DataFrame) -> pd.DataFrame:
    """Monthly totals of new values (sum) and month-end cumulative values (last)."""
    t = ts.set_index("date")
    m = t[["new_confirmed", "new_deaths"]].resample("MS").sum()
    m["new_recovered"] = t["new_recovered"].resample("MS").sum(min_count=1)
    for col in ("confirmed", "deaths", "recovered"):
        m[f"{col}_cum"] = t[col].resample("MS").last()
    return m.reset_index()


def monthly_heatmap_data(df: pd.DataFrame, countries: list[str], value: str = "new_confirmed") -> pd.DataFrame:
    """Country x month matrix of monthly totals (DERIVED from daily differences)."""
    d = df[df["country"].isin(countries)].copy()
    d["month"] = d["date"].dt.to_period("M").dt.to_timestamp()
    pv = d.pivot_table(index="country", columns="month", values=value, aggfunc="sum")
    return pv.loc[[c for c in countries if c in pv.index]]


def generate_insights(df: pd.DataFrame, meta: dict) -> list[str]:
    """Plain-language findings calculated directly from the data (nothing hard-coded)."""
    last = meta["date_max"]
    snap = snapshot(df, last)
    snap = snap[snap["who_region"] != NON_COUNTRY]
    total_c, total_d = snap["confirmed"].sum(), snap["deaths"].sum()
    top = snap.nlargest(1, "confirmed").iloc[0]
    top5 = snap.nlargest(5, "confirmed")
    reg = region_summary(df, meta)
    ts = aggregate_by_date(df[df["who_region"] != NON_COUNTRY])
    peak_c = ts.loc[ts["new_confirmed_7d"].idxmax()]
    peak_d = ts.loc[ts["new_deaths_7d"].idxmax()]
    big = snap[snap["confirmed"] >= 100_000]
    hi_cfr, lo_cfr = big.nlargest(1, "death_rate").iloc[0], big.nsmallest(1, "death_rate").iloc[0]
    pc = snap[snap["population"] > 1_000_000].nlargest(1, "confirmed_per_100k").iloc[0]
    r_top = reg.iloc[0]
    r_dr = reg.sort_values("death_rate", ascending=False).iloc[0]
    items = [
        f"**{top['country']}** reported the most confirmed cases ({top['confirmed']:,.0f}), and the top five countries together account for "
        f"{top5['confirmed'].sum() / total_c * 100:.1f}% of all confirmed cases.",
        f"By WHO region, **{r_top['who_region']}** has the largest share of confirmed cases ({r_top['share_of_confirmed']:.1f}%). "
        f"**{r_dr['who_region']}** has the highest reported death rate ({r_dr['death_rate']:.2f}% of confirmed cases).",
        f"The highest 7-day average of new confirmed cases was about **{peak_c['new_confirmed_7d']:,.0f} per day**, around {peak_c['date']:%d %b %Y}. "
        f"The deaths peak (7-day average) was about **{peak_d['new_deaths_7d']:,.0f} per day**, around {peak_d['date']:%d %b %Y}.",
        f"Among countries with at least 100,000 confirmed cases, the reported death rate ranges from {lo_cfr['death_rate']:.2f}% ({lo_cfr['country']}) "
        f"to {hi_cfr['death_rate']:.2f}% ({hi_cfr['country']}). Differences partly reflect testing and reporting practices, not only disease severity.",
        f"Relative to population, **{pc['country']}** had the highest confirmed cases per 100,000 people among countries above 1 million population "
        f"({pc['confirmed_per_100k']:,.0f}).",
    ]
    return items
