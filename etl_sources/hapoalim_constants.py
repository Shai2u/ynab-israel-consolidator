"""Hapoalim-specific parsing and mapping constants (prototype)."""

# Canonical account name in ACCOUNT_REGISTRY.md.
HAPOALIM_ACCOUNT_NAME = "Bank Hapoalim"

# Fill this once you confirm the export date pattern(s), e.g. "%d/%m/%Y".
HAPOALIM_INPUT_DATE_FORMAT =  "%Y-%m-%d %H:%M:%S"

HAPOALIM_REQUIRED_HEADERS = {"עבור", "לטובת", "זכות", "חובה", "פרטים", "הפעולה", "תאריך"}


# Fill this with Hapoalim source header mappings once discovered.
HAPOALIM_SOURCE_TO_CANONICAL_COLUMN_MAP: dict[str, str] = {"עבור": "From Whom", 
        "לטובת": "To Whom 2",
        "זכות": "Inflow",
        "חובה": "Outflow", 
        "פרטים": "Details",
        "הפעולה": "Payee", 
        "תאריך": "Date"}

