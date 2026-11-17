import pandas as pd
import streamlit as st

from utils.data import filtered_applications, render_application_filters


st.title("Home Credit | Executive overview", icon=":material/dashboard:")
st.caption("Portfolio indicators and application outcomes from the training dataset.")

filters = render_application_filters("overview")
df = filtered_applications(filters)
if df.empty:
    st.warning("No applications match these filters. Adjust the selections above.")
    st.stop()

total = len(df)
defaults = int(df["TARGET"].sum())
non_defaults = total - defaults
default_rate = defaults / total
average_credit = df["AMT_CREDIT"].mean()
average_income = df["AMT_INCOME_TOTAL"].mean()

st.html(
    """
    <style>
    .st-key-kpi-applications { background: #e8f4fd; border: 1px solid #d4e7f5; border-radius: 0.75rem; padding: 0.6rem 0.9rem; }
    .st-key-kpi-applications * { color: #19324f !important; }
    .st-key-kpi-defaults { background: #fdecec; border: 1px solid #f3d5d5; border-radius: 0.75rem; padding: 0.6rem 0.9rem; }
    .st-key-kpi-defaults * { color: #782f32 !important; }
    .st-key-kpi-default-rate { background: #fff4d8; border: 1px solid #f0e2b9; border-radius: 0.75rem; padding: 0.6rem 0.9rem; }
    .st-key-kpi-default-rate * { color: #765314 !important; }
    .st-key-kpi-non-defaults { background: #e8f6ed; border: 1px solid #d2e8d9; border-radius: 0.75rem; padding: 0.6rem 0.9rem; }
    .st-key-kpi-non-defaults * { color: #24583a !important; }
    .st-key-kpi-average-credit { background: #e4f6f7; border: 1px solid #cfe9eb; border-radius: 0.75rem; padding: 0.6rem 0.9rem; }
    .st-key-kpi-average-credit * { color: #14566a !important; }
    .st-key-kpi-average-income { background: #f0edff; border: 1px solid #dfd9f4; border-radius: 0.75rem; padding: 0.6rem 0.9rem; }
    .st-key-kpi-average-income * { color: #493878 !important; }
    </style>
    """
)

first_row = st.columns(3)
with first_row[0].container(key="kpi-applications"):
    st.metric("Applications", f"{total:,}", icon=":material/description:")
with first_row[1].container(key="kpi-defaults"):
    st.metric("Defaults", f"{defaults:,}", icon=":material/warning:")
with first_row[2].container(key="kpi-default-rate"):
    st.metric("Default rate", f"{default_rate:.2%}", icon=":material/percent:")

second_row = st.columns(3)
with second_row[0].container(key="kpi-non-defaults"):
    st.metric("Non-defaults", f"{non_defaults:,}", icon=":material/check_circle:")
with second_row[1].container(key="kpi-average-credit"):
    st.metric(
        "Average credit",
        f"{average_credit:,.0f}",
        icon=":material/account_balance_wallet:",
    )
with second_row[2].container(key="kpi-average-income"):
    st.metric("Average income", f"{average_income:,.0f}", icon=":material/payments:")

pie_col, outcome_col, credit_col = st.columns(3)
with pie_col:
    st.subheader("Default vs. non-default")
    pie_data = [
        {
            "name": f"Non-default: {non_defaults:,} ({non_defaults / total:.2%})",
            "value": non_defaults,
        },
        {
            "name": f"Default: {defaults:,} ({default_rate:.2%})",
            "value": defaults,
        },
    ]
    st.echarts_chart(
        {
            "color": ["#16A6A1", "#F5A623"],
            "tooltip": {"trigger": "item"},
            "legend": {
                "orient": "horizontal",
                "left": "center",
                "bottom": 0,
            },
            "graphic": [
                {
                    "type": "text",
                    "left": "center",
                    "top": "middle",
                    "style": {
                        "text": f"{total:,}\nApplications",
                        "textAlign": "center",
                        "textVerticalAlign": "middle",
                        "fontSize": 16,
                        "fontWeight": "bold",
                        "fill": "#14233C",
                    },
                }
            ],
            "series": [
                {
                    "type": "pie",
                    "radius": ["38%", "56%"],
                    "center": ["50%", "50%"],
                    "data": pie_data,
                    "label": {
                        "show": True,
                        "position": "outside",
                        "formatter": "{c} ({d}%)",
                        "fontSize": 10,
                    },
                    "labelLine": {
                        "show": True,
                        "length": 6,
                        "length2": 4,
                    },
                }
            ],
        },
        alt="Share of applications with and without recorded payment difficulties",
    )

with outcome_col:
    st.subheader("Application outcome")
    st.echarts_chart(
        {
            "tooltip": {"trigger": "axis", "valueFormatter": "localized"},
            "xAxis": {
                "type": "category",
                "data": ["Non-default", "Default"],
            },
            "yAxis": {
                "type": "value",
                "name": "Applications",
            },
            "series": [
                {
                    "type": "bar",
                    "data": [
                        {
                            "value": non_defaults,
                            "itemStyle": {"color": "#16A6A1"},
                        },
                        {
                            "value": defaults,
                            "itemStyle": {"color": "#F5A623"},
                        },
                    ],
                    "label": {
                        "show": True,
                        "position": "top",
                        "formatter": "{c}",
                    },
                }
            ],
        },
        alt="Counts of non-default and default applications",
    )

