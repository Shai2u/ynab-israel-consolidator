"""Max Uniq-specific parsing and mapping constants (prototype)."""

# Canonical account name in ACCOUNT_REGISTRY.md.
MAX_UNIQ_ACCOUNT_NAME = "Max Uniq"

# Fill this once you confirm the export date pattern(s), e.g. "%d/%m/%Y".
MAX_UNIQ_INPUT_DATE_FORMAT = ""

# Fill this with required header values for header row detection.
MAX_UNIQ_REQUIRED_HEADERS: set[str] = set()

# Fill this with source header mappings once discovered.
MAX_UNIQ_SOURCE_TO_CANONICAL_COLUMN_MAP: dict[str, str] = {}
