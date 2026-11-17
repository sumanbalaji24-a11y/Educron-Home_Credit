import pandas as pd
import streamlit as st

from utils.data import filtered_applications, render_application_filters


CONTRACT_ORDER = ["Cash loans", "Revolving loans"]
INCOME_RANGES = {
    "Under 100K": (None, 100_000),
    "100K-250K": (100_000, 250_000),
    "250K-500K": (250_000, 500_000),
    "500K+": (500_000, None),
}
CREDIT_RANGES = {
    "Under 250K": (None, 250_000),
    "250K-500K": (250_000, 500_000),
    "500K-1M": (500_000, 1_000_000),
    "1M-2M": (1_000_000, 2_000_000),
    "2M+": (2_000_000, None),
}


st.title("Loan Application Analysis", icon=":material/layers:")
st.caption("Analyze loan amounts, contract types, and key ratios for Home Credit applications.")

filters = render_application_filters(
    "loan_analysis",
    [
        ("income_range", "Income range", ["All", *INCOME_RANGES]),
        ("credit_range", "Credit amount range", ["All", *CREDIT_RANGES]),
    ],
    filters_per_row=5,
)
df = filtered_applications(filters)

for column, filter_key, ranges in [
    ("AMT_INCOME_TOTAL", "income_range", INCOME_RANGES),
    ("AMT_CREDIT", "credit_range", CREDIT_RANGES),
]:
    selected_range = filters[filter_key]
    if selected_range != "All":
        lower, upper = ranges[selected_range]
        mask = df[column].notna()
        if lower is not None:
            mask &= df[column].ge(lower)
        if upper is not None:
            mask &= df[column].lt(upper)
        df = df.loc[mask]

if df.empty:
    st.warning("No applications match these filters. Adjust the selections above.")
    st.stop()

st.caption(f"Dataset: application_train.csv | {len(df):,} matching applications")

positive_income = df["AMT_INCOME_TOTAL"].where(df["AMT_INCOME_TOTAL"].gt(0))
loan_to_income = (
    (df["AMT_CREDIT"] / positive_income)
    .replace([float("inf"), -float("inf")], pd.NA)
    .dropna()
)
annuity_to_income = (
    (df["AMT_ANNUITY"] / positive_income)
    .replace([float("inf"), -float("inf")], pd.NA)
    .dropna()
)
total_loan_amount = float(df["AMT_CREDIT"].astype("float64").sum())
average_loan_amount = float(df["AMT_CREDIT"].mean())
median_loan_amount = float(df["AMT_CREDIT"].median())
average_goods_price = float(df["AMT_GOODS_PRICE"].mean())

kpi_specs = [
    (
        "loan-total-amount",
        "Total loan",
        f"{total_loan_amount / 1_000_000_000:.2f}B",
        ":material/account_balance_wallet:",
        "#e8f4fd",
        "#d4e7f5",
        "#19324f",
    ),
    (
        "loan-average-amount",
        "Average loan",
        f"{average_loan_amount / 1_000:.1f}K",
        ":material/bar_chart:",
        "#e8f6ed",
        "#d2e8d9",
        "#24583a",
    ),
    (
        "loan-median-amount",
        "Median loan",
        f"{median_loan_amount / 1_000:.1f}K",
        ":material/track_changes:",
        "#fff1e5",
        "#f2dfca",
        "#805126",
    ),
    (
        "loan-average-lti",
        "Loan-to-income",
        f"{loan_to_income.mean():.2f}" if not loan_to_income.empty else "N/A",
        ":material/percent:",
        "#e8f4fd",
        "#d4e7f5",
        "#19324f",
    ),
    (
        "loan-average-ati",
        "Annuity-to-income",
        f"{annuity_to_income.mean():.2f}" if not annuity_to_income.empty else "N/A",
        ":material/percent:",
        "#f0edff",
        "#dfd9f4",
        "#493878",
    ),
    (
        "loan-cash-share",
        "Cash loan share",
        f"{df['NAME_CONTRACT_TYPE'].eq('Cash loans').mean():.2%}",
        ":material/description:",
        "#e4f6ed",
        "#cfe9da",
        "#24583a",
    ),
    (
        "loan-average-goods",
        "Goods price avg.",
        f"{average_goods_price / 1_000:.1f}K",
        ":material/shopping_cart:",
        "#fff1e5",
        "#f2dfca",
        "#805126",
    ),
]

card_styles = "\n".join(
    f".st-key-{key} {{ background: {background}; border: 1px solid {border}; "
    f"border-radius: 0.75rem; padding: 0.55rem 0.65rem; }}\n"
    f".st-key-{key} * {{ color: {foreground} !important; }}"
    for key, _, _, _, background, border, foreground in kpi_specs
)
st.html(f"<style>{card_styles}</style>")