with credit_col:
    st.subheader("Loan amount distribution")
    credit = df["AMT_CREDIT"].dropna()
    if not credit.empty:
        bins = pd.cut(credit, bins=20)
        distribution = (
            bins.value_counts(sort=False)
            .rename_axis("Credit range")
            .reset_index(name="Applications")
        )
        distribution["Credit range"] = distribution["Credit range"].astype(str)
        st.bar_chart(
            distribution,
            x="Credit range",
            y="Applications",
            alt="Application counts across loan amount ranges",
        )
    else:
        st.info("No credit amounts are available for this filter.")

income_col, contract_col = st.columns(2)
with income_col:
    st.subheader("Income vs. credit amount")
    points = df[["AMT_INCOME_TOTAL", "AMT_CREDIT", "TARGET"]].dropna()
    if not points.empty:
        plot_columns = ["AMT_INCOME_TOTAL", "AMT_CREDIT"]
        non_defaults = (
            points.loc[points["TARGET"].eq(0), plot_columns].reset_index(drop=True)
        )
        defaults = (
            points.loc[points["TARGET"].eq(1), plot_columns].reset_index(drop=True)
        )
        st.echarts_chart(
            {
                "legend": {},
                "dataset": [
                    {"source": non_defaults},
                    {"source": defaults},
                ],
                "xAxis": {
                    "type": "value",
                    "name": "Annual income",
                    "nameLocation": "middle",
                },
                "yAxis": {
                    "type": "value",
                    "name": "Credit amount",
                    "nameLocation": "middle",
                },
                "series": [
                    {
                        "type": "scatter",
                        "name": "Non-default",
                        "datasetIndex": 0,
                        "encode": {
                            "x": "AMT_INCOME_TOTAL",
                            "y": "AMT_CREDIT",
                        },
                        "large": True,
                        "symbolSize": 4,
                    },
                    {
                        "type": "scatter",
                        "name": "Default",
                        "datasetIndex": 1,
                        "encode": {
                            "x": "AMT_INCOME_TOTAL",
                            "y": "AMT_CREDIT",
                        },
                        "large": True,
                        "symbolSize": 4,
                    }
                ],
            },
            alt="Applications colored by payment outcome, comparing annual income with requested credit",
        )
    else:
        st.info("No complete income and credit amount pairs are available.")

with contract_col:
    st.subheader("Default rate by contract type")
    by_contract = (
        df.groupby("NAME_CONTRACT_TYPE", observed=True)["TARGET"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(
            columns={
                "NAME_CONTRACT_TYPE": "Contract type",
                "mean": "Default rate",
                "count": "Applications",
            }
        )
    )
    by_contract["Default rate"] *= 100
    contract_colors = {
        "Cash loans": "#16A6A1",
        "Revolving loans": "#F5A623",
    }
    contract_types = by_contract["Contract type"].astype(str).tolist()
    st.echarts_chart(
        {
            "tooltip": {"trigger": "axis", "formatter": "{b}: {c}%"},
            "xAxis": {
                "type": "category",
                "data": contract_types,
            },
            "yAxis": {
                "type": "value",
                "name": "Default rate (%)",
            },
            "series": [
                {
                    "type": "bar",
                    "data": [
                        {
                            "value": float(row["Default rate"]),
                            "itemStyle": {
                                "color": contract_colors.get(
                                    str(row["Contract type"]), "#16A6A1"
                                )
                            },
                            "label": {
                                "show": True,
                                "position": "top",
                                "formatter": f"{row['Default rate']:.2f}%",
                            },
                        }
                        for _, row in by_contract.iterrows()
                    ],
                }
            ],
        },
        alt="Historical default rate for each contract type",
    )

st.subheader("Sample application data", icon=":material/table_chart:")
sample_columns = [
    "SK_ID_CURR",
    "TARGET",
    "NAME_CONTRACT_TYPE",
    "AMT_CREDIT",
    "AMT_INCOME_TOTAL",
    "AMT_ANNUITY",
    "AGE_YEARS",
]
rows_per_page = 10
total_pages = max(1, (len(df) + rows_per_page - 1) // rows_per_page)
page_number = st.session_state.get("sample_data_page", 1)
if page_number > total_pages:
    page_number = 1
    st.session_state["sample_data_page"] = 1

start_index = (page_number - 1) * rows_per_page
end_index = start_index + rows_per_page
st.dataframe(
    df[sample_columns].iloc[start_index:end_index],
    column_config={
        "SK_ID_CURR": st.column_config.NumberColumn(alignment="center"),
        "TARGET": st.column_config.NumberColumn(alignment="center"),
        "NAME_CONTRACT_TYPE": st.column_config.TextColumn(alignment="center"),
        "AMT_CREDIT": st.column_config.NumberColumn(alignment="center"),
        "AMT_INCOME_TOTAL": st.column_config.NumberColumn(alignment="center"),
        "AMT_ANNUITY": st.column_config.NumberColumn(alignment="center"),
        "AGE_YEARS": st.column_config.NumberColumn(alignment="center"),
    },
    hide_index=True,
    alt="Applications matching the active filters on the selected page",
)
_, summary_col = st.columns([3, 1])
with summary_col:
    st.markdown(
        f"Showing {start_index + 1:,}–{min(end_index, len(df)):,} of {len(df):,} records.",
        text_alignment="right",
    )
with st.container(horizontal=True, horizontal_alignment="right"):
    st.pagination(
        total_pages,
        max_visible_pages=5,
        key="sample_data_page",
        width="content",
    )
