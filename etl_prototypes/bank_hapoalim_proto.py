"""Prototype pipeline scaffold for normalizing Hapoalim exports toward YNAB shape."""

from __future__ import annotations

import pandas as pd

from etl_common.column_mapping import select_mapped_columns, translate_columns
from etl_common.date_utilities import normalize_date_column, filter_by_dates_range
from etl_sources.account_registry import attach_account_metadata
from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT
from etl_sources.hapoalim_constants import (
    HAPOALIM_ACCOUNT_NAME,
    HAPOALIM_INPUT_DATE_FORMAT,
    HAPOALIM_SOURCE_TO_CANONICAL_COLUMN_MAP,
    HAPOALIM_REQUIRED_HEADERS,
)
from etl_sources.hapoalim_reader import load_hapoalim_tables
from etl_common.header_detection import detect_header_row_by_required_headers, apply_header_row


def main(path_to_folder: str, dates_range: tuple[str, str] | None = None) -> None:
    """Run the Hapoalim prototype pipeline on loaded tables."""
    loaded_tables = load_hapoalim_tables(folder=path_to_folder, recursive=False)
    for table in loaded_tables:
        print(f"\nFile: {table.path.name} ({table.extension})")
        df_pending = table.dataframe
        print(df_pending.head())

    if dates_range:
        print(f"Requested date range: {dates_range[0]} -> {dates_range[1]}")

    df_pending = normalize_hapoalim_table(df_pending, dates_range=dates_range)
    print(df_pending.head())
    return df_pending


def normalize_hapoalim_table(
    df_pending: pd.DataFrame, dates_range: tuple[str, str] | None = None
) -> pd.DataFrame:
    """End-to-end Hapoalim normalization story (to be implemented by you)."""
    header_row_idx = detect_header_row_by_required_headers(df_pending, required_headers=HAPOALIM_REQUIRED_HEADERS)
    normalized_df = apply_header_row(df_pending, header_row_idx)
    normalized_df = translate_columns(df=normalized_df, source_to_canonical_map=HAPOALIM_SOURCE_TO_CANONICAL_COLUMN_MAP)
    normalized_df = normalize_ynab_date_column(normalized_df)
    normalized_df = filter_by_dates_range(normalized_df, date_column="Date", dates_range=dates_range, output_date_format=YNAB_OUTPUT_DATE_FORMAT)
    normalized_df = select_mapped_columns(df=normalized_df, source_to_canonical_map=HAPOALIM_SOURCE_TO_CANONICAL_COLUMN_MAP)
    normalized_df = memo_hapoalim_table(normalized_df)
    normalized_df = attach_account_metadata(df=normalized_df, account_name=HAPOALIM_ACCOUNT_NAME)
    return normalized_df

def memo_hapoalim_table(df_pending: pd.DataFrame) -> pd.DataFrame:
    """Memo the Hapoalim table."""
    print(df_pending.head())
    for col in ['Details', 'To Whom 2', 'From Whom']:
        if col in df_pending.columns:
            df_pending[col] = df_pending[col].apply(lambda p: str(p).replace('nan', ''))
            df_pending[col] = df_pending[col].apply(lambda p: f"{str(p).strip()}, " if str(p).strip() != '' else '')

    df_pending['Memo'] = df_pending['Details'] + df_pending['To Whom 2'] + df_pending['From Whom']
    df_pending = df_pending.drop(columns=['Details', 'To Whom 2', 'From Whom'])
    return df_pending



def normalize_ynab_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """Parse and normalize Hapoalim date column to YNAB format."""
    if not HAPOALIM_INPUT_DATE_FORMAT:
        raise NotImplementedError("Set HAPOALIM_INPUT_DATE_FORMAT before date normalization.")
    return normalize_date_column(
        df=df,
        date_column="Date",
        input_date_format=HAPOALIM_INPUT_DATE_FORMAT,
        output_date_format=YNAB_OUTPUT_DATE_FORMAT,
    )


def select_mapped_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only mapped canonical output columns that exist."""
    return select_mapped_columns(
        df=df,
        source_to_canonical_map=HAPOALIM_SOURCE_TO_CANONICAL_COLUMN_MAP,
    )





if __name__ == "__main__":
    path_to_folder = r"C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\bank_hapoalim"
    dates_range = ("01/01/2026", "01/03/2026")
    main(path_to_folder=path_to_folder, dates_range=dates_range)
