
from etl_sources.mizrachi_reader import load_mizrachi_tables
import pandas as pd


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
    

    # Header row detection
    # Detect header row in Mizrachi export via NaN-first-row signature.
    header_row_idx = detect_header_row_mizrachi_case(df_pending)
    df_pending.columns = df_pending.iloc[header_row_idx, :]
    df_pending = df_pending.iloc[header_row_idx+1:].copy().reset_index(drop=True)
    

    #  
# STEP: parse date
# STEP: split inflow/outflow
# TODO: handle installment rows


if __name__ == "__main__":
    path_to_folder = r'C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\bank_mizrachi'
    dates_range = ("01/01/2026", "01/03/2026")
    main(path_to_folder=path_to_folder, dates_range=dates_range)