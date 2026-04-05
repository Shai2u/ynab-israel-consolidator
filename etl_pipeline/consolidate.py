"""Consolidation pipeline: merge all normalized source DataFrames into one master table.

Usage
-----
Run directly::

    python -m etl_pipeline.consolidate

Or import and call ``build_master_df`` from a notebook.

Design
------
Each source is registered once in ``SOURCE_REGISTRY`` with three things:
- ``name``       – human label used in error messages and the progress log
- ``folder``     – path to the folder containing that source's raw export files
- ``loader``     – function that reads raw files from the folder into LoadedTable objects
- ``normalizer`` – function that turns one raw DataFrame into a canonical-schema DataFrame

The consolidation loop is generic: it does not know anything about individual
sources beyond what is declared in the registry.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

import pandas as pd

from etl_pipeline.schema import CANONICAL_COLUMNS, validate_source_df
from etl_sources.isracard_reader import load_isracard_tables
from etl_sources.leumi_reader import load_leumi_tables
from etl_sources.hapoalim_reader import load_hapoalim_tables
from etl_sources.max_uniq_reader import load_max_uniq_tables
from etl_sources.mizrachi_reader import load_mizrachi_tables
from etl_sources.visa_cal_reader import load_visa_cal_tables
from etl_prototypes.bank_leumi_proto import normalize_leumi_table
from etl_prototypes.bank_hapoalim_proto import normalize_hapoalim_table
from etl_prototypes.bank_mizrachi_proto import normalize_mizrachi_table
from etl_prototypes.card_max_uniq_proto import normalize_max_uniq_table
from etl_prototypes.card_visa_cal_proto import normalize_visa_cal_table
from etl_prototypes.card_isracard_proto import normalize_isracard_table


# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------

@dataclass
class SourceConfig:
    """Declaration of one source's loader and normalizer."""

    name: str
    folder: str
    loader: Callable
    normalizer: Callable


SOURCE_REGISTRY: list[SourceConfig] = [
    SourceConfig(
        name="Mizrachi",
        folder=r"C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\bank_mizrachi",
        loader=load_mizrachi_tables,
        normalizer=normalize_mizrachi_table,
    ),
    SourceConfig(
        name="Bank Leumi",
        folder=r"C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\bank_leumi",
        loader=load_leumi_tables,
        normalizer=normalize_leumi_table,
    ),
    SourceConfig(
        name="Bank Hapoalim",
        folder=r"C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\bank_hapoalim",
        loader=load_hapoalim_tables,
        normalizer=normalize_hapoalim_table,
    ),
    SourceConfig(
        name="Max Uniq",
        folder=r"C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\visa_max",
        loader=load_max_uniq_tables,
        normalizer=normalize_max_uniq_table,
    ),
    SourceConfig(
        name="Visa Cal",
        folder=r"C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\visa_cal",
        loader=load_visa_cal_tables,
        normalizer=normalize_visa_cal_table,
    ),
    SourceConfig(
        name="Isracard",
        folder=r"C:\Users\shai\Documents\personal\personal_projects\ynab-israel-consolidator\private_data\incoming\isracard",
        loader=load_isracard_tables,
        normalizer=normalize_isracard_table,
    ),
]


# ---------------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------------

def collect_source_frames(
    dates_range: tuple[str, str] | None = None,
) -> list[pd.DataFrame]:
    """Load, normalize, and validate every registered source.

    Parameters
    ----------
    dates_range : tuple[str, str] | None, optional
        Inclusive date range filter ``(start, end)`` in ``dd/mm/YYYY`` format
        passed through to each normalizer, by default None (all dates).

    Returns
    -------
    list[pd.DataFrame]
        One validated canonical-schema DataFrame per loaded file.
        Sources with no files in their folder are skipped with a warning.
    """
    all_frames: list[pd.DataFrame] = []

    for source in SOURCE_REGISTRY:
        print(f"[{source.name}] loading from {source.folder} ...")
        loaded_tables = source.loader(folder=source.folder, recursive=False)

        if not loaded_tables:
            print(f"[{source.name}] WARNING: no files found, skipping.")
            continue

        for table in loaded_tables:
            normalized_df = source.normalizer(table.dataframe, dates_range=dates_range)
            validate_source_df(normalized_df, source_name=source.name)
            all_frames.append(normalized_df)
            print(f"[{source.name}] {table.path.name}: {len(normalized_df)} rows")

    return all_frames


def build_master_df(
    dates_range: tuple[str, str] | None = None,
) -> pd.DataFrame:
    """Build the consolidated master DataFrame from all registered sources.

    Parameters
    ----------
    dates_range : tuple[str, str] | None, optional
        Optional date range filter forwarded to every normalizer.

    Returns
    -------
    pd.DataFrame
        Single DataFrame with canonical columns, sorted by ``Date`` ascending,
        reset index.
    """
    frames = collect_source_frames(dates_range=dates_range)

    if not frames:
        raise ValueError("No source frames collected. Check folder paths and file contents.")

    master_df = pd.concat(frames, ignore_index=True)

    # Enforce column order defined by the contract.
    master_df = master_df[CANONICAL_COLUMNS]

    print(f"\nMaster DataFrame: {len(master_df)} total rows from {len(frames)} files.")
    return master_df


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

# Default output folder, relative to the project root.
_DEFAULT_OUTPUT_DIR = pathlib.Path(__file__).parent.parent / "private_data" / "outgoing"


def export_master_csv(
    master_df: pd.DataFrame,
    output_dir: pathlib.Path | str | None = None,
) -> pathlib.Path:
    """Write the master DataFrame to a timestamped CSV file.

    Parameters
    ----------
    master_df : pd.DataFrame
        Consolidated master DataFrame to export.
    output_dir : pathlib.Path | str | None, optional
        Destination folder. Defaults to ``private_data/outgoing/``.

    Returns
    -------
    pathlib.Path
        Path to the written CSV file.

    Notes
    -----
    Uses ``utf-8-sig`` encoding (UTF-8 with BOM) so Hebrew characters
    render correctly when opened directly in Excel on Windows.
    """
    out_dir = pathlib.Path(output_dir) if output_dir else _DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"master_{timestamp}.csv"

    master_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Exported {len(master_df)} rows -> {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    dates_range = ("01/01/2026", "01/03/2026")
    master_df = build_master_df(dates_range=dates_range)
    export_master_csv(master_df)
