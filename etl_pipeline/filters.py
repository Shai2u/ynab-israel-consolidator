"""Post-consolidation filters for the master DataFrame.

These functions operate on an already-built master DataFrame.
They are independent of how the data was loaded or normalized.
"""

from __future__ import annotations

import pandas as pd

from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT


def filter_by_account(
    master_df: pd.DataFrame,
    accounts: str | list[str],
) -> pd.DataFrame:
    """Keep only rows belonging to the given account(s).

    Parameters
    ----------
    master_df : pd.DataFrame
        Consolidated master DataFrame.
    accounts : str | list[str]
        One account name or a list of account names to keep.
        Names must match the ``Account`` column exactly.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame with reset index.

    Examples
    --------
    >>> filter_by_account(master_df, "Mizrachi")
    >>> filter_by_account(master_df, ["Mizrachi", "Bank Leumi"])
    """
    if isinstance(accounts, str):
        accounts = [accounts]
    mask = master_df["Account"].isin(accounts)
    return master_df[mask].reset_index(drop=True)


def filter_by_date_range(
    master_df: pd.DataFrame,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Keep only rows whose ``Date`` falls within the inclusive range.

    Parameters
    ----------
    master_df : pd.DataFrame
        Consolidated master DataFrame. ``Date`` column must be in
        ``dd/mm/YYYY`` string format.
    start_date : str
        Earliest date to include (``dd/mm/YYYY``).
    end_date : str
        Latest date to include (``dd/mm/YYYY``).

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame with reset index.

    Examples
    --------
    >>> filter_by_date_range(master_df, "01/01/2026", "31/03/2026")
    """
    dates = pd.to_datetime(master_df["Date"], format=YNAB_OUTPUT_DATE_FORMAT, errors="coerce")
    start = pd.to_datetime(start_date, format=YNAB_OUTPUT_DATE_FORMAT)
    end = pd.to_datetime(end_date, format=YNAB_OUTPUT_DATE_FORMAT)
    mask = (dates >= start) & (dates <= end)
    return master_df[mask].reset_index(drop=True)


def filter_by_source_type(
    master_df: pd.DataFrame,
    source_type: str,
) -> pd.DataFrame:
    """Keep only rows of a given source type (``'bank_card'`` or ``'ynab'``).

    Parameters
    ----------
    master_df : pd.DataFrame
        Consolidated master DataFrame.
    source_type : str
        ``'bank_card'`` or ``'ynab'``.

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame with reset index.
    """
    mask = master_df["source_type"] == source_type
    return master_df[mask].reset_index(drop=True)
