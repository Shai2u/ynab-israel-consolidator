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
from typing import Any
from etl_pipeline.adapter import SourceLoader, SourceNormalizer

import pandas as pd

from etl_pipeline.config_loader import load_source_paths
from etl_pipeline.schema import CANONICAL_COLUMNS, SOURCE_TYPE_BANK_CARD, SOURCE_TYPE_YNAB, validate_source_df
from etl_sources.ynab_reader import load_ynab_tables
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
    loader: SourceLoader
    normalizer: SourceNormalizer


RunStatus = dict[str, Any]


def _append_status(
    status_rows: list[RunStatus],
    *,
    source: str,
    file_name: str,
    file_path: str,
    status: str,
    rows: int,
    error: str = "",
) -> None:
    """Append one run-status record used for end-of-run reporting."""
    status_rows.append(
        {
            "source": source,
            "file_name": file_name,
            "file_path": file_path,
            "status": status,
            "rows": rows,
            "error": error,
        }
    )


_paths = load_source_paths()

YNAB_FOLDER: str = _paths.ynab_folder

SOURCE_REGISTRY: list[SourceConfig] = [
    SourceConfig(
        name="Mizrachi",
        folder=_paths.sources["Mizrachi"],
        loader=load_mizrachi_tables,
        normalizer=normalize_mizrachi_table,
    ),
    SourceConfig(
        name="Bank Leumi",
        folder=_paths.sources["Bank Leumi"],
        loader=load_leumi_tables,
        normalizer=normalize_leumi_table,
    ),
    SourceConfig(
        name="Bank Hapoalim",
        folder=_paths.sources["Bank Hapoalim"],
        loader=load_hapoalim_tables,
        normalizer=normalize_hapoalim_table,
    ),
    SourceConfig(
        name="Max Uniq",
        folder=_paths.sources["Max Uniq"],
        loader=load_max_uniq_tables,
        normalizer=normalize_max_uniq_table,
    ),
    SourceConfig(
        name="Visa Cal 4779",
        folder=_paths.sources["Visa Cal 4779"],
        loader=load_visa_cal_tables,
        normalizer=normalize_visa_cal_table,
    ),
    SourceConfig(
        name="Visa Cal 7353",
        folder=_paths.sources["Visa Cal 7353"],
        loader=load_visa_cal_tables,
        normalizer=normalize_visa_cal_table,
    ),
    SourceConfig(
        name="Isracard",
        folder=_paths.sources["Isracard"],
        loader=load_isracard_tables,
        normalizer=normalize_isracard_table,
    ),
]


# ---------------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------------

