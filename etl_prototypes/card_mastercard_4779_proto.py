"""Prototype pipeline scaffold for Mastercard 4779 normalization."""

from __future__ import annotations

import pandas as pd

from etl_common.column_mapping import select_mapped_columns, translate_columns
from etl_common.date_utilities import filter_by_dates_range, normalize_date_column
from etl_common.header_detection import apply_header_row, detect_header_row_by_required_headers
from etl_sources.account_registry import attach_account_metadata
from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT
from etl_sources.mastercard_4779_constants import (
    MASTERCARD_4779_ACCOUNT_NAME,
    MASTERCARD_4779_INPUT_DATE_FORMAT,
    MASTERCARD_4779_REQUIRED_HEADERS,
    MASTERCARD_4779_SOURCE_TO_CANONICAL_COLUMN_MAP,
)
from etl_sources.mastercard_4779_reader import load_mastercard_4779_tables


def main(path_to_folder: str, dates_range: tuple[str, str] | None = None) -> pd.DataFrame:
    """Run the Mastercard 4779 prototype pipeline on loaded tables."""
    loaded_tables = load_mastercard_4779_tables(folder=path_to_folder, recursive=False)
    for table in loaded_tables:
        print(f"\nFile: {table.path.name} ({table.extension})")
        df_pending = table.dataframe
        print(df_pending.head())

    if dates_range:
        print(f"Requested date range: {dates_range[0]} -> {dates_range[1]}")

    df_pending = normalize_mastercard_4779_table(df_pending, dates_range=dates_range)
    print(df_pending.head())
    return df_pending


def normalize_mastercard_4779_table(
    df_pending: pd.DataFrame, dates_range: tuple[str, str] | None = None
) -> pd.DataFrame:
    """End-to-end Mastercard 4779 normalization story (you implement details)."""
    header_row_idx = detect_header_row_by_required_headers(
        df_pending,
        required_headers=MASTERCARD_4779_REQUIRED_HEADERS,
    )
    normalized_df = apply_header_row(df_pending, header_row_idx)
    normalized_df = translate_columns(
        df=normalized_df,
        source_to_canonical_map=MASTERCARD_4779_SOURCE_TO_CANONICAL_COLUMN_MAP,
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
        source_to_canonical_map=MASTERCARD_4779_SOURCE_TO_CANONICAL_COLUMN_MAP,
    )
    normalized_df = attach_account_metadata(
        df=normalized_df,
        account_name=MASTERCARD_4779_ACCOUNT_NAME,
    )
    return normalized_df


def normalize_ynab_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """Parse and normalize Mastercard 4779 date column to YNAB format."""
    if not MASTERCARD_4779_INPUT_DATE_FORMAT:
        raise NotImplementedError("Set MASTERCARD_4779_INPUT_DATE_FORMAT before date normalization.")
    return normalize_date_column(
        df=df,
        date_column="Date",
        input_date_format=MASTERCARD_4779_INPUT_DATE_FORMAT,
        output_date_format=YNAB_OUTPUT_DATE_FORMAT,
    )


if __name__ == "__main__":
    path_to_folder = r"C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\card_mastercard_4779"
    dates_range = ("01/01/2026", "01/03/2026")
    main(path_to_folder=path_to_folder, dates_range=dates_range)
