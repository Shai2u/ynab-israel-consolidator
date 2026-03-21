"""Prototype pipeline scaffold for Isracard normalization."""

from __future__ import annotations

import pandas as pd

from etl_common.column_mapping import select_mapped_columns, translate_columns
from etl_common.date_utilities import filter_by_dates_range, normalize_date_column
from etl_common.header_detection import apply_header_row, detect_header_row_by_required_headers
from etl_sources.account_registry import attach_account_metadata
from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT
from etl_sources.isracard_constants import (
    ISRACARD_ACCOUNT_NAME,
    ISRACARD_HEADER_DEFAULT_ROW_IDX,
    ISRACARD_INPUT_DATE_FORMAT,
    ISRACARD_MEMO_SOURCE_COLUMNS,
    ISRACARD_REQUIRED_HEADERS,
    ISRACARD_SOURCE_TO_CANONICAL_COLUMN_MAP,
)
from etl_sources.isracard_reader import load_isracard_tables


def main(path_to_folder: str, dates_range: tuple[str, str] | None = None) -> pd.DataFrame:
    """Run the Isracard prototype pipeline on loaded tables."""
    loaded_tables = load_isracard_tables(folder=path_to_folder, recursive=False)
    normalized_frames: list[pd.DataFrame] = []

    for table in loaded_tables:
        print(f"\nFile: {table.path.name} ({table.extension})")
        df_pending = table.dataframe
        print(df_pending.head())
        normalized_df = normalize_isracard_table(df_pending, dates_range=dates_range)
        normalized_frames.append(normalized_df)

    if not normalized_frames:
        raise ValueError("No Isracard tables were loaded from the provided folder.")

    combined_normalized_df = pd.concat(normalized_frames, ignore_index=True)
    print(combined_normalized_df.head())
    return combined_normalized_df


def normalize_isracard_table(
    df_pending: pd.DataFrame, dates_range: tuple[str, str] | None = None
) -> pd.DataFrame:
    """End-to-end Isracard normalization story (you implement details)."""
    header_row_idx = detect_header_row_by_required_headers(
        df_pending,
        required_headers=ISRACARD_REQUIRED_HEADERS,
        default_row_idx=ISRACARD_HEADER_DEFAULT_ROW_IDX,
    )
    normalized_df = apply_header_row(df_pending, header_row_idx)
    normalized_df = translate_columns(
        df=normalized_df,
        source_to_canonical_map=ISRACARD_SOURCE_TO_CANONICAL_COLUMN_MAP,
    )
    normalized_df = normalize_ynab_date_column(normalized_df)
    normalized_df = filter_by_dates_range(
        normalized_df,
        date_column="Date",
        dates_range=dates_range,
        output_date_format=YNAB_OUTPUT_DATE_FORMAT,
    )
    normalized_df = select_mapped_columns(
        df=normalized_df,
        source_to_canonical_map=ISRACARD_SOURCE_TO_CANONICAL_COLUMN_MAP,
    )
    normalized_df = derive_inflow_outflow_from_amount(normalized_df)
    normalized_df = memo_isracard_table(normalized_df, memo_source_columns=ISRACARD_MEMO_SOURCE_COLUMNS)
    normalized_df = attach_account_metadata(
        df=normalized_df,
        account_name=ISRACARD_ACCOUNT_NAME,
    )
    return normalized_df


def normalize_ynab_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """Parse and normalize Isracard date column to YNAB format."""
    if not ISRACARD_INPUT_DATE_FORMAT:
        raise NotImplementedError("Set ISRACARD_INPUT_DATE_FORMAT before date normalization.")
    return normalize_date_column(
        df=df,
        date_column="Date",
        input_date_format=ISRACARD_INPUT_DATE_FORMAT,
        output_date_format=YNAB_OUTPUT_DATE_FORMAT,
    )


def derive_inflow_outflow_from_amount(df: pd.DataFrame) -> pd.DataFrame:
    """Derive Inflow/Outflow from Amount based on minus-sign rule."""
    if "Amount" not in df.columns:
        raise ValueError("Expected 'Amount' column after mapping.")

    normalized_df = df.copy()
    amount_str = normalized_df["Amount"].astype(str).str.strip()
    numeric_amount = pd.to_numeric(
        amount_str.str.replace(r"[^0-9.\-]", "", regex=True),
        errors="coerce",
    )
    abs_amount = numeric_amount.abs()
    minus_mask = amount_str.str.contains("-", regex=False)

    normalized_df["Inflow"] = abs_amount.where(minus_mask, 0.0)
    normalized_df["Outflow"] = abs_amount.where(~minus_mask, 0.0)
    normalized_df = normalized_df.drop(columns=["Amount"])
    return normalized_df


def memo_isracard_table(df: pd.DataFrame, memo_source_columns: dict[str, str]) -> pd.DataFrame:
    """Build memo text from optional source columns, then drop them."""
    if not memo_source_columns:
        return df

    normalized_df = df.copy()
    if "Memo" not in normalized_df.columns:
        normalized_df["Memo"] = ""

    drop_cols: list[str] = []
    for source_col, label in memo_source_columns.items():
        if source_col not in normalized_df.columns:
            continue
        value_str = normalized_df[source_col].astype(str).str.replace("nan", "", regex=False).str.strip()
        chunk = value_str.apply(lambda p: f"{label}:{p}, " if p else "")
        normalized_df["Memo"] = normalized_df["Memo"] + chunk
        drop_cols.append(source_col)

    if drop_cols:
        normalized_df = normalized_df.drop(columns=drop_cols)
    return normalized_df


if __name__ == "__main__":
    path_to_folder = r"C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\isracard"
    dates_range = ("01/01/2026", "01/03/2026")
    main(path_to_folder=path_to_folder, dates_range=dates_range)
