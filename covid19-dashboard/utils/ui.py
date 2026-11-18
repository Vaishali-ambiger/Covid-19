"""Shared layout helpers: page set-up, styling, KPI cards and data loading with friendly errors."""
import pandas as pd
import streamlit as st

from utils.data_loader import DataNotFoundError, load_data

CSS = """
<style>
.block-container {padding-top: 4rem; padding-bottom: 3rem; max-width: 1280px;}
html, body, [class*="css"] {font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;}
h1, h2, h3 {color: #0B3A6F; letter-spacing: -0.01em;}
#MainMenu, footer {visibility: hidden;}
[data-testid="stSidebar"] {background: #FFFFFF; border-right: 1px solid #E3EBF3;}
.page-title {font-size: 2rem; font-weight: 700; color: #0B3A6F; margin: 0;}
.page-sub {color: #4F6B85; margin: 4px 0 18px 0; font-size: 1rem;}
.banner {background: #FFFFFF; border: 1px solid #E3EBF3; border-left: 5px solid #2AB7A9; border-radius: 12px; padding: 12px 16px; font-size: 0.9rem; color: #31506B; margin-bottom: 18px;}
.kpi {background: #FFFFFF; border: 1px solid #E3EBF3; border-top: 4px solid var(--accent); border-radius: 14px; padding: 16px 18px; box-shadow: 0 6px 18px -12px rgba(11,58,111,.35); min-height: 235px;}
.kpi-label {font-size: .78rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #5B7083;}
.kpi-value {font-size: 1.9rem; font-weight: 700; color: #0B3A6F; line-height: 1.25; margin: 4px 0;}
.kpi-sub {font-size: .8rem; color: #5B7083; line-height: 1.35;}
.tag {display: inline-block; font-size: .65rem; font-weight: 700; padding: 1px 8px; border-radius: 999px; margin-left: 6px; vertical-align: middle;}
.tag-actual {background: #D6E6F8; color: #0B3A6F;}
.tag-derived {background: #CFEFEA; color: #0D6B61;}
.note {background: #EEF5FC; border-radius: 10px; padding: 10px 14px; font-size: .88rem; color: #31506B; margin: 6px 0 14px 0;}
.section-title {font-size: 1.25rem; font-weight: 700; color: #0B3A6F; margin: 26px 0 2px 0;}
.section-desc {color: #5B7083; font-size: .92rem; margin-bottom: 10px;}
</style>
"""


def setup(title: str = "", icon: str = "") -> None:
    """Applies the shared styling. (Page title, icon and layout are set once in app.py.)"""
    st.markdown(CSS, unsafe_allow_html=True)


def get_data() -> tuple[pd.DataFrame, dict]:
    """Loads data; shows a clear message and stops the page if files are missing."""
    try:
        data = load_data()
    except DataNotFoundError as err:
        st.error("The dataset could not be loaded.")
        st.code(str(err))
        st.stop()
    except Exception as err:  # unexpected problem: show it rather than a blank page
        st.error(f"Unexpected error while loading data: {err}")
        st.stop()
    return data["df"], data["meta"]


def page_header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="page-title">{title}</div><div class="page-sub">{subtitle}</div>', unsafe_allow_html=True)


def section(title: str, desc: str = "") -> None:
    st.markdown(f'<div class="section-title">{title}</div><div class="section-desc">{desc}</div>', unsafe_allow_html=True)


def note(text: str) -> None:
    st.markdown(f'<div class="note">{text}</div>', unsafe_allow_html=True)


def data_banner(meta: dict) -> None:
    st.markdown(
        f'<div class="banner"><b>Source:</b> {meta["source"]}. <b>Coverage:</b> {meta["date_min"]:%d %b %Y} to {meta["date_max"]:%d %b %Y} '
        f'({meta["n_countries"]} countries/regions). The source stopped updating after the last date shown.</div>',
        unsafe_allow_html=True,
    )


def kpi(label: str, value: str, sub: str, kind: str, accent: str = "#1D6FDB") -> None:
    """kind is 'actual' (reported number) or 'derived' (calculated by this project)."""
    tag = "ACTUAL" if kind == "actual" else "DERIVED"
    st.markdown(
        f'<div class="kpi" style="--accent:{accent}"><div class="kpi-label">{label}<span class="tag tag-{kind}">{tag}</span></div>'
        f'<div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def big(n: float) -> str:
    """12,345,678 -> '12.35M' for compact cards."""
    if pd.isna(n):
        return "n/a"
    for unit, size in (("B", 1e9), ("M", 1e6), ("K", 1e4)):
        if abs(n) >= size:
            return f"{n / size:,.2f}{unit}"
    return f"{n:,.0f}"


def sidebar_info(meta: dict) -> None:
    with st.sidebar:
        st.markdown("---")
        st.caption(f"Data: JHU CSSE, {meta['date_min']:%b %Y} to {meta['date_max']:%b %Y}. Use the page list above to navigate.")
