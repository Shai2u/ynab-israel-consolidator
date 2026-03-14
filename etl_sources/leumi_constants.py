"""Leumi-specific parsing and mapping constants (prototype)."""

# Canonical account name in ACCOUNT_REGISTRY.md.
LEUMI_ACCOUNT_NAME = "Bank Leumi"

# Confirmed Leumi export date format (dd/mm/YYYY).
LEUMI_INPUT_DATE_FORMAT = "%d/%m/%Y"

# Fill this with Leumi Hebrew/source header mappings once discovered.
LEUMI_SOURCE_TO_CANONICAL_COLUMN_MAP: dict[str, str] = {    
    "תאריך": "Date",
    "תיאור": "Payee",
    "בזכות": "Inflow",
    "בחובה": "Outflow",
    "הערה": "Memo"
}
# Translation from Mizrachi Hebrew headers to canonical/intermediate names.

