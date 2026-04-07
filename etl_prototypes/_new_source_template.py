"""Boilerplate template for adding a new bank or credit-card source.

HOW TO USE THIS FILE
--------------------
1. Copy this file and rename it:
       etl_prototypes/bank_SOURCENAME_proto.py
   or  etl_prototypes/card_SOURCENAME_proto.py

2. Create a constants file:
       etl_sources/SOURCENAME_constants.py
   Fill in the 4 required constants (see Step A below).

3. Create a reader file (or skip if the generic loader is enough):
       etl_sources/SOURCENAME_reader.py
   See Step B below.

4. Fill in the 3 TODO sections in normalize_SOURCENAME_table().

5. Run this file directly and verify the output looks right.

6. Register the source in etl_pipeline/consolidate.py SOURCE_REGISTRY.

The 5 steps are marked with TODO comments throughout this file.
"""

from __future__ import annotations

import pandas as pd

from etl_common.column_mapping import select_mapped_columns, translate_columns
from etl_common.date_utilities import normalize_date_column, filter_by_dates_range
from etl_common.header_detection import detect_header_row_by_required_headers, apply_header_row
from etl_sources.account_registry import attach_account_metadata
from etl_sources.constants import YNAB_OUTPUT_DATE_FORMAT

# TODO [Step A] — replace this import block with your source's constants file.
# Create etl_sources/SOURCENAME_constants.py and define these 4 values:
#
#   SOURCENAME_ACCOUNT_NAME = "My Bank"          # must match ACCOUNT_REGISTRY.md
#   SOURCENAME_INPUT_DATE_FORMAT = "%d/%m/%Y"    # date format in the raw export
#   SOURCENAME_REQUIRED_HEADERS = {"col1", "col2"}  # Hebrew/source header signature
#   SOURCENAME_SOURCE_TO_CANONICAL_COLUMN_MAP = {
#       "תאריך": "Date",
#       "שם": "Payee",
#       "חיוב": "Outflow",
#       "זיכוי": "Inflow",
#       "הערה": "Memo",
#   }
#
# Then replace the four lines below:
SOURCENAME_ACCOUNT_NAME = "TODO"
SOURCENAME_INPUT_DATE_FORMAT = "%d/%m/%Y"
SOURCENAME_REQUIRED_HEADERS: set[str] = set()
SOURCENAME_SOURCE_TO_CANONICAL_COLUMN_MAP: dict[str, str] = {}

# TODO [Step B] — replace with your source's loader import.
# If the generic read_tabular_file() is enough (standard xlsx/csv),
# you can use load_folder_tables from etl_common.file_loader directly
# and skip creating a custom reader.
# Otherwise, create etl_sources/SOURCENAME_reader.py and import here:
#
#   from etl_sources.SOURCENAME_reader import load_SOURCENAME_tables
#
# For now this uses the generic loader as a placeholder:
from etl_common.file_loader import LoadedTable, load_folder_tables


def load_SOURCENAME_tables(
    folder: str, recursive: bool = False
) -> list[LoadedTable]:
    """Load raw export files for SOURCENAME.

    Replace this function with a custom reader if the generic loader is
    not sufficient (e.g. HTML tables, multi-sheet xlsx, zip archives).
    """
    return load_folder_tables(folder=folder, recursive=recursive)


# ---------------------------------------------------------------------------
# Normalizer — this is the function that plugs into SOURCE_REGISTRY
# ---------------------------------------------------------------------------

