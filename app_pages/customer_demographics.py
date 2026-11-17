import pandas as pd
import streamlit as st

from utils.data import (
    filtered_applications,
    load_applications,
    render_application_filters,
)


AGE_GROUP_EDGES = [0, 25, 30, 35, 40, 45, 50, 55, 60, float("inf")]
AGE_GROUP_LABELS = [
    "<25",
    "25-29",
    "30-34",
    "35-39",
    "40-44",
    "45-49",
    "50-54",
    "55-59",
    "60+",
]


st.title("Customer demographics", icon=":material/groups:")
st.caption(
    "Customer profile, family structure, education and age analysis with default risk."
)

all_applications = load_applications()
family_options = sorted(
    all_applications["NAME_FAMILY_STATUS"]
    .astype("string")
    .fillna("Not reported")
    .unique()
    .tolist()
)
education_options = sorted(
    all_applications["NAME_EDUCATION_TYPE"]
    .astype("string")
    .fillna("Not reported")
    .unique()
    .tolist()
)
filters = render_application_filters(
    "customer_demographics",
    [
        ("age_group", "Age group", ["All", *AGE_GROUP_LABELS]),
        ("family_status", "Family status", ["All", *family_options]),
        ("education", "Education", ["All", *education_options]),
    ],
)
base_df = filtered_applications(filters).copy()
if base_df.empty:
    st.warning("No applications match these filters. Change or reset the selections above.")
    st.stop()

base_df["GENDER"] = (
    base_df["CODE_GENDER"]
    .astype("string")
    .map({"F": "Female", "M": "Male", "XNA": "Unknown"})
    .fillna("Unknown")
)
base_df["FAMILY_STATUS"] = (
    base_df["NAME_FAMILY_STATUS"].astype("string").fillna("Not reported")
)
base_df["EDUCATION"] = (
    base_df["NAME_EDUCATION_TYPE"].astype("string").fillna("Not reported")
)
base_df["AGE_GROUP"] = pd.cut(
    base_df["AGE_YEARS"],
    bins=AGE_GROUP_EDGES,
    labels=AGE_GROUP_LABELS,
    right=False,
)

df = base_df
if filters["age_group"] != "All":
    df = df.loc[df["AGE_GROUP"].astype("string").eq(filters["age_group"])]
if filters["family_status"] != "All":
    df = df.loc[df["FAMILY_STATUS"].eq(filters["family_status"])]
if filters["education"] != "All":
    df = df.loc[df["EDUCATION"].eq(filters["education"])]

if df.empty:
    st.warning("No customers match these filters. Change or reset the selections.")
    st.stop()

total = len(df)
male_count = int(df["GENDER"].eq("Male").sum())
female_count = int(df["GENDER"].eq("Female").sum())
average_age = df["AGE_YEARS"].mean()
married_count = int(df["FAMILY_STATUS"].eq("Married").sum())
average_family_size = df["CNT_FAM_MEMBERS"].mean()
customers_with_children = int(df["CNT_CHILDREN"].gt(0).sum())

st.html(
    """
    <style>
    .st-key-customer-male { background: #e8f4fd; border: 1px solid #d4e7f5; border-radius: 0.75rem; padding: 0.55rem 0.7rem; }
    .st-key-customer-male * { color: #19324f !important; }
    .st-key-customer-female { background: #fceaf3; border: 1px solid #f2d5e4; border-radius: 0.75rem; padding: 0.55rem 0.7rem; }
    .st-key-customer-female * { color: #803b65 !important; }
    .st-key-customer-age { background: #e4f6ed; border: 1px solid #cfe9da; border-radius: 0.75rem; padding: 0.55rem 0.7rem; }
    .st-key-customer-age * { color: #24583a !important; }
    .st-key-customer-married { background: #fff1e5; border: 1px solid #f2dfca; border-radius: 0.75rem; padding: 0.55rem 0.7rem; }
    .st-key-customer-married * { color: #805126 !important; }
    .st-key-customer-family { background: #f0edff; border: 1px solid #dfd9f4; border-radius: 0.75rem; padding: 0.55rem 0.7rem; }
    .st-key-customer-family * { color: #493878 !important; }
    .st-key-customer-children { background: #e4f6f7; border: 1px solid #cfe9eb; border-radius: 0.75rem; padding: 0.55rem 0.7rem; }
    .st-key-customer-children * { color: #14566a !important; }
    </style>
    """
)

