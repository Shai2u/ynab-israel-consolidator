from __future__ import annotations

from pathlib import Path

import pandas as pd

from etl_common.file_loader import LoadedTable, list_tabular_files


def load_hapoalim_tables(folder: str | Path, recursive: bool = False) -> list[LoadedTable]:
    """Load Hapoalim source files into dataframes (prototype)."""
    loaded: list[LoadedTable] = []
    for file_path in list_tabular_files(folder=folder, recursive=recursive):
        df = read_hapoalim_file(file_path)
        loaded.append(LoadedTable(path=file_path, extension=file_path.suffix.lower(), dataframe=df))
    return loaded


def read_hapoalim_file(path: str | Path) -> pd.DataFrame:
    """Read one Hapoalim file and attach source metadata.

    Note
    ----
    This is intentionally a minimal skeleton. Update table-selection logic
    (for example, ``tables[?]``) once real Hapoalim samples are inspected.
    """
    file_path = Path(path)
    tables = pd.read_excel(file_path)

    if not tables:
        raise ValueError(f"Hapoalim rule expected at least one HTML table in {file_path.name}")

    # TODO: choose the correct table index based on real exports.
    df = tables[0].copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    df = df.reset_index(drop=True)

    df["__source_file"] = file_path.name
    df["__source_path"] = str(file_path)
    df["__source_ext"] = file_path.suffix.lower()
    df["__source_rule"] = "hapoalim_read_html_table_0"
    return df
