from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


SUPPORTED_EXTENSIONS = (".xlsx", ".xls", ".csv")


@dataclass(frozen=True)
class LoadedTable:
    path: Path
    extension: str
    dataframe: pd.DataFrame


def list_tabular_files(folder: str | Path, recursive: bool = False) -> list[Path]:
    """Return sorted tabular files from a folder."""
    base = Path(folder)
    if not base.exists():
        raise FileNotFoundError(f"Folder not found: {base}")

    walker: Iterable[Path]
    if recursive:
        walker = base.rglob("*")
    else:
        walker = base.iterdir()

    files = [p for p in walker if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    return sorted(files)


def read_tabular_file(path: str | Path, add_source_columns: bool = True) -> pd.DataFrame:
    """
    Read .xlsx/.xls/.csv into a DataFrame with basic cleanup.

    Basic cleanup tasks:
    - trim column names
    - drop fully empty rows/columns
    - reset index
    - optional source metadata columns
    """
    file_path = Path(path)
    extension = file_path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {extension}")

    if extension == ".csv":
        df = _read_csv_with_fallback(file_path)
    else:
        df = _read_excel_with_html_fallback(file_path)

    df = _basic_cleanup(df)

    if add_source_columns:
        df["__source_file"] = file_path.name
        df["__source_path"] = str(file_path)
        df["__source_ext"] = extension

    return df


def load_folder_tables(
    folder: str | Path,
    recursive: bool = False,
    add_source_columns: bool = True,
) -> list[LoadedTable]:
    """Load all supported tabular files from folder."""
    loaded: list[LoadedTable] = []
    for file_path in list_tabular_files(folder=folder, recursive=recursive):
        df = read_tabular_file(path=file_path, add_source_columns=add_source_columns)
        loaded.append(LoadedTable(path=file_path, extension=file_path.suffix.lower(), dataframe=df))
    return loaded


def _read_csv_with_fallback(path: Path) -> pd.DataFrame:
    # utf-8-sig is common for exports; cp1255 handles many Hebrew CSVs.
    for encoding in ("utf-8-sig", "utf-8", "cp1255"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path)


def _read_excel_with_html_fallback(path: Path) -> pd.DataFrame:
    try:
        return pd.read_excel(path)
    except Exception as excel_error:
        try:
            tables = pd.read_html(path)
        except Exception:
            raise excel_error

        if not tables:
            raise excel_error
        return tables[0]


def _basic_cleanup(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = [str(c).strip() for c in cleaned.columns]
    cleaned = cleaned.dropna(how="all")
    cleaned = cleaned.dropna(axis=1, how="all")
    cleaned = cleaned.reset_index(drop=True)
    return cleaned