kpi_specs = [
    (
        "customer-male",
        "Male customers",
        f"{male_count:,}",
        f"({male_count / total:.2%})",
        ":material/male:",
    ),
    (
        "customer-female",
        "Female customers",
        f"{female_count:,}",
        f"({female_count / total:.2%})",
        ":material/female:",
    ),
    (
        "customer-age",
        "Average age",
        f"{average_age:.2f} years",
        None,
        ":material/calendar_month:",
    ),
    (
        "customer-married",
        "Married customers",
        f"{married_count / total:.2%}",
        f"({married_count:,} customers)",
        ":material/favorite:",
    ),
    (
        "customer-family",
        "Average family size",
        f"{average_family_size:.2f}",
        None,
        ":material/groups:",
    ),
    (
        "customer-children",
        "Customers with children",
        f"{customers_with_children / total:.2%}",
        f"({customers_with_children:,} customers)",
        ":material/child_care:",
    ),
]

for column, (key, label, value, detail, icon) in zip(
    st.columns(6, gap="small"),
    kpi_specs,
):
    with column.container(key=key, height="stretch"):
        st.metric(label, value, icon=icon)
        if detail is not None:
            st.caption(detail)

left_chart, middle_chart, right_chart = st.columns([1.2, 1, 1.2])

with left_chart.container(border=True):
    st.subheader("Age distribution")
    age_bins = [0, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 100]
    age_labels = [
        "<20",
        "20-24",
        "25-29",
        "30-34",
        "35-39",
        "40-44",
        "45-49",
        "50-54",
        "55-59",
        "60-64",
        "65-69",
        "70-74",
        "75+",
    ]
    age_bins_series = pd.cut(
        df["AGE_YEARS"],
        bins=age_bins,
        labels=age_labels,
        right=False,
    )
    age_distribution = (
        age_bins_series.value_counts(sort=False)
        .rename_axis("Age")
        .reset_index(name="Customers")
    )
    age_distribution = age_distribution.loc[age_distribution["Customers"].gt(0)]
    st.echarts_chart(
        {
            "color": ["#8451d4"],
            "tooltip": {"trigger": "axis"},
            "xAxis": {
                "type": "category",
                "data": age_distribution["Age"].astype(str).tolist(),
                "name": "Age (years)",
                "nameLocation": "middle",
                "nameGap": 28,
            },
            "yAxis": {"type": "value", "name": "Customers"},
            "series": [
                {
                    "type": "bar",
                    "data": age_distribution["Customers"].tolist(),
                    "barMaxWidth": 22,
                }
            ],
        },
        alt="Customer counts across age ranges",
    )

with middle_chart.container(border=True):
    st.subheader("Gender distribution")
    gender_order = ["Male", "Female", "Unknown"]
    gender_counts = (
        df["GENDER"]
        .value_counts()
        .reindex(gender_order, fill_value=0)
    )
    gender_colors = {"Male": "#2878e8", "Female": "#8451d4", "Unknown": "#8c95a6"}
    gender_data = [
        {
            "name": gender,
            "value": int(count),
            "itemStyle": {"color": gender_colors[gender]},
        }
        for gender, count in gender_counts.items()
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
                    "left": "32%",
                    "top": "middle",
                    "style": {
                        "text": f"{total:,}\nCustomers",
                        "textAlign": "center",
                        "textVerticalAlign": "middle",
                        "fontSize": 14,
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
                    "data": gender_data,
                    "minShowLabelAngle": 3,
                    "label": {
                        "show": True,
                        "position": "inside",
                        "formatter": "{d}%",
                    },
                }
            ],
        },
        alt="Customer distribution by gender",
    )

with right_chart.container(border=True):
    st.subheader("Family status distribution")
    family_counts = (
        df["FAMILY_STATUS"]
        .value_counts()
        .sort_values(ascending=False)
        .rename_axis("Family status")
        .reset_index(name="Customers")
    )
    st.echarts_chart(
        {
            "color": ["#16a6a1", "#8451d4", "#a882e4", "#c1a8eb", "#d8c8f2"],
            "tooltip": {"trigger": "axis"},
            "xAxis": {
                "type": "category",
                "data": family_counts["Family status"].tolist(),
                "name": "Family status",
                "nameLocation": "middle",
                "nameGap": 38,
                "axisLabel": {"rotate": 18, "interval": 0},
            },
            "yAxis": {"type": "value", "name": "Customers"},
            "series": [
                {
                    "type": "bar",
                    "data": family_counts["Customers"].tolist(),
                    "label": {"show": True, "position": "top", "formatter": "{c}"},
                }
            ],
        },
        alt="Customer counts by family status",
    )