with st.grid(7, min_column_width=110, gap="small"):
    for key, label, value, icon, *_style in kpi_specs:
        with st.container(key=key, height="stretch"):
            help_text = {
                "loan-total-amount": f"Exact total: {total_loan_amount:,.2f}",
                "loan-average-amount": f"Exact average: {average_loan_amount:,.2f}",
                "loan-median-amount": f"Exact median: {median_loan_amount:,.2f}",
                "loan-average-goods": f"Exact average: {average_goods_price:,.2f}",
            }.get(key)
            st.metric(label, value, icon=icon, help=help_text)

credit_col = df["AMT_CREDIT"].dropna()
loan_histogram = pd.cut(credit_col, bins=20)
credit_counts = loan_histogram.value_counts(sort=False)
credit_distribution = pd.DataFrame(
    {
        "Credit range": [
            f"{interval.left / 1_000_000:.1f}M" for interval in credit_counts.index
        ],
        "Applications": credit_counts.to_numpy(),
    }
)

contract_credit = (
    df.groupby("NAME_CONTRACT_TYPE", observed=True)["AMT_CREDIT"]
    .sum()
    .reindex(CONTRACT_ORDER, fill_value=0)
)
contract_credit_data = pd.DataFrame(
    {
        "Contract type": CONTRACT_ORDER,
        "Total credit (billions)": (
            contract_credit.astype("float64").to_numpy() / 1_000_000_000
        ),
    }
)

distribution_col, contract_credit_col = st.columns([1.2, 1])
with distribution_col.container(border=True):
    st.subheader("Loan amount distribution", icon=":material/bar_chart:")
    st.echarts_chart(
        {
            "tooltip": {"trigger": "axis", "valueFormatter": "localized"},
            "grid": {"left": 52, "right": 18, "top": 54, "bottom": 46},
            "graphic": [
                {
                    "type": "text",
                    "right": 10,
                    "top": 8,
                    "style": {
                        "text": (
                            f"Mean: {credit_col.mean():,.0f}\n"
                            f"Median: {credit_col.median():,.0f}"
                        ),
                        "fontSize": 11,
                        "lineHeight": 18,
                        "fill": "#19324f",
                        "backgroundColor": "#e4f6f7",
                        "padding": [6, 8],
                        "borderRadius": 6,
                    },
                }
            ],
            "dataset": {"source": credit_distribution},
            "xAxis": {
                "type": "category",
                "name": "Loan amount",
                "nameLocation": "middle",
                "nameGap": 28,
                "axisLabel": {"interval": 2},
            },
            "yAxis": {"type": "value", "name": "Applications"},
            "series": [
                {
                    "type": "bar",
                    "encode": {"x": "Credit range", "y": "Applications"},
                    "itemStyle": {"color": "#16A6A1"},
                    "barMaxWidth": 18,
                }
            ],
        },
        height=250,
        alt="Application counts across requested loan amounts",
    )

with contract_credit_col.container(border=True):
    st.subheader("Credit amount by contract type", icon=":material/bar_chart:")
    st.echarts_chart(
        {
            "color": ["#16A6A1", "#F5A623"],
            "tooltip": {"trigger": "axis", "formatter": "{b}: {c}B"},
            "dataset": {"source": contract_credit_data},
            "xAxis": {
                "type": "category",
                "axisLabel": {"rotate": 0},
            },
            "yAxis": {
                "type": "value",
                "name": "Total credit (billions)",
                "axisLabel": {"formatter": "{value}B"},
            },
            "series": [
                {
                    "type": "bar",
                    "encode": {
                        "x": "Contract type",
                        "y": "Total credit (billions)",
                    },
                    "barMaxWidth": 90,
                    "label": {
                        "show": True,
                        "position": "top",
                        "formatter": "{c}B",
                    },
                }
            ],
        },
        height=250,
        alt="Total credit requested by cash and revolving loan contracts",
    )

ratio_col, annuity_col, share_col = st.columns(3)
with ratio_col.container(border=True):
    st.subheader("Loan-to-income distribution", icon=":material/bar_chart:")
    visible_ratios = loan_to_income.loc[loan_to_income.between(0, 10)]
    if visible_ratios.empty:
        st.info("No valid loan-to-income ratios are available.")
    else:
        ratio_edges = [index * 10 / 25 for index in range(26)]
        ratio_bins = pd.cut(
            visible_ratios,
            bins=ratio_edges,
            include_lowest=True,
        )
        ratio_counts = ratio_bins.value_counts(sort=False)
        ratio_density = ratio_counts / (len(visible_ratios) * (10 / 25))
        ratio_distribution = pd.DataFrame(
            {
                "Loan-to-income ratio": [
                    f"{max(interval.left, 0):.1f}" for interval in ratio_counts.index
                ],
                "Density": ratio_density.to_numpy(),
            }
        )
        st.echarts_chart(
            {
                "tooltip": {"trigger": "axis", "valueFormatter": "%.2f"},
                "dataset": {"source": ratio_distribution},
                "xAxis": {
                    "type": "category",
                    "name": "AMT_CREDIT / AMT_INCOME_TOTAL",
                    "nameLocation": "middle",
                    "nameGap": 28,
                    "axisLabel": {"interval": 4},
                },
                "yAxis": {"type": "value", "name": "Density"},
                "series": [
                    {
                        "type": "line",
                        "encode": {
                            "x": "Loan-to-income ratio",
                            "y": "Density",
                        },
                        "smooth": True,
                        "showSymbol": False,
                        "lineStyle": {"color": "#16A6A1"},
                        "areaStyle": {"color": "#16A6A1", "opacity": 0.35},
                    }
                ],
            },
            height=230,
            alt="Distribution of loan-to-income ratios up to ten",
        )

