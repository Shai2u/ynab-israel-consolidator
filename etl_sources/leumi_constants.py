"""Leumi-specific parsing and mapping constants (prototype)."""

# Canonical account name in ACCOUNT_REGISTRY.md.
LEUMI_ACCOUNT_NAME = "Bank Leumi"

# Fill this once you confirm the export date pattern(s), e.g. "%d/%m/%Y".
LEUMI_INPUT_DATE_FORMAT = ""

# Fill this with Leumi Hebrew/source header mappings once discovered.
LEUMI_SOURCE_TO_CANONICAL_COLUMN_MAP: dict[str, str] = {}