education_col, age_rate_col = st.columns([1, 1.35])
with education_col.container(border=True):
    st.subheader("Default rate by education")
    education_rates = (
        df.groupby("EDUCATION", observed=True)["TARGET"]
        .mean()
        .mul(100)
        .sort_values(ascending=False)
        .rename("Default rate")
        .rename_axis("Education")
        .reset_index()
    )
    st.echarts_chart(
        {
            "tooltip": {"trigger": "axis", "valueFormatter": "%.2f%%"},
            "xAxis": {
                "type": "value",
                "name": "Default rate (%)",
                "axisLabel": {"formatter": "{value}%"},
            },
            "yAxis": {
                "type": "category",
                "data": education_rates["Education"].tolist(),
                "inverse": True,
            },
            "series": [
                {
                    "type": "bar",
                    "data": education_rates["Default rate"].round(2).tolist(),
                    "itemStyle": {"color": "#8451d4"},
                    "label": {
                        "show": True,
                        "position": "right",
                        "formatter": "{c}%",
                    },
                }
            ],
        },
        alt="Historical default rate for each education category",
    )

with age_rate_col.container(border=True):
    st.subheader("Default rate by age group")
    age_rates = (
        df.dropna(subset=["AGE_GROUP"])
        .groupby("AGE_GROUP", observed=True)["TARGET"]
        .mean()
        .mul(100)
        .rename("Default rate")
        .reset_index()
    )
    age_rates["Age group"] = age_rates["AGE_GROUP"].astype(str)
    age_rates["Default rate"] = age_rates["Default rate"].round(2)
    st.echarts_chart(
        {
            "color": ["#8451d4"],
            "tooltip": {"trigger": "axis", "valueFormatter": "%.2f%%"},
            "xAxis": {
                "type": "category",
                "data": age_rates["Age group"].tolist(),
                "name": "Age group (years)",
                "nameLocation": "middle",
                "nameGap": 28,
            },
            "yAxis": {
                "type": "value",
                "name": "Default rate (%)",
                "axisLabel": {"formatter": "{value}%"},
            },
            "series": [
                {
                    "type": "line",
                    "data": age_rates["Default rate"].tolist(),
                    "smooth": True,
                    "symbol": "circle",
                    "areaStyle": {"opacity": 0.12},
                    "label": {
                        "show": True,
                        "position": "top",
                        "formatter": "{c}%",
                    },
                }
            ],
        },
        alt="Historical default rate by customer age group",
    )

with st.container(border=True):
    metric_col, example_col = st.columns([0.8, 2.2])
    metric_col.markdown(
        "**Derived metric**  \n"
        "`AGE_YEARS = -DAYS_BIRTH / 365.25`"
    )
    example_col.markdown(
        "**Example:** `DAYS_BIRTH = -16000` "
        "-> `AGE_YEARS = 16000 / 365.25 = 43.81 years`"
    )

st.subheader("Customer table (sample)", icon=":material/table_chart:")
table_columns = [
    "SK_ID_CURR",
    "CODE_GENDER",
    "DAYS_BIRTH",
    "NAME_FAMILY_STATUS",
    "NAME_EDUCATION_TYPE",
    "CNT_CHILDREN",
    "CNT_FAM_MEMBERS",
    "TARGET",
]
rows_per_page = 10
total_pages = max(1, (len(df) + rows_per_page - 1) // rows_per_page)
page_number = st.session_state.get("customer_demographics_page", 1)
if page_number > total_pages:
    page_number = 1
    st.session_state["customer_demographics_page"] = 1

start_index = (page_number - 1) * rows_per_page
end_index = start_index + rows_per_page
st.dataframe(
    df[table_columns].iloc[start_index:end_index],
    hide_index=True,
    alt="Sample customer demographic records matching the selected filters",
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
        key="customer_demographics_page",
        width="content",
    )
