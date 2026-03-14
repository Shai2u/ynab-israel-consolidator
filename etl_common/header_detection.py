import pandas as pd

def detect_header_row_by_required_headers(
    df: pd.DataFrame,
    required_headers: set[str],
    default_row_idx: int = 0,
) -> int:

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

def apply_header_row(df: pd.DataFrame, header_row_idx: int) -> pd.DataFrame:
    """Promote detected header row and return data rows below it."""
    if not 0 <= header_row_idx < len(df):
        raise ValueError(f"header_row_idx out of range: {header_row_idx}")

    with_header_df = df.copy()
    with_header_df.columns = with_header_df.iloc[header_row_idx, :]
    return with_header_df.iloc[header_row_idx + 1 :].reset_index(drop=True)