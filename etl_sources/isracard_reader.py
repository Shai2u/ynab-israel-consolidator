from __future__ import annotations

from pathlib import Path

import pandas as pd

from etl_common.file_loader import LoadedTable, list_tabular_files


def load_isracard_tables(folder: str | Path, recursive: bool = False) -> list[LoadedTable]:
    """Load Isracard source files into dataframes (prototype)."""
    loaded: list[LoadedTable] = []
    for file_path in list_tabular_files(folder=folder, recursive=recursive):
        df = read_isracard_file(file_path)
        loaded.append(LoadedTable(path=file_path, extension=file_path.suffix.lower(), dataframe=df))
    return loaded


def read_isracard_file(path: str | Path) -> pd.DataFrame:
    """Read one Isracard file and attach source metadata.

    Note
    ----
    This is intentionally minimal. If your files are CSV or multi-sheet Excel,
    update this reader accordingly.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Isracard source file does not exist: {file_path}")

    df = pd.read_excel(file_path)
    if df.empty:
        raise ValueError(f"Isracard source file is empty: {file_path.name}")

    # Keep rows intact for downstream header detection.
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    df = df.reset_index(drop=True)

    df["__source_file"] = file_path.name
    df["__source_path"] = str(file_path)
    df["__source_ext"] = file_path.suffix.lower()
    df["__source_rule"] = "isracard_read_excel"
    return df