with annuity_col.container(border=True):
    st.subheader("Annuity-to-income comparison", icon=":material/monitoring:")
    target_labels = {0: "Non-default (0)", 1: "Default (1)"}
    annuity_by_target = (
        pd.DataFrame(
            {
                "Target": df["TARGET"].map(target_labels),
                "Ratio": annuity_to_income,
            }
        )
        .dropna()
        .groupby("Target", observed=True)["Ratio"]
        .mean()
        .reindex(["Non-default (0)", "Default (1)"])
        .dropna()
    )
    if annuity_by_target.empty:
        st.info("No annuity-to-income ratios are available for this selection.")
    else:
        target_colors = {
            "Non-default (0)": "#16A6A1",
            "Default (1)": "#F5A623",
        }
        st.echarts_chart(
            {
                "tooltip": {"trigger": "axis", "valueFormatter": "%.2f"},
                "xAxis": {
                    "type": "category",
                    "data": annuity_by_target.index.tolist(),
                },
                "yAxis": {
                    "type": "value",
                    "name": "Average annuity-to-income ratio",
                    "min": 0,
                },
                "series": [
                    {
                        "type": "bar",
                        "data": [
                            {
                                "value": float(value),
                                "itemStyle": {
                                    "color": target_colors[str(target)]
                                },
                                "label": {
                                    "show": True,
                                    "position": "top",
                                    "formatter": f"{value:.2f}",
                                },
                            }
                            for target, value in annuity_by_target.items()
                        ],
                        "barMaxWidth": 90,
                    }
                ],
            },
            height=230,
            alt="Average annuity-to-income ratio for non-default and default applications",
        )

with share_col.container(border=True):
    st.subheader("Contract type share", icon=":material/pie_chart:")
    contract_counts = (
        df["NAME_CONTRACT_TYPE"]
        .value_counts()
        .reindex(CONTRACT_ORDER, fill_value=0)
    )
    contract_share_data = [
        {
            "name": f"{contract_type} ({count:,})",
            "value": int(count),
            "itemStyle": {
                "color": "#16A6A1"
                if contract_type == "Cash loans"
                else "#F5A623"
            },
        }
        for contract_type, count in contract_counts.items()
        if count > 0
    ]
    st.echarts_chart(
        {
            "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
            "legend": {
                "orient": "vertical",
                "right": 0,
                "top": "middle",
                "formatter": "{name}",
            },
            "graphic": [
                {
                    "type": "text",
                    "left": "34%",
                    "top": "50%",
                    "style": {
                        "text": f"{len(df):,}\nApplications",
                        "textAlign": "center",
                        "textVerticalAlign": "middle",
                        "fontSize": 13,
                        "fontWeight": "bold",
                        "fill": "#14233c",
                    },
                }
            ],
            "series": [
                {
                    "type": "pie",
                    "radius": ["45%", "68%"],
                    "center": ["34%", "50%"],
                    "data": contract_share_data,
                    "label": {
                        "show": True,
                        "position": "inside",
                        "formatter": "{d}%",
                    },
                }
            ],
        },
        height=230,
        alt="Share of cash and revolving loan applications",
    )

st.subheader("Loan application details", icon=":material/table_chart:")
rows_per_page = 5
total_pages = max(1, (len(df) + rows_per_page - 1) // rows_per_page)
page_number = st.session_state.get("loan_application_page", 1)
if page_number > total_pages:
    page_number = 1
    st.session_state["loan_application_page"] = 1

start_index = (page_number - 1) * rows_per_page
end_index = start_index + rows_per_page
detail_columns = [
    "SK_ID_CURR",
    "NAME_CONTRACT_TYPE",
    "AMT_CREDIT",
    "AMT_INCOME_TOTAL",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "TARGET",
]
st.dataframe(
    df[detail_columns].iloc[start_index:end_index],
    column_config={
        column: st.column_config.NumberColumn(
            alignment="center",
            format="%.2f",
        )
        for column in [
            "AMT_CREDIT",
            "AMT_INCOME_TOTAL",
            "AMT_ANNUITY",
            "AMT_GOODS_PRICE",
        ]
    },
    hide_index=True,
    alt="Loan application records matching the selected filters",
)

_, summary_col = st.columns([3, 1])
with summary_col:
    st.markdown(
        f"Showing {start_index + 1:,}–{min(end_index, len(df)):,} "
        f"of {len(df):,} records.",
        text_alignment="right",
    )
with st.container(horizontal=True, horizontal_alignment="right"):
    st.pagination(
        total_pages,
        max_visible_pages=5,
        key="loan_application_page",
        width="content",
    )
