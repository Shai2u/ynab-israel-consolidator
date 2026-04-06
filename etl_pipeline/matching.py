"""Deterministic fingerprint matching between bank/card and YNAB rows.

This implements a cascading pyramid matcher (Steps 6–8 of the product roadmap).

Pyramid levels
--------------
Each level tries to match only the rows that the previous level left unmatched.
Earlier levels make the strongest claim (exact); later levels relax tolerances.

    Level 1  exact        – Date, Inflow, Outflow, Account all identical
    Level 2  1_day        – Date ±1 day, amounts exact
    Level 3  2_day        – Date ±2 days, amounts exact
    Level 4  1_day_1nis   – Date ±1 day, amounts within 1 NIS
    Level 5  2_day_1nis   – Date ±2 days, amounts within 1 NIS

Matching is one-to-one and greedy: for each bank/card row the best available
YNAB candidate is chosen (lowest combined date + amount distance).
Once a row is matched it is locked and unavailable to later levels.

Limitations
-----------
- YNAB account names may differ from bank/card names (e.g. ``"Poalim"`` vs
  ``"Bank Hapoalim"``), causing real pairs to show as unmatched until an
  account-name reconciliation map is added (future step).
- Payee and Memo are intentionally excluded — they are free-text and
  unreliable for deterministic matching.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT
from etl_pipeline.schema import SOURCE_TYPE_BANK_CARD, SOURCE_TYPE_YNAB


# ---------------------------------------------------------------------------
# Match level definition
# ---------------------------------------------------------------------------

@dataclass
class MatchLevel:
    """One tier of the matching pyramid."""

    name: str
    date_tolerance: int    # max allowed days gap between bank and YNAB date
    amount_tolerance: float  # max allowed NIS difference on Inflow and Outflow


DEFAULT_LEVELS: list[MatchLevel] = [
    MatchLevel(name="exact",      date_tolerance=0, amount_tolerance=0.0),
    MatchLevel(name="1_day",      date_tolerance=1, amount_tolerance=0.0),
    MatchLevel(name="2_day",      date_tolerance=2, amount_tolerance=0.0),
    MatchLevel(name="1_day_1nis", date_tolerance=1, amount_tolerance=1.0),
    MatchLevel(name="2_day_1nis", date_tolerance=2, amount_tolerance=1.0),
]


# ---------------------------------------------------------------------------
# Cascade matcher
# ---------------------------------------------------------------------------

def run_cascade_matching(
    df: pd.DataFrame,
    levels: list[MatchLevel] | None = None,
) -> pd.DataFrame:
    """Run the full matching pyramid on ``df``.

    Each level only processes rows still marked ``"unmatched"`` by the
    previous level.  Adds ``match_status`` and ``match_level`` columns.

    Parameters
    ----------
    df : pd.DataFrame
        Master or filtered DataFrame containing canonical columns.
        Must include ``source_type``.
    levels : list[MatchLevel] | None, optional
        Pyramid levels to run, by default :data:`DEFAULT_LEVELS`.

    Returns
    -------
    pd.DataFrame
        Copy of ``df`` with ``match_status`` (``"matched"`` / ``"unmatched"``)
        and ``match_level`` (level name, or ``""`` if unmatched) columns.
    """
    if levels is None:
        levels = DEFAULT_LEVELS

    result = df.copy()
    result["match_status"] = "unmatched"
    result["match_level"] = ""

    # Pre-parse dates once for the whole DataFrame.
    result["_date_parsed"] = pd.to_datetime(
        result["Date"], format=YNAB_OUTPUT_DATE_FORMAT, errors="coerce"
    )

    for level in levels:
        unmatched_mask = result["match_status"] == "unmatched"
        bank_idx = result.index[unmatched_mask & (result["source_type"] == SOURCE_TYPE_BANK_CARD)]
        ynab_idx = result.index[unmatched_mask & (result["source_type"] == SOURCE_TYPE_YNAB)]

        if bank_idx.empty or ynab_idx.empty:
            break

        pairs = _find_pairs(result, bank_idx, ynab_idx, level)

        for b_idx, y_idx in pairs:
            result.loc[b_idx, "match_status"] = "matched"
            result.loc[b_idx, "match_level"] = level.name
            result.loc[y_idx, "match_status"] = "matched"
            result.loc[y_idx, "match_level"] = level.name

    result = result.drop(columns=["_date_parsed"])
    return result


def _find_pairs(
    df: pd.DataFrame,
    bank_idx: pd.Index,
    ynab_idx: pd.Index,
    level: MatchLevel,
) -> list[tuple]:
    """Greedily match bank/card rows to YNAB rows within the given tolerances.

    For each bank row, the best YNAB candidate is the one with the smallest
    combined (date_diff + inflow_diff + outflow_diff).  Each YNAB row can
    only be claimed once.
    """
    pairs: list[tuple] = []
    claimed_ynab: set = set()

    for b_idx in bank_idx:
        b_row = df.loc[b_idx]
        b_date = b_row["_date_parsed"]
        b_account = str(b_row["Account"]).strip()

        best_score = None
        best_y_idx = None

        for y_idx in ynab_idx:
            if y_idx in claimed_ynab:
                continue

            y_row = df.loc[y_idx]

            # Account must match exactly (relaxable in a future step).
            if str(y_row["Account"]).strip() != b_account:
                continue

            date_diff = abs((y_row["_date_parsed"] - b_date).days)
            if date_diff > level.date_tolerance:
                continue

            inflow_diff = abs(float(y_row["Inflow"]) - float(b_row["Inflow"]))
            outflow_diff = abs(float(y_row["Outflow"]) - float(b_row["Outflow"]))
            if inflow_diff > level.amount_tolerance or outflow_diff > level.amount_tolerance:
                continue

            score = date_diff + inflow_diff + outflow_diff
            if best_score is None or score < best_score:
                best_score = score
                best_y_idx = y_idx

        if best_y_idx is not None:
            pairs.append((b_idx, best_y_idx))
            claimed_ynab.add(best_y_idx)

    return pairs


# ---------------------------------------------------------------------------
# Legacy exact-only helpers (kept for backward compatibility)
# ---------------------------------------------------------------------------

def add_fingerprint(df: pd.DataFrame) -> pd.DataFrame:
    """Add an exact ``fingerprint`` string column (Date|Inflow|Outflow|Account)."""
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


def add_match_status(df: pd.DataFrame) -> pd.DataFrame:
    """Exact-only match (Level 1 only).  Use :func:`run_cascade_matching` for the full pyramid."""
    return run_cascade_matching(df, levels=[DEFAULT_LEVELS[0]])


# ---------------------------------------------------------------------------
# Score and summary
# ---------------------------------------------------------------------------

def compute_match_score(df: pd.DataFrame) -> dict:
    """Compute match statistics broken down by level.

    Parameters
    ----------
    df : pd.DataFrame
        Output of :func:`run_cascade_matching` or :func:`add_match_status`.

    Returns
    -------
    dict
        ``bank_card_total``, ``bank_card_matched``, ``score_pct``,
        ``ynab_total``, ``ynab_matched``, ``by_level`` (counts per level).
    """
    bank_card = df[df["source_type"] == SOURCE_TYPE_BANK_CARD]
    ynab = df[df["source_type"] == SOURCE_TYPE_YNAB]

    bank_card_matched = (bank_card["match_status"] == "matched").sum()
    ynab_matched = (ynab["match_status"] == "matched").sum()
    total_bank_card = len(bank_card)
    score_pct = round(bank_card_matched / total_bank_card * 100, 1) if total_bank_card else 0.0

    by_level = (
        bank_card[bank_card["match_status"] == "matched"]
        .groupby("match_level")
        .size()
        .to_dict()
    )

    return {
        "bank_card_total": total_bank_card,
        "bank_card_matched": int(bank_card_matched),
        "score_pct": score_pct,
        "ynab_total": len(ynab),
        "ynab_matched": int(ynab_matched),
        "by_level": by_level,
    }


def print_match_summary(df: pd.DataFrame) -> None:
    """Print a human-readable match summary including per-level breakdown."""
    s = compute_match_score(df)
    print(f"Match score:  {s['score_pct']}%  "
          f"({s['bank_card_matched']} / {s['bank_card_total']} bank/card rows matched)")
    print(f"YNAB rows:    {s['ynab_matched']} matched / {s['ynab_total']} total")
    if s["by_level"]:
        print("  Breakdown by level:")
        for level_name, count in sorted(s["by_level"].items()):
            print(f"    {level_name:15s} {count} pairs")
    unmatched_bank = s["bank_card_total"] - s["bank_card_matched"]
    unmatched_ynab = s["ynab_total"] - s["ynab_matched"]
    if unmatched_bank:
        print(f"  ↳ {unmatched_bank} bank/card rows still unmatched")
    if unmatched_ynab:
        print(f"  ↳ {unmatched_ynab} YNAB rows still unmatched")