def normalize_SOURCENAME_table(
    df: pd.DataFrame,
    dates_range: tuple[str, str] | None = None,
) -> pd.DataFrame:
    """Normalize one raw SOURCENAME DataFrame into the canonical schema.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame as produced by ``load_SOURCENAME_tables``.
    dates_range : tuple[str, str] | None, optional
        Inclusive date filter ``(start, end)`` in ``dd/mm/YYYY`` format.

    Returns
    -------
    pd.DataFrame
        DataFrame with exactly the canonical columns.
    """
    # TODO [Step C-1] — Header detection.
    # If the real data starts on row 0, remove these two lines entirely.
    # If there is a preamble (bank logos, account info above the header row),
    # use detect_header_row_by_required_headers to find and promote the header:
    header_row_idx = detect_header_row_by_required_headers(
        df, required_headers=SOURCENAME_REQUIRED_HEADERS
    )
    df = apply_header_row(df, header_row_idx)

    # TODO [Step C-2] — Column translation.
    # translate_columns renames source columns to canonical names.
    df = translate_columns(df, source_to_canonical_map=SOURCENAME_SOURCE_TO_CANONICAL_COLUMN_MAP)

    # TODO [Step C-3] — Date normalization.
    # Change SOURCENAME_INPUT_DATE_FORMAT to match the raw export (e.g. "%d.%m.%y").
    df = normalize_date_column(
        df,
        date_column="Date",
        input_date_format=SOURCENAME_INPUT_DATE_FORMAT,
        output_date_format=YNAB_OUTPUT_DATE_FORMAT,
    )

    # Date filter — no changes needed here.
    df = filter_by_dates_range(
        df,
        date_column="Date",
        dates_range=dates_range,
        output_date_format=YNAB_OUTPUT_DATE_FORMAT,
    )

    # Keep only canonical output columns — no changes needed here.
    df = select_mapped_columns(
        df, source_to_canonical_map=SOURCENAME_SOURCE_TO_CANONICAL_COLUMN_MAP
    )

    # TODO [Step C-4] — Memo column.
    # If your source has no Memo equivalent, keep the line below as-is.
    # If you want to concatenate extra columns into Memo, do it before
    # select_mapped_columns() above and add those columns to the map.
    if "Memo" not in df.columns:
        df["Memo"] = ""

    # TODO [Step C-5] — Inflow / Outflow split.
    # If the source exports a single signed Amount column, split it here:
    #
    #   amount = pd.to_numeric(df["Amount"], errors="coerce").fillna(0.0)
    #   df["Inflow"]  = amount.clip(lower=0)
    #   df["Outflow"] = amount.clip(upper=0).abs()
    #   df = df.drop(columns=["Amount"])

    # Attach account name and ownership — no changes needed here.
    df = attach_account_metadata(df=df, account_name=SOURCENAME_ACCOUNT_NAME)

    return df


# ---------------------------------------------------------------------------
# Manual run / smoke test
# ---------------------------------------------------------------------------

def main(path_to_folder: str, dates_range: tuple[str, str] | None = None) -> pd.DataFrame:
    """Load files from folder, normalize, and print a preview.

    Parameters
    ----------
    path_to_folder : str
        Folder containing raw export files.
    dates_range : tuple[str, str] | None, optional
        Optional date range for a focused run.

    Returns
    -------
    pd.DataFrame
        Normalized DataFrame from the last loaded file.
    """
    loaded_tables = load_SOURCENAME_tables(folder=path_to_folder, recursive=False)
    print(f"Files found: {len(loaded_tables)}")

    df_result = pd.DataFrame()
    for table in loaded_tables:
        print(f"\nFile: {table.path.name}")
        df_result = normalize_SOURCENAME_table(table.dataframe, dates_range=dates_range)
        print(df_result.head())
        print(f"Shape: {df_result.shape}")

    return df_result


# TODO [Step D] — Update the path below and run this file to smoke-test.
if __name__ == "__main__":
    path_to_folder = r"C:\path\to\private_data\incoming\SOURCENAME"
    dates_range = ("01/01/2026", "01/03/2026")
    main(path_to_folder=path_to_folder, dates_range=dates_range)


# ---------------------------------------------------------------------------
# TODO [Step E] — Register in consolidate.py SOURCE_REGISTRY
# ---------------------------------------------------------------------------
#
# Once this works, open etl_pipeline/consolidate.py and add:
#
#   from etl_sources.SOURCENAME_reader import load_SOURCENAME_tables
#   from etl_prototypes.SOURCENAME_proto import normalize_SOURCENAME_table
#
#   SourceConfig(
#       name="My Bank Display Name",
#       folder=r"C:\path\to\private_data\incoming\SOURCENAME",
#       loader=load_SOURCENAME_tables,
#       normalizer=normalize_SOURCENAME_table,
#   ),
