import pandas as pd
import streamlit as st

from utils.data import filtered_applications, render_application_filters


st.title("Default risk analysis", icon=":material/warning:")
st.caption(
    "Observed training-set default rates across application features; these are associations, "
    "not individual credit decisions."
)

filters = render_application_filters("default_risk")
df = filtered_applications(filters)
if df.empty:
    st.warning("No applications match these filters. Adjust the selections above.")
    st.stop()

default_rate = df["TARGET"].mean()
st.html(
    """
    <style>
    .st-key-risk-default-rate { background: #fdecec; border: 1px solid #f3d5d5; border-radius: 0.75rem; padding: 0.6rem 0.9rem; }
    .st-key-risk-default-rate * { color: #782f32 !important; }
    </style>
    """
)
with st.container(key="risk-default-rate"):
    st.metric("Observed default rate", f"{default_rate:.2%}")

score_columns = ["EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3"]
available_scores = [column for column in score_columns if column in df.columns]
if available_scores:
    st.subheader("External source score and observed outcomes")
    score_choice = st.selectbox(
        "External score",
        available_scores,
        format_func=lambda column: column.replace("_", " ").title(),
    )
    score_data = df[[score_choice, "TARGET"]].dropna().copy()
    if not score_data.empty:
        try:
            score_data["Score group"] = pd.qcut(
                score_data[score_choice],
                q=10,
                duplicates="drop",
            )
        except ValueError:
            score_data["Score group"] = pd.cut(score_data[score_choice], bins=5)

        score_rates = (
            score_data.groupby("Score group", observed=True)["TARGET"]
            .agg(["mean", "count"])
            .reset_index()
            .rename(
                columns={
                    "mean": "Default rate",
                    "count": "Applications",
                }
            )
        )
        score_rates["Default rate"] *= 100
        score_rates["Score group"] = score_rates["Score group"].astype(str)
        st.bar_chart(
            score_rates,
            x="Score group",
            y="Default rate",
            y_label="Default rate (%)",
            alt=f"Observed default rate by {score_choice} score group",
        )
    else:
        st.info("No score values are available for this filter.")

type_col, occupation_col = st.columns(2)
with type_col:
    st.subheader("Default rate by income type")
    income_rates = (
        df.groupby("NAME_INCOME_TYPE", observed=True)["TARGET"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(
            columns={
                "NAME_INCOME_TYPE": "Income type",
                "mean": "Default rate",
                "count": "Applications",
            }
        )
    )
    income_rates["Default rate"] *= 100
    st.bar_chart(
        income_rates,
        x="Income type",
        y="Default rate",
        y_label="Default rate (%)",
        alt="Observed default rate by applicant income type",
    )

with occupation_col:
    st.subheader("Default rate by occupation")
    occupation_rates = (
        df.groupby("OCCUPATION_TYPE", observed=True)["TARGET"]
        .agg(["mean", "count"])
        .reset_index()
        .dropna(subset=["OCCUPATION_TYPE"])
        .nlargest(12, "count")
        .rename(
            columns={
                "OCCUPATION_TYPE": "Occupation",
                "mean": "Default rate",
                "count": "Applications",
            }
        )
    )
    occupation_rates["Default rate"] *= 100
    st.bar_chart(
        occupation_rates,
        x="Occupation",
        y="Default rate",
        y_label="Default rate (%)",
        alt="Observed default rate for the twelve most common occupations",
    )

st.subheader("Risk indicator data availability")
score_availability = (
    df[available_scores]
    .notna()
    .mean()
    .mul(100)
    .rename("Available applications (%)")
    .rename_axis("External score")
    .reset_index()
)
st.bar_chart(
    score_availability,
    x="External score",
    y="Available applications (%)",
    alt="Percentage of applications with each external source score present",
)
