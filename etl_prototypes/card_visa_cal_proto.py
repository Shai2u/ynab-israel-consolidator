"""Prototype pipeline scaffold for Mastercard 4779 normalization."""

from __future__ import annotations

import pandas as pd

from etl_common.column_mapping import select_mapped_columns, translate_columns
from etl_common.date_utilities import filter_by_dates_range, normalize_date_column
from etl_common.header_detection import apply_header_row, detect_header_row_by_required_headers
from etl_sources.account_registry import attach_account_metadata
from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT
from etl_sources.visa_cal_constants import (
    VISA_CAL_INPUT_DATE_FORMAT,
    VISA_CAL_LAST4_TO_ACCOUNT_NAME,
    VISA_CAL_REQUIRED_HEADERS,
    VISA_CAL_SOURCE_TO_CANONICAL_COLUMN_MAP,
    VISA_CAL_DICT_COLS,
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


def detect_account_name(df_pending: pd.DataFrame) -> str:
    """Detect the account name from the dataframe."""
    return df_pending.columns[0][-4:]


def resolve_visa_cal_account_name(account_last4: str) -> str:
    """Resolve Visa Cal account name from detected last-4 digits."""
    account_name = VISA_CAL_LAST4_TO_ACCOUNT_NAME.get(account_last4)
    if account_name is None:
        raise ValueError(
            f"Unsupported Visa Cal account suffix '{account_last4}'. "
            f"Expected one of: {sorted(VISA_CAL_LAST4_TO_ACCOUNT_NAME.keys())}"
        )
    return account_name

def memo_visa_cal_table(df: pd.DataFrame, dict_cols: dict[str, str]) -> pd.DataFrame:
    """Memo the Visa Cal table."""
    cols = list(dict_cols.keys())
    for col in cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda p: str(p).replace('nan', ''))
            df[col] = df[col].apply(lambda p: f"{dict_cols[col]}:{str(p).strip()}, " if str(p).strip() != '' else '')
    df['Memo'] = ''
    for col in cols:
        if col in df.columns:
            df['Memo'] += df[col]
    df = df.drop(columns=[c for c in cols if c in df.columns])
    return df

def normalize_visa_cal_table(
    df_pending: pd.DataFrame, dates_range: tuple[str, str] | None = None
) -> pd.DataFrame:
    """End-to-end Visa Cal normalization story (you implement details)."""
    account_last4 = detect_account_name(df_pending)
    account_name = resolve_visa_cal_account_name(account_last4)
    header_row_idx = detect_header_row_by_required_headers(
        df_pending,
        required_headers=VISA_CAL_REQUIRED_HEADERS,
        default_row_idx=0,
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
    normalized_df = coalesce_amount_columns(normalized_df)
    normalized_df = derive_inflow_outflow_from_amount(normalized_df)
    normalized_df = memo_visa_cal_table(normalized_df, dict_cols=VISA_CAL_DICT_COLS)
    normalized_df = attach_account_metadata(
        df=normalized_df,
        account_name=account_name,
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


def coalesce_amount_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Merge the billing-cycle export's split amount columns into 'Amount'.

    That export variant has no single amount column: 'Amount_billed' (סכום
    חיוב) is blank for a transaction still pending, in which case
    'Amount_transaction' (סכום עסקה) is the only amount available. Prefer
    the billed amount and fall back to the transaction amount.
    """
    if 'Amount' in df.columns:
        return df
    has_billed = 'Amount_billed' in df.columns
    has_transaction = 'Amount_transaction' in df.columns
    if not has_billed and not has_transaction:
        return df

    combined_df = df.copy()
    billed = combined_df.pop('Amount_billed') if has_billed else None
    transaction = combined_df.pop('Amount_transaction') if has_transaction else None
    combined_df['Amount'] = billed.fillna(transaction) if has_billed and has_transaction else (
        billed if has_billed else transaction
    )
    return combined_df


def derive_inflow_outflow_from_amount(df: pd.DataFrame) -> pd.DataFrame:
    """Derive Inflow/Outflow from Amount based on minus-sign rule."""
    if "Amount" not in df.columns:
        raise ValueError("Expected 'Amount' column after mapping.")

    normalized_df = df.copy()
    amount_str = normalized_df["Amount"].astype(str).str.strip()

    # Keep digits, decimal point, and minus sign for numeric conversion.
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


if __name__ == "__main__":
    path_to_folder = r"C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\visa_cal"
    dates_range = ("01/01/2026", "01/03/2026")
    main(path_to_folder=path_to_folder, dates_range=dates_range)
