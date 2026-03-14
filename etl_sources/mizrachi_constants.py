"""Mizrachi-specific parsing and mapping constants."""

# Canonical account name in ACCOUNT_REGISTRY.md.
MIZRACHI_ACCOUNT_NAME = "Mizrachi"

# Accepted input date formats from Mizrachi exports.
# Keep ordered from most common to less common for predictable parsing.
MIZRACHI_INPUT_DATE_FORMAT = "%d/%m/%y"

# Translation from Mizrachi Hebrew headers to canonical/intermediate names.
MIZRACHI_HEBREW_TO_CANONICAL_COLUMN_MAP = {
    "תאריך": "Date",
    "סוג תנועה": "Payee",
    "זכות": "Inflow",
    "חובה": "Outflow",
}
