"""Prototype pipeline scaffold for Mastercard 4779 normalization."""

from __future__ import annotations

import pandas as pd

from etl_common.column_mapping import select_mapped_columns, translate_columns
from etl_common.date_utilities import filter_by_dates_range, normalize_date_column
from etl_common.header_detection import apply_header_row, detect_header_row_by_required_headers
from etl_sources.account_registry import attach_account_metadata
from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT
from etl_sources.visa_cal_constants import (
    VISA_CAL_ACCOUNT_NAME,
    VISA_CAL_INPUT_DATE_FORMAT,
    VISA_CAL_REQUIRED_HEADERS,
    VISA_CAL_SOURCE_TO_CANONICAL_COLUMN_MAP,
)
from etl_sources.visa_cal_reader import load_visa_cal_tables


def main(path_to_folder: str, dates_range: tuple[str, str] | None = None) -> pd.DataFrame:
    """Run the Visa Cal prototype pipeline on loaded tables."""
    loaded_tables = load_visa_cal_tables(folder=path_to_folder, recursive=False)
    normalized_frames: list[pd.DataFrame] = []

    for table in loaded_tables:
        print(f"\nFile: {table.path.name} ({table.extension})")
        df_pending = table.dataframe
        print(df_pending.head())
        normalized_df = normalize_visa_cal_table(df_pending, dates_range=dates_range)
        normalized_frames.append(normalized_df)

    if not normalized_frames:
        raise ValueError("No Visa Cal tables were loaded from the provided folder.")

    combined_normalized_df = pd.concat(normalized_frames, ignore_index=True)
    print(combined_normalized_df.head())
    return combined_normalized_df


def normalize_visa_cal_table(
    df_pending: pd.DataFrame, dates_range: tuple[str, str] | None = None
) -> pd.DataFrame:
    """End-to-end Visa Cal normalization story (you implement details)."""
    header_row_idx = detect_header_row_by_required_headers(
        df_pending,
        required_headers=VISA_CAL_REQUIRED_HEADERS,
    )
    normalized_df = apply_header_row(df_pending, header_row_idx)
    normalized_df = translate_columns(
        df=normalized_df,
        source_to_canonical_map=VISA_CAL_SOURCE_TO_CANONICAL_COLUMN_MAP,
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
        source_to_canonical_map=VISA_CAL_SOURCE_TO_CANONICAL_COLUMN_MAP,
    )
    normalized_df = attach_account_metadata(
        df=normalized_df,
        account_name=VISA_CAL_ACCOUNT_NAME,
    )
    return normalized_df


def normalize_ynab_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """Parse and normalize Visa Cal date column to YNAB format."""
    if not VISA_CAL_INPUT_DATE_FORMAT:
        raise NotImplementedError("Set VISA_CAL_INPUT_DATE_FORMAT before date normalization.")
    return normalize_date_column(
        df=df,
        date_column="Date",
        input_date_format=VISA_CAL_INPUT_DATE_FORMAT,
        output_date_format=YNAB_OUTPUT_DATE_FORMAT,
    )


if __name__ == "__main__":
    path_to_folder = r"C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\visa_cal"
    dates_range = ("01/01/2026", "01/03/2026")
    main(path_to_folder=path_to_folder, dates_range=dates_range)
