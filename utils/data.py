from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIRECTORY = PROJECT_ROOT / "Datasets"

DATASETS = {
    "application_train.csv": "application_train.csv",
    "application_test.csv": "application_test.csv",
    "bureau.csv": "bureau.csv",
    "bureau_balance.csv": "bureau_balance.csv",
    "POS_CASH_balance.csv": "POS_CASH_balance.csv",
    "credit_card_balance.csv": "credit_card_balance.csv",
    "previous_application.csv": "previous_application.csv",
    "installments_payments.csv": "installments_payments.csv",
    "HomeCredit_columns_description.csv": "HomeCredit_columns_description.csv",
    "sample_submission.csv": "sample_submission.csv",
}

APPLICATION_COLUMNS = [
    "SK_ID_CURR",
    "TARGET",
    "NAME_CONTRACT_TYPE",
    "CODE_GENDER",
    "CNT_CHILDREN",
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "AMT_GOODS_PRICE",
    "NAME_INCOME_TYPE",
    "NAME_EDUCATION_TYPE",
    "NAME_FAMILY_STATUS",
    "NAME_HOUSING_TYPE",
    "DAYS_BIRTH",
    "DAYS_EMPLOYED",
    "CNT_FAM_MEMBERS",
    "OCCUPATION_TYPE",
    "ORGANIZATION_TYPE",
    "REGION_RATING_CLIENT",
    "EXT_SOURCE_1",
    "EXT_SOURCE_2",
    "EXT_SOURCE_3",
]

APPLICATION_DTYPES: dict[str, Any] = {
    "SK_ID_CURR": "int32",
    "TARGET": "int8",
    "NAME_CONTRACT_TYPE": "category",
    "CODE_GENDER": "category",
    "CNT_CHILDREN": "int8",
    "AMT_INCOME_TOTAL": "float32",
    "AMT_CREDIT": "float32",
    "AMT_ANNUITY": "float32",
    "AMT_GOODS_PRICE": "float32",
    "NAME_INCOME_TYPE": "category",
    "NAME_EDUCATION_TYPE": "category",
    "NAME_FAMILY_STATUS": "category",
    "NAME_HOUSING_TYPE": "category",
    "DAYS_BIRTH": "int32",
    "DAYS_EMPLOYED": "int32",
    "CNT_FAM_MEMBERS": "float32",
    "OCCUPATION_TYPE": "category",
    "ORGANIZATION_TYPE": "category",
    "REGION_RATING_CLIENT": "int8",
    "EXT_SOURCE_1": "float32",
    "EXT_SOURCE_2": "float32",
    "EXT_SOURCE_3": "float32",
}


def dataset_path(dataset_name: str) -> Path:
    if dataset_name not in DATASETS:
        raise ValueError(f"Unknown Home Credit dataset: {dataset_name}")
    path = DATA_DIRECTORY / DATASETS[dataset_name]
    if not path.is_file():
        raise FileNotFoundError(
            f"Could not find {path}. Put the extracted Home Credit CSV files in "
            f"{DATA_DIRECTORY}."
        )
    return path


@st.cache_data(ttl="1h", max_entries=1, show_spinner="Loading application data...")
def load_applications() -> pd.DataFrame:
    path = dataset_path("application_train.csv")
    df = pd.read_csv(
        path,
        usecols=lambda column: column in APPLICATION_COLUMNS,
        dtype=APPLICATION_DTYPES,
        low_memory=False,
    )
    df["AGE_YEARS"] = (-df["DAYS_BIRTH"] / 365.25).astype("float32")
    days_employed = df["DAYS_EMPLOYED"]
    df["EMPLOYMENT_YEARS"] = (
        (-days_employed / 365.25).where(days_employed <= 0).astype("float32")
    )
    return df


def apply_application_filters(
    df: pd.DataFrame,
    filters: dict[str, str],
) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)

    contract_type = filters.get("contract_type", "All")
    if contract_type != "All":
        mask &= df["NAME_CONTRACT_TYPE"].eq(contract_type)

    gender = filters.get("gender", "All")
    gender_values = {"Female": "F", "Male": "M", "Unknown": "XNA"}
    if gender in gender_values:
        mask &= df["CODE_GENDER"].eq(gender_values[gender])

    target = filters.get("target", "All")
    if target == "Default":
        mask &= df["TARGET"].eq(1)
    elif target == "Non-default":
        mask &= df["TARGET"].eq(0)

    return df.loc[mask]


