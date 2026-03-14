"""Prototype pipeline scaffold for normalizing Leumi exports toward YNAB shape."""

from __future__ import annotations

import pandas as pd

from etl_common.column_mapping import translate_columns
from etl_common.date_normalization import normalize_date_column
from etl_common.header_detection import detect_header_row_by_required_headers, apply_header_row
from etl_sources.leumi_reader import load_leumi_tables
from etl_sources.account_registry import attach_account_metadata
from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT
from etl_sources.leumi_constants import (
    LEUMI_ACCOUNT_NAME,
    LEUMI_SOURCE_TO_CANONICAL_COLUMN_MAP,
    LEUMI_INPUT_DATE_FORMAT,
    LEUMI_REQUIRED_HEADERS,
)


def main(path_to_folder: str, dates_range: tuple[str, str] | None = None) -> None:
    """Run the Leumi prototype pipeline on loaded tables.

    Parameters
    ----------
    path_to_folder : str
        Folder containing Leumi source files.
    dates_range : tuple[str, str] | None, optional
        Optional date range hint for the run, by default None.
    """
    loaded_tables = load_leumi_tables(folder=path_to_folder, recursive=False)
    for table in loaded_tables:
        print(f"\nFile: {table.path.name} ({table.extension})")
        df_pending = table.dataframe
        print(df_pending.head())

    if dates_range:
        print(f"Requested date range: {dates_range[0]} -> {dates_range[1]}")

    df_pending = normalize_leumi_table(df_pending, dates_range=dates_range)
    
    print('in')

def normalize_leumi_table(
    df_pending: pd.DataFrame, dates_range: tuple[str, str] | None = None
) -> pd.DataFrame:
    """End-to-end Leumi normalization story (to be implemented by you)."""
    header_row_idx = detect_header_row_by_required_headers(df_pending, required_headers=LEUMI_REQUIRED_HEADERS)
    normalized_df = apply_header_row(df_pending, header_row_idx)
    normalized_df = translate_leumi_columns(normalized_df)
    normalized_df = normalize_ynab_date_column(normalized_df)
    normalized_df = filter_by_dates_range(normalized_df, dates_range=dates_range)
    normalized_df = select_mapped_output_columns(normalized_df)
    normalized_df = add_leumi_account_metadata(normalized_df)
    return normalized_df


def detect_leumi_header_row(df: pd.DataFrame, default_row_idx: int = 1) -> int:
    """Detect header row using a Leumi column-signature heuristic with fallback."""
    required_headers = {"הערה", "בזכות", "בחובה", "אסמכתא", "תאריך"}

    def normalize_cell(value: object) -> str:
        if pd.isna(value):
            return ""
        return str(value).strip()

    start_row = max(default_row_idx, 0)
    for row_idx in range(start_row, len(df)):
        row_values = {normalize_cell(value) for value in df.iloc[row_idx].tolist()}
        if required_headers.issubset(row_values):
            return row_idx

    return default_row_idx





def translate_leumi_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Translate Leumi source headers to canonical names."""
    return translate_columns(
        df=df,
        source_to_canonical_map=LEUMI_SOURCE_TO_CANONICAL_COLUMN_MAP,
    )


def normalize_ynab_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """Parse and normalize Leumi date column to YNAB format."""
    return normalize_date_column(
        df=df,
        date_column="Date",
        input_date_format=LEUMI_INPUT_DATE_FORMAT,
        output_date_format=YNAB_OUTPUT_DATE_FORMAT,
    )


def filter_by_dates_range(
    df: pd.DataFrame, dates_range: tuple[str, str] | None = None
) -> pd.DataFrame:
    """Optional inclusive date-range filter on normalized ``Date`` column."""
    if dates_range is None:
        return df.copy()

    start_date_str, end_date_str = dates_range
    start_date = pd.to_datetime(start_date_str, format=YNAB_OUTPUT_DATE_FORMAT, errors="raise")
    end_date = pd.to_datetime(end_date_str, format=YNAB_OUTPUT_DATE_FORMAT, errors="raise")

    parsed_dates = pd.to_datetime(df["Date"], format=YNAB_OUTPUT_DATE_FORMAT, errors="coerce")
    in_range_mask = parsed_dates.between(start_date, end_date, inclusive="both")
    return df.loc[in_range_mask].copy()


def select_mapped_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only mapped canonical output columns that exist."""
    keep_columns = [
        column for column in LEUMI_SOURCE_TO_CANONICAL_COLUMN_MAP.values() if column in df.columns
    ]
    return df[keep_columns]


def add_leumi_account_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Attach canonical account and ownership columns for Leumi source."""
    return attach_account_metadata(df=df, account_name=LEUMI_ACCOUNT_NAME)

# Entry point
if __name__ == "__main__":
    path_to_folder = r'C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\bank_leumi'
    dates_range = ("01/01/2026", "01/03/2026")
    main(path_to_folder=path_to_folder, dates_range=dates_range)