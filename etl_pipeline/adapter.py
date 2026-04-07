"""Formal interface contracts for source pipeline adapters.

Every source (bank or credit card) must provide two callables that satisfy
these Protocols before it can be registered in ``SOURCE_REGISTRY``:

- :class:`SourceLoader`    – reads raw files from a folder into LoadedTable objects.
- :class:`SourceNormalizer` – converts one raw DataFrame into the canonical schema.

Why Protocol (not ABC)?
-----------------------
Using ``typing.Protocol`` means *no inheritance required*.  Any existing
function that already has the matching signature automatically satisfies the
contract.  Type checkers (pyright, mypy) will raise an error if a registered
function deviates from the expected signature — catching mistakes before
runtime.

Usage example (in consolidate.py)::

    from etl_pipeline.adapter import SourceLoader, SourceNormalizer

    @dataclass
    class SourceConfig:
        name: str
        folder: str
        loader: SourceLoader
        normalizer: SourceNormalizer
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

import pandas as pd

from etl_common.file_loader import LoadedTable


@runtime_checkable
class SourceLoader(Protocol):
    """A callable that reads raw export files from a folder.

    Parameters
    ----------
    folder : str | Path
        Directory containing the raw source export files.
    recursive : bool, optional
        Whether to search sub-directories, by default ``False``.

    Returns
    -------
    list[LoadedTable]
        One :class:`~etl_common.file_loader.LoadedTable` per file found.
        Empty list if the folder contains no matching files.
    """

    def __call__(
        self,
        folder: str | Path,
        recursive: bool = False,
    ) -> list[LoadedTable]: ...


@runtime_checkable
class SourceNormalizer(Protocol):
    """A callable that transforms one raw DataFrame into the canonical schema.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame as produced by a :class:`SourceLoader`.
    dates_range : tuple[str, str] | None, optional
        Inclusive date filter ``(start, end)`` in ``dd/mm/YYYY`` format.
        ``None`` means keep all rows.

    Returns
    -------
    pd.DataFrame
        DataFrame with exactly the columns defined in
        :data:`~etl_pipeline.schema.CANONICAL_COLUMNS`.
        The ``source_type`` column is stamped by the consolidation loop,
        not by the normalizer.
    """

    def __call__(
        self,
        df: pd.DataFrame,
        dates_range: tuple[str, str] | None = None,
    ) -> pd.DataFrame: ...
