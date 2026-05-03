"""Load machine-specific folder paths from sources_config.json.

The config file lives in ``private_data/sources_config.json`` (gitignored).
Copy ``sources_config.example.json`` from the project root to create it,
then fill in your local paths. Relative paths are resolved from the project
root, so the same config shape works on macOS, Linux, and Windows.

Why a separate config file instead of hardcoded paths?
- Paths are machine-specific; the code is not.
- A new machine or a colleague only needs to edit one JSON file, not Python.
- This is the same data that will eventually come from the Django settings page.
"""

from __future__ import annotations

import json
import pathlib
from typing import NamedTuple

# Resolved at import time so error messages show the absolute path.
_PROJECT_ROOT = pathlib.Path(__file__).parent.parent
_CONFIG_PATH = _PROJECT_ROOT / "private_data" / "sources_config.json"


class SourcePaths(NamedTuple):
    """Folder paths resolved from the config file."""

    ynab_folder: str
    sources: dict[str, str]  # source name -> folder path


def load_source_paths() -> SourcePaths:
    """Read folder paths from ``private_data/sources_config.json``.

    Returns
    -------
    SourcePaths
        Parsed paths from the config file.

    Raises
    ------
    FileNotFoundError
        If ``private_data/sources_config.json`` does not exist.
        Copy ``sources_config.example.json`` and fill in your local paths.
    KeyError
        If a required key is missing from the config.
    """
    if not _CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Config file not found: {_CONFIG_PATH}\n"
            "Copy 'sources_config.example.json' to 'private_data/sources_config.json' "
            "and fill in your local folder paths."
        )

    with _CONFIG_PATH.open(encoding="utf-8") as f:
        raw = json.load(f)

    missing = [k for k in ("ynab_folder", "sources") if k not in raw]
    if missing:
        raise KeyError(
            f"sources_config.json is missing required keys: {missing}. "
            "Check sources_config.example.json for the expected structure."
        )

    return SourcePaths(
        ynab_folder=str(_resolve_config_path(raw["ynab_folder"])),
        sources={
            source_name: str(_resolve_config_path(folder))
            for source_name, folder in raw["sources"].items()
        },
    )


def _resolve_config_path(path_value: str) -> pathlib.Path:
    """Resolve a config path, keeping absolute paths untouched."""
    path = pathlib.Path(path_value).expanduser()
    if path.is_absolute():
        return path
    return _PROJECT_ROOT / path


def get_source_folder(source_name: str) -> str:
    """Return the folder path for a named source.

    Parameters
    ----------
    source_name : str
        Must match a key in the ``sources`` section of the config file.

    Raises
    ------
    KeyError
        If ``source_name`` is not declared in the config.
    """
    paths = load_source_paths()
    if source_name not in paths.sources:
        raise KeyError(
            f"Source '{source_name}' not found in sources_config.json. "
            f"Known sources: {list(paths.sources.keys())}"
        )
    return paths.sources[source_name]
