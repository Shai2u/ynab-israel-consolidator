"""Shared column mapping helpers for ETL prototypes."""

from __future__ import annotations

import pandas as pd


def translate_columns(
    df: pd.DataFrame,
    source_to_canonical_map: dict[str, str],
) -> pd.DataFrame:
    """Translate source column names to canonical names using a mapping.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe with source column names.
    source_to_canonical_map : dict[str, str]
        Mapping from source header names to canonical names.

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with translated columns.
    """
    translated_df = df.copy()
    translated_df.columns = translated_df.columns.map(source_to_canonical_map)
    return translated_df


def select_mapped_columns(
    df: pd.DataFrame,
    source_to_canonical_map: dict[str, str],
) -> pd.DataFrame:
    """Keep only mapped canonical columns that exist in the dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe after translation/normalization steps.
    source_to_canonical_map : dict[str, str]
        Mapping from source header names to canonical names.

    Returns
    -------
    pd.DataFrame
        Dataframe containing only mapped canonical columns present in ``df``.
    """
    keep_columns = [column for column in source_to_canonical_map.values() if column in df.columns]
    return df[keep_columns]
