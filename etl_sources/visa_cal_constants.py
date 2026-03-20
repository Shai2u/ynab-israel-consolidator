"""Mastercard 4779-specific parsing and mapping constants (prototype)."""

# Canonical account name in ACCOUNT_REGISTRY.md.
VISA_CAL_ACCOUNT_NAME = "Visa Cal"

# Fill this once you confirm the export date pattern(s), e.g. "%d/%m/%Y".
VISA_CAL_INPUT_DATE_FORMAT = ""

# Fill this with required header values for header row detection.
VISA_CAL_REQUIRED_HEADERS: set[str] = set()

# Fill this with source header mappings once discovered.
VISA_CAL_SOURCE_TO_CANONICAL_COLUMN_MAP: dict[str, str] = {}
