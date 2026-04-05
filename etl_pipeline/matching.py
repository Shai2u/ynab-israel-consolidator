"""Deterministic fingerprint matching between bank/card and YNAB rows.

This is Step 6 (exact matching) of the product roadmap.

How it works
------------
A fingerprint is a string key built from the columns that must be identical
for two rows to be considered the same transaction:
    Date + Inflow + Outflow + Account

For each fingerprint that appears in both ``bank_card`` and ``ynab`` rows,
all rows carrying that fingerprint are marked ``"matched"``.

Limitations at this stage
--------------------------
- YNAB account names often differ from bank/card canonical names
  (e.g. YNAB ``"Poalim"`` vs bank ``"Bank Hapoalim"``).  This means
  true matches on different-name accounts will show as ``"unmatched"``
  until an account-name reconciliation map is added (future step).
- Amounts must be identical to the cent.  Rounding differences or
  installment splits will not match (future: easement window).
- Payee and Memo are intentionally excluded from the fingerprint —
  they are free-text and unreliable for exact matching.
"""

from __future__ import annotations

import pandas as pd

from etl_pipeline.schema import SOURCE_TYPE_BANK_CARD, SOURCE_TYPE_YNAB


# ---------------------------------------------------------------------------
# Fingerprint
# ---------------------------------------------------------------------------

def add_fingerprint(df: pd.DataFrame) -> pd.DataFrame:
    """Add a ``fingerprint`` column derived from Date, Inflow, Outflow, Account.

    Parameters
    ----------
    df : pd.DataFrame
        Master or filtered DataFrame containing the canonical columns.

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with an added ``fingerprint`` string column.
    """
    result = df.copy()
    result["fingerprint"] = (
        result["Date"].astype(str).str.strip()
        + "|"
        + result["Inflow"].round(2).astype(str)
        + "|"
        + result["Outflow"].round(2).astype(str)
        + "|"
        + result["Account"].astype(str).str.strip()
    )
    return result


# ---------------------------------------------------------------------------
# Match status
# ---------------------------------------------------------------------------

def add_match_status(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``fingerprint`` and ``match_status`` columns to the DataFrame.

    A row is ``"matched"`` when its fingerprint appears in **both**
    ``bank_card`` and ``ynab`` rows within ``df``.

    Parameters
    ----------
    df : pd.DataFrame
        Master or filtered DataFrame. Must contain ``source_type``.

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with ``fingerprint`` and ``match_status`` columns added.
    """
    result = add_fingerprint(df)

    # Find fingerprints that have at least one bank_card AND one ynab row.
    source_sets = result.groupby("fingerprint")["source_type"].apply(set)
    matched_fingerprints = source_sets[
        source_sets.apply(lambda s: SOURCE_TYPE_BANK_CARD in s and SOURCE_TYPE_YNAB in s)
    ].index

    result["match_status"] = result["fingerprint"].isin(matched_fingerprints).map(
        {True: "matched", False: "unmatched"}
    )
    return result


# ---------------------------------------------------------------------------
# Score
# ---------------------------------------------------------------------------

def compute_match_score(df: pd.DataFrame) -> dict:
    """Compute match statistics for the bank/card rows in ``df``.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame that already has a ``match_status`` column
        (i.e. output of :func:`add_match_status`).

    Returns
    -------
    dict
        ``bank_card_total``   – total bank/card rows
        ``bank_card_matched`` – bank/card rows with a YNAB pair
        ``score_pct``         – match rate as a percentage (0–100, 1 decimal)
        ``ynab_total``        – total YNAB rows
        ``ynab_matched``      – YNAB rows with a bank/card pair
    """
    bank_card = df[df["source_type"] == SOURCE_TYPE_BANK_CARD]
    ynab = df[df["source_type"] == SOURCE_TYPE_YNAB]

    bank_card_matched = (bank_card["match_status"] == "matched").sum()
    ynab_matched = (ynab["match_status"] == "matched").sum()

    total_bank_card = len(bank_card)
    score_pct = round(bank_card_matched / total_bank_card * 100, 1) if total_bank_card else 0.0

    return {
        "bank_card_total": total_bank_card,
        "bank_card_matched": int(bank_card_matched),
        "score_pct": score_pct,
        "ynab_total": len(ynab),
        "ynab_matched": int(ynab_matched),
    }


def print_match_summary(df: pd.DataFrame) -> None:
    """Print a human-readable match summary for ``df``.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame that already has a ``match_status`` column.
    """
    s = compute_match_score(df)
    print(f"Match score:  {s['score_pct']}%  "
          f"({s['bank_card_matched']} / {s['bank_card_total']} bank/card rows matched)")
    print(f"YNAB rows:    {s['ynab_matched']} matched / {s['ynab_total']} total")
    unmatched_bank = s['bank_card_total'] - s['bank_card_matched']
    unmatched_ynab = s['ynab_total'] - s['ynab_matched']
    if unmatched_bank:
        print(f"  ↳ {unmatched_bank} bank/card rows have no YNAB pair")
    if unmatched_ynab:
        print(f"  ↳ {unmatched_ynab} YNAB rows have no bank/card pair")
