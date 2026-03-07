# Consolidation Schema (v1)

This file defines the current target output schema for source-file consolidation before full reconciliation.

## Scope
- Script-first deterministic ETL (pandas).
- Auto-detect source format, then support manual audit/correction of labels.
- Consolidate all accounts into one long dataframe aligned to YNAB-like columns.

## Canonical Columns (v1)

### `Ownership`
- Type: string
- Required: yes
- Allowed values (current): `Shai (Private)`, `Shai & Nirit (Joint)`
- Meaning: ownership context for account/transaction.

### `Account`
- Type: string
- Required: yes
- Meaning: account source identifier (bank name or credit-card vendor).
- Current controlled values are listed in `ACCOUNT_REGISTRY.md`.

### `Flag`
- Type: string
- Required: no
- Default: empty string
- Meaning: YNAB-style flag; not a priority in v1 consolidation.

### `Date`
- Type: date (normalized)
- Required: yes
- Meaning: transaction date from source data.
- Parsing rules:
  - accept mixed formats per source;
  - keep deterministic parsing logic;
  - if parsing fails, record explicit parse issue (no silent drop).

### `Payee`
- Type: string
- Required: yes (fallback empty string if unavailable)
- Meaning: main transaction action/description.

### `Category Group/Category`
- Type: string
- Required: no
- Default: empty string
- Meaning: intentionally empty in v1.

### `Category Group`
- Type: string
- Required: no
- Default: empty string
- Meaning: intentionally empty in v1.

### `Category`
- Type: string
- Required: no
- Default: empty string
- Meaning: intentionally empty in v1.

### `Memo`
- Type: string
- Required: no
- Meaning: extra details derived from source data using concatenation and conditional formatting rules.
- Notes:
  - intended place for payment/installment context and source extras;
  - exact per-source rules will be added as fixtures and parser tests are introduced.

### `Outflow`
- Type: decimal-like numeric (export-ready)
- Required: yes (can be zero)
- Meaning: amount spent.
- Rule: for inflow rows, set `Outflow = 0`.

### `Inflow`
- Type: decimal-like numeric (export-ready)
- Required: yes (can be zero)
- Meaning: amount received.
- Rule: for outflow rows, set `Inflow = 0`.

### `Cleared`
- Type: string
- Required: no in v1, planned required in reconciliation stage
- Meaning: audit/reconciliation status indicator and future registration-quality marker.

## Operational Rules
- Preserve row traceability to source file and source row in intermediate artifacts.
- Preserve original columns as raw/extras in intermediate artifacts.
- Never silently coerce or drop malformed rows; write issue artifacts explicitly.
- Keep deterministic behavior as source of truth; use agent fallback only for unresolved anomalies.

## Planned Extensions
- Django UI over same deterministic ETL core.
- Category inference/matching as a separate future module.
- More advanced anomaly handlers for inconsistent start rows and multi-sheet edge cases.
