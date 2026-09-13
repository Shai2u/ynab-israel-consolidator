"""Isracard-specific parsing and mapping constants (prototype)."""

# Canonical account name in ACCOUNT_REGISTRY.md.
ISRACARD_ACCOUNT_NAME = "Isracard 4054"

# Confirmed Isracard export date format (dd.mm.yy).
ISRACARD_INPUT_DATE_FORMAT = "%d.%m.%y"

# Default header row index fallback in Isracard exports.
ISRACARD_HEADER_DEFAULT_ROW_IDX = 0

# Header signature used to detect the true header row of the "billed"
# transactions table (עסקאות למועד חיוב) — the main, finalized-amount table.
ISRACARD_REQUIRED_HEADERS: set[str] = {
    "תאריך רכישה",
    "שם בית עסק",
    "סכום עסקה",
    "מטבע עסקה",
    "סכום חיוב",
    "מטבע חיוב",
    "פירוט נוסף",
}

# Some exports additionally include an earlier "not yet recorded" table
# (עסקאות שטרם נקלטו) for transactions with no billed amount yet — it has
# only these 4 columns, a subset of ISRACARD_REQUIRED_HEADERS above.
ISRACARD_PENDING_REQUIRED_HEADERS: set[str] = {
    "תאריך רכישה",
    "שם בית עסק",
    "סכום עסקה",
    "מטבע עסקה",
}

# Section title cells (first column) marking each table's start, when both
# are present in one export.
ISRACARD_PENDING_SECTION_TITLE = "עסקאות שטרם נקלטו"
ISRACARD_BILLED_SECTION_TITLE = "עסקאות למועד חיוב"

# Source header -> canonical mapping.
ISRACARD_SOURCE_TO_CANONICAL_COLUMN_MAP: dict[str, str] = {
    "תאריך רכישה": "Date",
    "שם בית עסק": "Payee",
    "סכום עסקה": "Original_amount",
    "מטבע עסקה": "Original_currency",
    "סכום חיוב": "Amount",
    "מטבע חיוב": "Currency_of_charge",
    "פירוט נוסף": "Additional_details",
}

# Optional memo source columns (source_col -> memo label).
ISRACARD_MEMO_SOURCE_COLUMNS: dict[str, str] = {
    "Original_currency": "Orig Currency",
    "Currency_of_charge": "Currency",
    "Additional_details": "Details",
    "Original_amount": "Original Amount",
}
