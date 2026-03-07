from __future__ import annotations

from pathlib import Path

import pandas as pd

from etl_common.file_loader import LoadedTable, list_tabular_files


def load_mizrachi_tables(folder: str | Path, recursive: bool = False) -> list[LoadedTable]:
    """
    Mizrachi-specific loading rule (tryout v1):
    1) read using pd.read_html
    2) use tables[1]
    """
    loaded: list[LoadedTable] = []
    for file_path in list_tabular_files(folder=folder, recursive=recursive):
        df = read_mizrachi_file(file_path)
        loaded.append(LoadedTable(path=file_path, extension=file_path.suffix.lower(), dataframe=df))
    return loaded


def read_mizrachi_file(path: str | Path) -> pd.DataFrame:
    file_path = Path(path)
    tables = pd.read_html(file_path)

    if len(tables) <= 1:
        raise ValueError(
            f"Mizrachi rule expected tables[1], but found {len(tables)} table(s) in {file_path.name}"
        )

    df = tables[1].copy()
    df.columns = [str(c).strip() for c in df.columns]
    # Remove completely empty rows that come from HTML table rendering gaps.
    df = df.dropna(how="all")
    # Remove empty columns that are often created by visual spacing in exported tables.
    df = df.dropna(axis=1, how="all")
    # Normalize row numbering after filtering so downstream logic gets a clean index.
    df = df.reset_index(drop=True)

    df["__source_file"] = file_path.name
    df["__source_path"] = str(file_path)
    df["__source_ext"] = file_path.suffix.lower()
    df["__source_rule"] = "mizrachi_read_html_table_1"
    return df

