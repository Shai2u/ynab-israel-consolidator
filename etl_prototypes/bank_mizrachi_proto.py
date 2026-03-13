
from etl_sources.mizrachi_reader import load_mizrachi_tables
from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT
from etl_sources.mizrachi_constants import (
    MIZRACHI_HEBREW_TO_CANONICAL_COLUMN_MAP,
    MIZRACHI_INPUT_DATE_FORMAT,
)
import pandas as pd


def _dedupe_column_names(names: list[str]) -> list[str]:
    seen_counts: dict[str, int] = {}
    deduped: list[str] = []

    for name in names:
        count = seen_counts.get(name, 0) + 1
        seen_counts[name] = count
        deduped.append(name if count == 1 else f"{name}_{count}")

    return deduped


def parse_mizrachi_dates(
    raw_date_col: pd.Series, date_format: str = MIZRACHI_INPUT_DATE_FORMAT
) -> pd.Series:
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


def apply_detected_header(df: pd.DataFrame, header_row_idx: int) -> pd.DataFrame:
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


def detect_header_row_mizrachi_case(
    df: pd.DataFrame,
    default_row: int = 3,
    probe_rows: int = 1,
) -> int:
    """
    Heuristic:
    1) Find first column that has NaN in the first `probe_rows`.
    2) In that column, return first non-null row index.
    3) If no signal found, return default_row.
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

def main(path_to_folder: str, dates_range: tuple[str, str] | None = None) -> None:
    loaded_tables = load_mizrachi_tables(folder=path_to_folder, recursive=False)
    print(f"Loaded files: {len(loaded_tables)}")

    for table in loaded_tables:
        print(f"\nFile: {table.path.name} ({table.extension})")
        df_pending = table.dataframe
        print(df_pending.head())

    if dates_range:
        print(f"Requested date range: {dates_range[0]} -> {dates_range[1]}")
    

    # Detect header row in Mizrachi export via NaN-first-row signature.
    header_row_idx = detect_header_row_mizrachi_case(df_pending)

    df_pending = apply_detected_header(df_pending, header_row_idx)

    # find last footer of dataframe  using date column (non date values) or     
    # dataframe has been aligned to the header row

    # translating columns names using global mapping (for this project)
    df_pending.columns = df_pending.columns.map(MIZRACHI_HEBREW_TO_CANONICAL_COLUMN_MAP)
    
    # Align dates to dd/mm/YYYY format + drop rows with invalid dates
    parsed_dates = parse_mizrachi_dates(df_pending["Date"])
    # 2) Keep only valid date rows
    valid_mask = parsed_dates.notna()
    df_pending = df_pending.loc[valid_mask].copy()
    # 3) Format to dd/mm/yyyy
    df_pending["Date"] = parsed_dates.loc[valid_mask].dt.strftime(YNAB_OUTPUT_DATE_FORMAT)

    # Keep only the mapped columns if exist
    df_pending = df_pending[
        [
            column
            for column in MIZRACHI_HEBREW_TO_CANONICAL_COLUMN_MAP.values()
            if column in df_pending.columns
        ]
    ]


    #  
# STEP: parse date
# STEP: split inflow/outflow
# TODO: handle installment rows


if __name__ == "__main__":
    path_to_folder = r'C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\bank_mizrachi'
    dates_range = ("01/01/2026", "01/03/2026")
    main(path_to_folder=path_to_folder, dates_range=dates_range)