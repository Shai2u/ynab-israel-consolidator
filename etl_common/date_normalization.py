"""Shared date normalization helpers for ETL prototypes."""

from __future__ import annotations

import pandas as pd


def normalize_date_column(
    df: pd.DataFrame,
    date_column: str,
    input_date_format: str,
    output_date_format: str,
) -> pd.DataFrame:
    """Parse, filter, and format a date column.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe containing a date column.
    date_column : str
        Date column name to normalize.
    input_date_format : str
        Input date format used for parsing.
    output_date_format : str
        Output date format used for final string formatting.

    Returns
    -------
    pd.DataFrame
        Dataframe with invalid date rows removed and normalized date strings.
    """
    normalized_df = df.copy()
    parsed_dates = pd.to_datetime(
        normalized_df[date_column],
        format=input_date_format,
        errors="coerce",
    )
    valid_mask = parsed_dates.notna()
    normalized_df = normalized_df.loc[valid_mask].copy()
    normalized_df[date_column] = parsed_dates.loc[valid_mask].dt.strftime(output_date_format)
    return normalized_df
