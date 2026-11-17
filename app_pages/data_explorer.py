import re

import streamlit as st

from utils.data import (
    DATASETS,
    dataset_file_size,
    load_column_descriptions,
    load_dataset_preview,
)


st.title("Data explorer", icon=":material/database:")
st.caption(
    "Inspect small previews of the source tables and look up their documented columns. "
    "Previews are not full-table analyses."
)

dataset_name = st.selectbox("Dataset", list(DATASETS))
row_count = st.select_slider(
    "Preview rows",
    options=[10, 25, 100, 500],
    value=25,
)

size_bytes = dataset_file_size(dataset_name)
size_mb = size_bytes / (1024 * 1024)
st.metric("Source file size", f"{size_mb:,.1f} MB", border=True)
st.caption(
    "Large related tables are read only as a preview here. The application dashboards "
    "use the full training application table."
)

preview = load_dataset_preview(dataset_name, row_count)
st.subheader(f"{dataset_name} preview")
st.dataframe(
    preview,
    hide_index=True,
    alt=f"First {len(preview)} rows from {dataset_name}; this is a preview only",
)
st.download_button(
    "Download preview",
    data=preview.to_csv(index=False).encode("utf-8"),
    file_name=f"{dataset_name.removesuffix('.csv')}_preview.csv",
    mime="text/csv",
    icon=":material/download:",
)

st.subheader("Column descriptions")
descriptions = load_column_descriptions()
description_table = (
    "application_{train|test}.csv"
    if dataset_name in {"application_train.csv", "application_test.csv"}
    else dataset_name
)
table_descriptions = descriptions.loc[
    descriptions["Table"].eq(description_table)
].copy()

search = st.text_input(
    "Search columns or descriptions",
    type="search",
    placeholder="For example: AMT_CREDIT or loan amount",
)
if search:
    search_pattern = re.escape(search)
    matching_rows = (
        table_descriptions["Row"].astype(str).str.contains(
            search_pattern, case=False, na=False
        )
        | table_descriptions["Description"].str.contains(
            search_pattern, case=False, na=False
        )
    )
    table_descriptions = table_descriptions.loc[matching_rows]

st.dataframe(
    table_descriptions[["Row", "Description", "Special"]],
    hide_index=True,
    alt=f"Documented columns for {dataset_name}",
)
