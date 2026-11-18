"""
Entry point. Run with:   python -m streamlit run app.py

This file sets the page title/layout once and builds the sidebar navigation.
Each page lives in the pages/ folder.
"""
import streamlit as st

st.set_page_config(page_title="COVID-19 Global Data Analysis Dashboard", page_icon="🦠", layout="wide", initial_sidebar_state="expanded")

from utils import ui  # noqa: E402  (imported after set_page_config on purpose)

ui.setup()

navigation = st.navigation(
    [
        st.Page("pages/0_Global_Overview.py", title="Global Overview", icon="🌍", default=True),
        st.Page("pages/1_Country_Analysis.py", title="Country Analysis", icon="🌐"),
        st.Page("pages/2_WHO_Region_Analysis.py", title="WHO Region Analysis", icon="🧭"),
        st.Page("pages/3_Time_Series_Analysis.py", title="Time-Series Analysis", icon="📈"),
        st.Page("pages/4_Maps_and_Heatmaps.py", title="Maps and Heatmaps", icon="🗺️"),
        st.Page("pages/5_Statistical_View.py", title="Statistical View", icon="📊"),
        st.Page("pages/6_Data_Quality_and_About.py", title="Data Quality and About", icon="🧪"),
    ]
)
navigation.run()
