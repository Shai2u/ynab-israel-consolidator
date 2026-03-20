"""Mastercard 4779-specific parsing and mapping constants (prototype)."""

# Canonical account name in ACCOUNT_REGISTRY.md.
MASTERCARD_4779_ACCOUNT_NAME = "Mastercard 4779"

# Fill this once you confirm the export date pattern(s), e.g. "%d/%m/%Y".
MASTERCARD_4779_INPUT_DATE_FORMAT = ""

# Fill this with required header values for header row detection.
MASTERCARD_4779_REQUIRED_HEADERS: set[str] = set()

# Fill this with source header mappings once discovered.
MASTERCARD_4779_SOURCE_TO_CANONICAL_COLUMN_MAP: dict[str, str] = {}
