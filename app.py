from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Home Credit risk analytics",
    page_icon=":material/analytics:",
    layout="wide",
)
st.logo(str(Path(__file__).parent / "utils" / "home_credit_logo.svg"), size="large")


pages = {
    "Portfolio": [
        st.Page(
            "app_pages/overview.py",
            title="Executive overview",
            icon=":material/dashboard:",
            help="Portfolio KPIs, application outcomes, loan amounts, and default rates.",
        ),
        st.Page(
            "app_pages/customer_demographics.py",
            title="Customer demographics",
            icon=":material/groups:",
            help="Explore applicant demographics and how observed outcomes vary by group.",
        ),
        st.Page(
            "app_pages/loan_analysis.py",
            title="Loan application analysis",
            icon=":material/layers:",
            help="Analyze loan amounts, contract types, and key application ratios.",
        ),
        st.Page(
            "app_pages/default_risk.py",
            title="Default risk analysis",
            icon=":material/warning:",
            help="Review historical default rates across application attributes and external scores.",
        ),
    ],
    "Data": [
        st.Page(
            "app_pages/data_explorer.py",
            title="Data explorer",
            icon=":material/database:",
            help="Preview source tables and search the official Home Credit column descriptions.",
        ),
    ],
}
page = st.navigation(pages, position="sidebar")

page.run()
