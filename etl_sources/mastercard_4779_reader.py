from __future__ import annotations

from pathlib import Path

import pandas as pd

from etl_common.file_loader import LoadedTable, list_tabular_files


def load_mastercard_4779_tables(
    folder: str | Path, recursive: bool = False
) -> list[LoadedTable]:
    """Load Mastercard 4779 source files into dataframes (prototype)."""
    loaded: list[LoadedTable] = []
    for file_path in list_tabular_files(folder=folder, recursive=recursive):
        df = read_mastercard_4779_file(file_path)
        loaded.append(LoadedTable(path=file_path, extension=file_path.suffix.lower(), dataframe=df))
    return loaded


def read_mastercard_4779_file(path: str | Path) -> pd.DataFrame:
    """Read one Mastercard 4779 file and attach source metadata.

    Note
    ----
    This is intentionally minimal. If your files are CSV or HTML instead of
    Excel, update this reader accordingly.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Mastercard 4779 source file does not exist: {file_path}")

    df = pd.read_excel(file_path)
    if df.empty:
        raise ValueError(f"Mastercard 4779 source file is empty: {file_path.name}")

    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    df = df.reset_index(drop=True)

    df["__source_file"] = file_path.name
    df["__source_path"] = str(file_path)
    df["__source_ext"] = file_path.suffix.lower()
    df["__source_rule"] = "mastercard_4779_read_excel"
    return df
