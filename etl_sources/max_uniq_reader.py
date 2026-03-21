from __future__ import annotations

from pathlib import Path

import pandas as pd

from etl_common.file_loader import LoadedTable, list_tabular_files


def load_max_uniq_tables(folder: str | Path, recursive: bool = False) -> list[LoadedTable]:
    """Load Max Uniq source files into dataframes (prototype)."""
    loaded: list[LoadedTable] = []
    for file_path in list_tabular_files(folder=folder, recursive=recursive):
        sheet_tables = read_max_uniq_file(file_path)
        loaded.extend(
            LoadedTable(path=file_path, extension=file_path.suffix.lower(), dataframe=sheet_df)
            for sheet_df in sheet_tables
        )
    return loaded


def read_max_uniq_file(path: str | Path) -> list[pd.DataFrame]:
    """Read one Max Uniq file and attach source metadata.

    Note
    ----
    This is intentionally minimal. If your files are CSV or HTML instead of
    Excel, update this reader accordingly.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Max Uniq source file does not exist: {file_path}")

    sheets = pd.read_excel(file_path, sheet_name=None, header=None)
    if not sheets:
        raise ValueError(f"Max Uniq source file has no sheets: {file_path.name}")

    loaded_sheets: list[pd.DataFrame] = []
    for sheet_name, raw_df in sheets.items():
        if raw_df.empty:
            continue

        # Keep raw rows intact so header detection can find true header row.
        df = raw_df.dropna(how="all")
        df = df.dropna(axis=1, how="all")
        if df.empty:
            continue

        df = df.reset_index(drop=True)
        df["__source_file"] = file_path.name
        df["__source_path"] = str(file_path)
        df["__source_ext"] = file_path.suffix.lower()
        df["__source_sheet"] = str(sheet_name)
        df["__source_rule"] = "max_uniq_read_excel_all_sheets"
        loaded_sheets.append(df)

    if not loaded_sheets:
        raise ValueError(f"Max Uniq source file has no non-empty sheets: {file_path.name}")

    return loaded_sheets
