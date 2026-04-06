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

# Maps YNAB account names to canonical bank/card account names used in SOURCE_REGISTRY.
# Only accounts that have a corresponding source file need an entry here.
# YNAB-only accounts (tracking, pension, savings) are intentionally omitted —
# they will never match a bank/card row and that is expected.
YNAB_TO_CANONICAL_ACCOUNT_MAP: dict[str, str] = {
    # Banks
    "Poalim":                  "Bank Hapoalim",
    "Leumi":                   "Bank Leumi",
    # Isracard
    "Isracard Top":            "Isracard 4054",
    # Visa Cal / Hitechzone
    "Hitechzone Cal 4779":     "Mastercard_4779_private",
    "Hitechzone CAL 7353":     "Mastercard_7353_private",
    # Max
    "Visa Max":                "Max Uniq",
    # Already matching — listed here for documentation only.
    # "Mizrachi":              "Mizrachi",
    # "Max Uniq":              "Max Uniq",
}
