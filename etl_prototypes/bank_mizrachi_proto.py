"""Prototype pipeline for normalizing Mizrachi exports toward YNAB shape."""

# Imports
from etl_sources.mizrachi_reader import load_mizrachi_tables
from etl_sources.account_registry import attach_account_metadata
from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT
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

    df_pending = normalize_mizrachi_table(df_pending)

    # Prototype next steps:
    # - Split inflow/outflow to YNAB-compatible amount fields.
    # - Add installment-specific handling.

# Pipeline steps
# End-to-end normalization story
def normalize_mizrachi_table(df_pending: pd.DataFrame) -> pd.DataFrame:
    """Normalize one raw Mizrachi dataframe to canonical shape.

    Parameters
    ----------
    df_pending : pd.DataFrame
        Raw dataframe as loaded from the Mizrachi source.

    Returns
    -------
    pd.DataFrame
        Normalized dataframe with mapped columns and formatted date field.
    """
    header_row_idx = detect_mizrachi_header_row(df_pending)
    normalized_df = apply_header_row(df_pending, header_row_idx)
    normalized_df = translate_mizrachi_columns(normalized_df)
    normalized_df = normalize_ynab_date_column(normalized_df)
    normalized_df = select_mapped_output_columns(normalized_df)
    normalized_df = add_mizrachi_account_metadata(normalized_df)
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


# Header application
def apply_header_row(df: pd.DataFrame, header_row_idx: int) -> pd.DataFrame:
    """Apply a detected header row and return data rows below it.

    Parameters
    ----------
    df : pd.DataFrame
        Input dataframe containing the header row inside data.
    header_row_idx : int
        Row index that should become the dataframe columns.

    Returns
    -------
    pd.DataFrame
        Dataframe with normalized/deduplicated columns and reset index.

    Raises
    ------
    ValueError
        If ``header_row_idx`` is outside dataframe bounds.
    """
    if df.empty:
        return df.copy()

    if header_row_idx < 0 or header_row_idx >= len(df):
        raise ValueError(
            f"Detected header_row_idx {header_row_idx} is out of bounds for dataframe with {len(df)} rows."
        )

    raw_header = df.iloc[header_row_idx, :]
    cleaned_header = []
    for col_idx, value in enumerate(raw_header):
        if pd.isna(value):
            cleaned_header.append(f"unnamed_{col_idx}")
            continue

        header_name = str(value).strip()
        cleaned_header.append(header_name or f"unnamed_{col_idx}")

    normalized_columns = _dedupe_column_names(cleaned_header)
    normalized_df = df.iloc[header_row_idx + 1 :].copy().reset_index(drop=True)
    normalized_df.columns = normalized_columns
    return normalized_df


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


# Column translation
def translate_mizrachi_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Translate Mizrachi Hebrew column names to canonical names.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with source column names.

    Returns
    -------
    pd.DataFrame
        Dataframe with translated column names.
    """
    translated_df = df.copy()
    translated_df.columns = translated_df.columns.map(MIZRACHI_HEBREW_TO_CANONICAL_COLUMN_MAP)
    return translated_df


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
    normalized_df = df.copy()
    parsed_dates = parse_mizrachi_dates(normalized_df["Date"])
    valid_mask = parsed_dates.notna()
    normalized_df = normalized_df.loc[valid_mask].copy()
    normalized_df["Date"] = parsed_dates.loc[valid_mask].dt.strftime(YNAB_OUTPUT_DATE_FORMAT)
    return normalized_df


# Output shaping
def select_mapped_output_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only mapped canonical output columns that exist.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe after normalization steps.

    Returns
    -------
    pd.DataFrame
        Dataframe limited to mapped output columns present in ``df``.
    """
    keep_columns = [
        column
        for column in MIZRACHI_HEBREW_TO_CANONICAL_COLUMN_MAP.values()
        if column in df.columns
    ]
    return df[keep_columns]


# Account metadata
def add_mizrachi_account_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Attach canonical account and ownership columns for Mizrachi source.

    Parameters
    ----------
    df : pd.DataFrame
        Normalized dataframe from Mizrachi pipeline.

    Returns
    -------
    pd.DataFrame
        Dataframe enriched with ``Account`` and ``Ownership``.
    """
    return attach_account_metadata(df=df, account_name=MIZRACHI_ACCOUNT_NAME)

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