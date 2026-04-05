"""Prototype pipeline for normalizing Mizrachi exports toward YNAB shape."""

# Imports
from etl_sources.mizrachi_reader import load_mizrachi_tables
from etl_sources.account_registry import attach_account_metadata
from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT
from etl_common.column_mapping import select_mapped_columns, translate_columns
from etl_common.date_utilities import normalize_date_column, filter_by_dates_range
from etl_common.header_detection import apply_header_row
from etl_sources.mizrachi_constants import (
    MIZRACHI_ACCOUNT_NAME,
    MIZRACHI_HEBREW_TO_CANONICAL_COLUMN_MAP,
    MIZRACHI_INPUT_DATE_FORMAT,
)

import pandas as pd

# Orchestration
def main(path_to_folder: str, dates_range: tuple[str, str] | None = None) -> None:
    """Run the Mizrachi prototype pipeline on loaded tables.

    Parameters
    ----------
    path_to_folder : str
        Folder containing Mizrachi source files.
    dates_range : tuple[str, str] | None, optional
        Optional date range hint for the run, by default None.
    """
    loaded_tables = load_mizrachi_tables(folder=path_to_folder, recursive=False)
    print(f"Loaded files: {len(loaded_tables)}")

    for table in loaded_tables:
        print(f"\nFile: {table.path.name} ({table.extension})")
        df_pending = table.dataframe
        print(df_pending.head())

    if dates_range:
        print(f"Requested date range: {dates_range[0]} -> {dates_range[1]}")

    df_pending = normalize_mizrachi_table(df_pending, dates_range=dates_range)

    # Prototype next steps:
    # - Split inflow/outflow to YNAB-compatible amount fields.
    # - Add installment-specific handling.
    return df_pending
# Pipeline steps
# End-to-end normalization story
def normalize_mizrachi_table(
    df_pending: pd.DataFrame, dates_range: tuple[str, str] | None = None
) -> pd.DataFrame:
    """Normalize one raw Mizrachi dataframe to canonical shape.

    Parameters
    ----------
    df_pending : pd.DataFrame
        Raw dataframe as loaded from the Mizrachi source.
    dates_range : tuple[str, str] | None, optional
        Optional inclusive date range filter (start_date, end_date) using
        ``YNAB_OUTPUT_DATE_FORMAT``, by default None.

    Returns
    -------
    pd.DataFrame
        Normalized dataframe with mapped columns and formatted date field.
    """
    header_row_idx = detect_mizrachi_header_row(df_pending)
    normalized_df = apply_header_row(df_pending, header_row_idx)
    normalized_df = translate_columns(df=normalized_df, source_to_canonical_map=MIZRACHI_HEBREW_TO_CANONICAL_COLUMN_MAP)
    normalized_df = normalize_ynab_date_column(normalized_df)
    normalized_df = filter_by_dates_range(normalized_df, date_column="Date", dates_range=dates_range, output_date_format=YNAB_OUTPUT_DATE_FORMAT)
    normalized_df = select_mapped_columns(df=normalized_df, source_to_canonical_map=MIZRACHI_HEBREW_TO_CANONICAL_COLUMN_MAP)
    normalized_df["Memo"] = ""
    normalized_df = attach_account_metadata(df=normalized_df, account_name=MIZRACHI_ACCOUNT_NAME)
    return normalized_df


# Header detection
def detect_mizrachi_header_row(
    df: pd.DataFrame,
    default_row: int = 3,
    probe_rows: int = 1,
) -> int:
    """Detect header row index using Mizrachi-specific heuristics.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe before header normalization.
    default_row : int, optional
        Fallback header row index when no signal is found, by default 3.
    probe_rows : int, optional
        Number of top rows to inspect for the NaN signature, by default 1.

    Returns
    -------
    int
        Detected header row index.
    """
    if df.empty:
        return default_row
    # Step 1: columns that look like your Mizrachi signature
    candidate_cols = [
        col for col in df.columns
        if df[col].iloc[:probe_rows].isna().any()
    ]
    # Step 2: find first non-null row in first matching column
    for col in candidate_cols:
        first_valid = df[col].first_valid_index()  # returns None if all null
        if first_valid is not None:
            return int(first_valid)
    return default_row


def detect_header_row_mizrachi_case(
    df: pd.DataFrame,
    default_row: int = 3,
    probe_rows: int = 1,
) -> int:
    """Backward-compatible alias for ``detect_mizrachi_header_row``.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe before header normalization.
    default_row : int, optional
        Fallback header row index, by default 3.
    probe_rows : int, optional
        Number of rows to probe for signature detection, by default 1.

    Returns
    -------
    int
        Detected header row index.
    """
    return detect_mizrachi_header_row(df, default_row=default_row, probe_rows=probe_rows)




# Backward-compatible alias
def apply_detected_header(df: pd.DataFrame, header_row_idx: int) -> pd.DataFrame:
    """Backward-compatible alias for ``apply_header_row``.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing the header row.
    header_row_idx : int
        Row index to apply as header.

    Returns
    -------
    pd.DataFrame
        Header-normalized dataframe.
    """
    return apply_header_row(df, header_row_idx)


# Date parsing
def parse_mizrachi_dates(
    raw_date_col: pd.Series, date_format: str = MIZRACHI_INPUT_DATE_FORMAT
) -> pd.Series:
    """Parse Mizrachi date values into pandas datetimes.

    Parameters
    ----------
    raw_date_col : pd.Series
        Raw date column values (may include non-date noise).
    date_format : str, optional
        Expected Mizrachi date format, by default ``MIZRACHI_INPUT_DATE_FORMAT``.

    Returns
    -------
    pd.Series
        Datetime series where invalid values are ``NaT``.
    """
    # Clean raw values
    s = raw_date_col.astype(str).str.strip()
    s = s.replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    parsed = pd.to_datetime(s, format=date_format, errors="coerce")
    # Second pass (only failed rows): dd/mm/yyyy
    missing = parsed.isna()
    parsed.loc[missing] = pd.to_datetime(
        s.loc[missing],
        format=date_format,
        errors="coerce",
    )
    return parsed


# Date normalization
def normalize_ynab_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize ``Date`` column to YNAB output format and drop invalid rows.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe containing a ``Date`` column after header/column normalization.

    Returns
    -------
    pd.DataFrame
        Dataframe with valid dates formatted as ``YNAB_OUTPUT_DATE_FORMAT``.
    """
    if not MIZRACHI_INPUT_DATE_FORMAT:
        raise NotImplementedError("Set MIZRACHI_INPUT_DATE_FORMAT before date normalization.")
    return normalize_date_column(
        df=df,
        date_column="Date",
        input_date_format=MIZRACHI_INPUT_DATE_FORMAT,
        output_date_format=YNAB_OUTPUT_DATE_FORMAT,
    )





# Helpers
def _dedupe_column_names(names: list[str]) -> list[str]:
    """Deduplicate column names by appending numeric suffixes.

    Parameters
    ----------
    names : list[str]
        Column names that may contain duplicates.

    Returns
    -------
    list[str]
        Stable list where duplicate names become ``name_2``, ``name_3``, etc.
    """
    seen_counts: dict[str, int] = {}
    deduped: list[str] = []

    for name in names:
        count = seen_counts.get(name, 0) + 1
        seen_counts[name] = count
        deduped.append(name if count == 1 else f"{name}_{count}")

    return deduped


# Entry point
if __name__ == "__main__":
    path_to_folder = r'C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\bank_mizrachi'
    dates_range = ("01/01/2026", "01/03/2026")
    main(path_to_folder=path_to_folder, dates_range=dates_range)