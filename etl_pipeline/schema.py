"""Canonical output schema contract for the consolidated master DataFrame.

Every source adapter (bank or credit card prototype) must produce exactly
these columns before it is eligible for consolidation.  Any column outside
this set will be dropped; any column missing will raise during validation.
"""

from __future__ import annotations

import pandas as pd


# The ordered list of columns every normalized source must expose.
CANONICAL_COLUMNS: list[str] = [
    "Date",       # dd/mm/YYYY string
    "Payee",      # merchant / counterparty name
    "Memo",       # optional free-text detail (may be empty string, not NaN)
    "Inflow",     # positive amount received  (0.0 if none)
    "Outflow",    # positive amount spent     (0.0 if none)
    "Account",    # canonical account name from ACCOUNT_REGISTRY.md
    "Ownership",  # canonical ownership label from ACCOUNT_REGISTRY.md
]


def validate_source_df(df: pd.DataFrame, source_name: str) -> None:
    """Raise if ``df`` is missing any column required by the canonical schema.

    Parameters
    ----------
    df : pd.DataFrame
        Normalized DataFrame produced by a source adapter.
    source_name : str
        Human-readable label used in error messages (e.g. ``"Mizrachi"``).

    Raises
    ------
    ValueError
        If one or more required columns are absent.
    """
    missing = [col for col in CANONICAL_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(
            f"[{source_name}] missing canonical columns: {missing}. "
            "Fix the source adapter before consolidating."
        )