def collect_source_frames(
    dates_range: tuple[str, str] | None = None,
    status_rows: list[RunStatus] | None = None,
    fail_on_error: bool = True,
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
    status_rows = status_rows if status_rows is not None else []

    for source in SOURCE_REGISTRY:
        print(f"[{source.name}] loading from {source.folder} ...")
        try:
            loaded_tables = source.loader(folder=source.folder, recursive=False)
        except Exception as exc:  # noqa: BLE001
            _append_status(
                status_rows,
                source=source.name,
                file_name="",
                file_path=source.folder,
                status="failed",
                rows=0,
                error=str(exc),
            )
            print(f"[{source.name}] ERROR: {exc}")
            if fail_on_error:
                raise
            continue

        if not loaded_tables:
            print(f"[{source.name}] WARNING: no files found, skipping.")
            _append_status(
                status_rows,
                source=source.name,
                file_name="",
                file_path=source.folder,
                status="skipped_no_files",
                rows=0,
            )
            continue

        for table in loaded_tables:
            try:
                normalized_df = source.normalizer(table.dataframe, dates_range=dates_range)
                normalized_df["source_type"] = SOURCE_TYPE_BANK_CARD
                validate_source_df(normalized_df, source_name=source.name)
                all_frames.append(normalized_df)
                _append_status(
                    status_rows,
                    source=source.name,
                    file_name=table.path.name,
                    file_path=str(table.path),
                    status="success",
                    rows=len(normalized_df),
                )
                print(f"[{source.name}] {table.path.name}: {len(normalized_df)} rows")
            except Exception as exc:  # noqa: BLE001
                _append_status(
                    status_rows,
                    source=source.name,
                    file_name=table.path.name,
                    file_path=str(table.path),
                    status="failed",
                    rows=0,
                    error=str(exc),
                )
                print(f"[{source.name}] ERROR in {table.path.name}: {exc}")
                if fail_on_error:
                    raise

    return all_frames


def collect_ynab_frames(
    dates_range: tuple[str, str] | None = None,
    status_rows: list[RunStatus] | None = None,
    fail_on_error: bool = True,
) -> list[pd.DataFrame]:
    """Load and validate all YNAB Register files from ``YNAB_FOLDER``.

    Parameters
    ----------
    dates_range : tuple[str, str] | None, optional
        Inclusive date range filter ``(start, end)`` in ``dd/mm/YYYY`` format.
        Rows outside this range are dropped, by default None (all dates).

    Returns
    -------
    list[pd.DataFrame]
        One validated canonical-schema DataFrame per YNAB Register file.
    """
    from etl_common.date_utilities import filter_by_dates_range
    from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT

    print(f"[YNAB] loading from {YNAB_FOLDER} ...")
    status_rows = status_rows if status_rows is not None else []
    try:
        raw_frames = load_ynab_tables(folder=YNAB_FOLDER)
    except Exception as exc:  # noqa: BLE001
        _append_status(
            status_rows,
            source="YNAB",
            file_name="",
            file_path=YNAB_FOLDER,
            status="failed",
            rows=0,
            error=str(exc),
        )
        print(f"[YNAB] ERROR: {exc}")
        if fail_on_error:
            raise
        return []

    if not raw_frames:
        print("[YNAB] WARNING: no Register files found, skipping.")
        _append_status(
            status_rows,
            source="YNAB",
            file_name="",
            file_path=YNAB_FOLDER,
            status="skipped_no_files",
            rows=0,
        )
        return []

    result: list[pd.DataFrame] = []
    for df in raw_frames:
        source_file = str(df["__source_file"].iloc[0]) if "__source_file" in df.columns and not df.empty else ""
        source_path = str(pathlib.Path(YNAB_FOLDER) / source_file) if source_file else YNAB_FOLDER
        try:
            df["source_type"] = SOURCE_TYPE_YNAB
            df["Memo"] = df["Memo"].fillna("")
            df = filter_by_dates_range(
                df,
                date_column="Date",
                dates_range=dates_range,
                output_date_format=YNAB_OUTPUT_DATE_FORMAT,
            )
            validate_source_df(df, source_name="YNAB")
            result.append(df)
            _append_status(
                status_rows,
                source="YNAB",
                file_name=source_file,
                file_path=source_path,
                status="success",
                rows=len(df),
            )
            print(f"[YNAB] {source_file}: {len(df)} rows")
        except Exception as exc:  # noqa: BLE001
            _append_status(
                status_rows,
                source="YNAB",
                file_name=source_file,
                file_path=source_path,
                status="failed",
                rows=0,
                error=str(exc),
            )
            print(f"[YNAB] ERROR in {source_file}: {exc}")
            if fail_on_error:
                raise

    return result


def build_master_df(
    dates_range: tuple[str, str] | None = None,
    status_rows: list[RunStatus] | None = None,
    fail_on_error: bool = True,
) -> pd.DataFrame:
    """Build the consolidated master DataFrame from all registered sources and YNAB.

    Parameters
    ----------
    dates_range : tuple[str, str] | None, optional
        Optional date range filter forwarded to every normalizer and YNAB loader.

    Returns
    -------
    pd.DataFrame
        Single DataFrame with canonical columns from both bank/card sources and YNAB.
    """
    bank_card_frames = collect_source_frames(
        dates_range=dates_range,
        status_rows=status_rows,
        fail_on_error=fail_on_error,
    )
    ynab_frames = collect_ynab_frames(
        dates_range=dates_range,
        status_rows=status_rows,
        fail_on_error=fail_on_error,
    )

    all_frames = bank_card_frames + ynab_frames
    if not all_frames:
        raise ValueError("No frames collected. Check folder paths and file contents.")

    master_df = pd.concat(all_frames, ignore_index=True)

    # Enforce column order defined by the contract.
    master_df = master_df[CANONICAL_COLUMNS]

    # Normalize numeric columns: coerce to float, no NaN (use 0.0), 2 decimal places.
    for col in ("Inflow", "Outflow"):
        master_df[col] = pd.to_numeric(master_df[col], errors="coerce").fillna(0.0).round(2)

    # Drop duplicate rows from overlapping statement periods.
    # Two rows are considered the same transaction when source_type, Account,
    # Date, Inflow, and Outflow are all identical.  Keep the first occurrence
    # (earliest file loaded).  This does not catch transactions that changed
    # state (e.g. pending → cleared with a slightly different amount) — those
    # are treated as distinct rows intentionally.
    rows_before = len(master_df)
    master_df = master_df.drop_duplicates(
        subset=["source_type", "Account", "Date", "Inflow", "Outflow", "Memo"],
        keep="first",
    ).reset_index(drop=True)
    dropped = rows_before - len(master_df)

    total_bank = sum(len(f) for f in bank_card_frames)
    total_ynab = sum(len(f) for f in ynab_frames)
    dup_note = f", {dropped} duplicates dropped" if dropped else ""
    print(f"\nMaster DataFrame: {len(master_df)} rows total ({total_bank} bank/card + {total_ynab} YNAB{dup_note}).")
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


def export_run_report(
    status_rows: list[RunStatus],
    output_dir: pathlib.Path | str | None = None,
) -> pathlib.Path:
    """Write per-source/per-file processing statuses to a timestamped CSV report."""
    out_dir = pathlib.Path(output_dir) if output_dir else _DEFAULT_OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"run_report_{timestamp}.csv"

    report_df = pd.DataFrame(
        status_rows,
        columns=["source", "file_name", "file_path", "status", "rows", "error"],
    )
    report_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"Exported run report ({len(report_df)} entries) -> {out_path}")
    return out_path


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_dates_range = ("01/03/2026", "01/06/2026")
    run_status_rows: list[RunStatus] = []
    try:
        run_master_df = build_master_df(
            dates_range=run_dates_range,
            status_rows=run_status_rows,
            fail_on_error=True,
        )
        export_master_csv(run_master_df)
    finally:
        export_run_report(run_status_rows)