def _reset_filter_widgets(widget_keys: tuple[str, ...]) -> None:
    for key in widget_keys:
        st.session_state[key] = "All"


def render_application_filters(
    page_key: str,
    extra_filters: list[tuple[str, str, list[str]]] | None = None,
    filters_per_row: int = 4,
) -> dict[str, str]:
    filters = [
        ("contract_type", "Contract type", ["All", "Cash loans", "Revolving loans"]),
        ("gender", "Gender", ["All", "Female", "Male", "Unknown"]),
        ("target", "Target (default)", ["All", "Non-default", "Default"]),
        *(extra_filters or []),
    ]
    widget_keys = tuple(
        f"application_filter_{page_key}_{filter_key}"
        for filter_key, _, _ in filters
    )
    for widget_key, (_, _, options) in zip(widget_keys, filters):
        if widget_key not in st.session_state:
            st.session_state[widget_key] = options[0]

    with st.expander("Filters", expanded=False, icon=":material/filter_alt:"):
        with st.form(f"application_filters_{page_key}", border=False):
            if extra_filters:
                if filters_per_row < 1:
                    raise ValueError("filters_per_row must be a positive integer.")
                filter_rows = [
                    filters[index : index + filters_per_row]
                    for index in range(0, len(filters), filters_per_row)
                ]
                key_rows = [
                    widget_keys[index : index + filters_per_row]
                    for index in range(0, len(widget_keys), filters_per_row)
                ]
            else:
                filter_rows = [filters]
                key_rows = [widget_keys]

            for row_index, (filter_row, key_row) in enumerate(
                zip(filter_rows, key_rows)
            ):
                include_actions = (
                    row_index == len(filter_rows) - 1 and not extra_filters
                )
                column_count = (
                    len(filter_rows[0]) if extra_filters else len(filter_row)
                )
                columns = st.columns(
                    [1.4] * column_count
                    + ([1.7, 1.4] if include_actions else []),
                    gap="small",
                    vertical_alignment=(
                        "bottom" if include_actions else "top"
                    ),
                )
                for column, (widget_key, (_, label, options)) in zip(
                    columns, zip(key_row, filter_row)
                ):
                    column.selectbox(
                        label,
                        options,
                        key=widget_key,
                        width="stretch",
                    )
                if extra_filters:
                    for column in columns[len(filter_row) :]:
                        column.space("xxsmall")

            if extra_filters:
                with st.container(horizontal=True, wrap=False):
                    st.space("stretch")
                    st.form_submit_button(
                        "Apply filters",
                        type="primary",
                        icon=":material/filter_alt:",
                        width="content",
                    )
                    st.form_submit_button(
                        "Reset",
                        icon=":material/refresh:",
                        key=f"application_filters_reset_{page_key}",
                        on_click=_reset_filter_widgets,
                        args=(widget_keys,),
                        width="content",
                    )
                    st.space("stretch")
            else:
                columns[-2].form_submit_button(
                    "Apply filters",
                    type="primary",
                    icon=":material/filter_alt:",
                    width="stretch",
                )
                columns[-1].form_submit_button(
                    "Reset",
                    icon=":material/refresh:",
                    key=f"application_filters_reset_{page_key}",
                    on_click=_reset_filter_widgets,
                    args=(widget_keys,),
                    width="stretch",
                )

    return {
        filter_key: st.session_state[widget_key]
        for widget_key, (filter_key, _, _) in zip(widget_keys, filters)
    }


def filtered_applications(filters: dict[str, str] | None = None) -> pd.DataFrame:
    return apply_application_filters(load_applications(), filters or {})


@st.cache_data(ttl="1h", max_entries=10, show_spinner="Reading a small data preview...")
def load_dataset_preview(dataset_name: str, rows: int = 25) -> pd.DataFrame:
    return pd.read_csv(dataset_path(dataset_name), nrows=rows)


@st.cache_data(ttl="1h", max_entries=1)
def load_column_descriptions() -> pd.DataFrame:
    return pd.read_csv(
        dataset_path("HomeCredit_columns_description.csv"),
        encoding="cp1252",
    )


def dataset_file_size(dataset_name: str) -> int:
    return dataset_path(dataset_name).stat().st_size
