"""YNAB-specific parsing constants."""

from etl_sources.account_registry import (
    OWNERSHIP_SHAI_NIRIT_JOINT,
    OWNERSHIP_SHAI_PRIVATE,
)

# YNAB exports already use dd/mm/YYYY — same as our canonical output format.
YNAB_REGISTER_DATE_FORMAT = "%d/%m/%Y"

# Amount columns carry a trailing ₪ symbol that must be stripped before float conversion.
YNAB_AMOUNT_CURRENCY_SUFFIX = "₪"

# YNAB Register columns we carry forward into the canonical schema.
# The names already match canonical; no renaming needed.
YNAB_REGISTER_KEEP_COLUMNS = ["Account", "Date", "Payee", "Memo", "Outflow", "Inflow"]

# Maps a substring found in the YNAB zip/csv filename to a canonical ownership label.
# Order matters: more specific patterns must come first.
YNAB_FILENAME_TO_OWNERSHIP: list[tuple[str, str]] = [
    ("Mizrahi Nirit and Shai", OWNERSHIP_SHAI_NIRIT_JOINT),
    ("Shai", OWNERSHIP_SHAI_PRIVATE),
]
