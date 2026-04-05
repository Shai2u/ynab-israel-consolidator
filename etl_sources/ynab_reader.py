"""YNAB Register reader: handles zip archives and plain CSV files."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

from etl_sources.ynab_constants import (
    YNAB_FILENAME_TO_OWNERSHIP,
    YNAB_REGISTER_KEEP_COLUMNS,
    YNAB_AMOUNT_CURRENCY_SUFFIX,
)


def load_ynab_tables(folder: str | Path) -> list[pd.DataFrame]:
    """Load all YNAB Register tables found in ``folder``.

    Accepts any mix of:
    - ``.zip`` files exported directly from YNAB (extracts the ``*Register.csv`` inside)
    - ``.csv`` files whose name contains ``Register``
    - plain ``.csv`` files (treated as Register if no other signal)

    Parameters
    ----------
    folder : str | Path
        Folder containing YNAB export files.

    Returns
    -------
    list[pd.DataFrame]
        One normalized DataFrame per Register file found.
        Each DataFrame already has ``Ownership`` and ``source_type`` columns set.
    """
    folder = Path(folder)
    frames: list[pd.DataFrame] = []

    for file_path in sorted(folder.iterdir()):
        if file_path.suffix.lower() == ".zip":
            df = _read_register_from_zip(file_path)
        elif file_path.suffix.lower() == ".csv" and "Register" in file_path.name:
            df = _read_register_csv(file_path)
        else:
            continue

        if df is None:
            continue

        ownership = _resolve_ownership_from_filename(file_path.name)
        df["Ownership"] = ownership
        df["__source_file"] = file_path.name
        frames.append(df)

    return frames


# ---------------------------------------------------------------------------
# Internal readers
# ---------------------------------------------------------------------------

def _read_register_from_zip(zip_path: Path) -> pd.DataFrame | None:
    """Extract and read the Register CSV from a YNAB zip export."""
    with zipfile.ZipFile(zip_path) as zf:
        register_names = [n for n in zf.namelist() if n.endswith("- Register.csv")]
        if not register_names:
            return None
        with zf.open(register_names[0]) as f:
            raw_bytes = f.read()

    return _parse_register_csv_bytes(raw_bytes, source_name=zip_path.name)


def _read_register_csv(csv_path: Path) -> pd.DataFrame | None:
    """Read a plain Register CSV file from disk."""
    raw_bytes = csv_path.read_bytes()
    return _parse_register_csv_bytes(raw_bytes, source_name=csv_path.name)


def _parse_register_csv_bytes(raw_bytes: bytes, source_name: str) -> pd.DataFrame:
    """Parse raw CSV bytes into a clean Register DataFrame.

    Tries ``utf-8-sig`` first (handles BOM from YNAB), falls back to ``utf-8``.
    """
    for encoding in ("utf-8-sig", "utf-8", "cp1255", "latin-1"):
        try:
            df = pd.read_csv(io.BytesIO(raw_bytes), encoding=encoding, encoding_errors="replace")
            break
        except Exception:
            continue
    else:
        raise ValueError(f"Could not decode YNAB Register file: {source_name}")

    missing = [c for c in YNAB_REGISTER_KEEP_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"[{source_name}] YNAB Register missing expected columns: {missing}. "
            f"Found: {df.columns.tolist()}"
        )

    df = df[YNAB_REGISTER_KEEP_COLUMNS].copy()
    df["Memo"] = df["Memo"].fillna("")
    df["Outflow"] = _parse_amount_column(df["Outflow"])
    df["Inflow"] = _parse_amount_column(df["Inflow"])
    return df


def _parse_amount_column(series: pd.Series) -> pd.Series:
    """Strip currency suffix and convert amount strings to float."""
    cleaned = (
        series.astype(str)
        .str.replace(YNAB_AMOUNT_CURRENCY_SUFFIX, "", regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce").fillna(0.0)


def _resolve_ownership_from_filename(filename: str) -> str:
    """Resolve ownership label by matching filename against known budget patterns.

    Parameters
    ----------
    filename : str
        Name of the source file (zip or csv).

    Returns
    -------
    str
        Canonical ownership label.

    Raises
    ------
    ValueError
        If no known budget pattern matches the filename.
    """
    for pattern, ownership in YNAB_FILENAME_TO_OWNERSHIP:
        if pattern in filename:
            return ownership
    raise ValueError(
        f"Cannot determine ownership for YNAB file '{filename}'. "
        f"Add a matching pattern to YNAB_FILENAME_TO_OWNERSHIP in ynab_constants.py."
    )
