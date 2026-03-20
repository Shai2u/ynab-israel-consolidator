"""Global account and ownership registry utilities."""

from __future__ import annotations

import pandas as pd


# Canonical ownership labels.
OWNERSHIP_SHAI_PRIVATE = "Shai (Private)"
OWNERSHIP_SHAI_NIRIT_JOINT = "Shai & Nirit (Joint)"


# Account -> ownership mapping (authoritative source aligned with ACCOUNT_REGISTRY.md).
ACCOUNT_TO_OWNERSHIP: dict[str, str] = {
    # Banks
    "Bank Leumi": OWNERSHIP_SHAI_PRIVATE,
    "Bank Hapoalim": OWNERSHIP_SHAI_PRIVATE,
    "Mizrachi": OWNERSHIP_SHAI_NIRIT_JOINT,
    # Credit cards
    "Max Uniq": OWNERSHIP_SHAI_NIRIT_JOINT,
    "Isracard 4054": OWNERSHIP_SHAI_NIRIT_JOINT,
    "Mastercard 4779": OWNERSHIP_SHAI_PRIVATE,
    "Mastercard 7353": OWNERSHIP_SHAI_PRIVATE,
}

# Account -> linked settlement bank mapping.
# For bank accounts, the linked settlement bank is the account itself.
ACCOUNT_TO_LINKED_BANK: dict[str, str] = {
    # Banks
    "Bank Leumi": "Bank Leumi",
    "Bank Hapoalim": "Bank Hapoalim",
    "Mizrachi": "Mizrachi",
    # Credit cards
    "Max Uniq": "Mizrachi",
    "Isracard 4054": "Mizrachi",
    "Mastercard 4779": "Bank Hapoalim",
    "Mastercard 7353": "Bank Leumi",
}


def resolve_ownership(account_name: str) -> str:
    """Resolve canonical ownership label for a known account.

    Parameters
    ----------
    account_name : str
        Canonical account name.

    Returns
    -------
    str
        Canonical ownership label for ``account_name``.

    Raises
    ------
    ValueError
        If the account is unknown in the registry.
    """
    ownership = ACCOUNT_TO_OWNERSHIP.get(account_name)
    if ownership is None:
        raise ValueError(
            f"Unknown account '{account_name}'. Add it to ACCOUNT_REGISTRY.md and ACCOUNT_TO_OWNERSHIP."
        )
    return ownership


def resolve_linked_bank_account(account_name: str) -> str:
    """Resolve linked settlement bank account for a known account.

    Parameters
    ----------
    account_name : str
        Canonical account name.

    Returns
    -------
    str
        Canonical linked settlement bank account.

    Raises
    ------
    ValueError
        If the account has no linked bank mapping in the registry.
    """
    linked_bank = ACCOUNT_TO_LINKED_BANK.get(account_name)
    if linked_bank is None:
        raise ValueError(
            f"Unknown linked bank for account '{account_name}'. "
            "Add it to ACCOUNT_REGISTRY.md and ACCOUNT_TO_LINKED_BANK."
        )
    return linked_bank


def attach_account_metadata(df: pd.DataFrame, account_name: str) -> pd.DataFrame:
    """Attach ``Account`` and ``Ownership`` columns to normalized data.

    Parameters
    ----------
    df : pd.DataFrame
        Normalized dataframe to enrich.
    account_name : str
        Canonical account name used to resolve ownership.

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with added ``Account`` and ``Ownership`` columns.
    """
    enriched_df = df.copy()
    enriched_df["Account"] = account_name
    enriched_df["Ownership"] = resolve_ownership(account_name)
    return enriched_df
