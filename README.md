# Financial Reconciliation (Deterministic, Low-Cost)

A deterministic Python pipeline for reconciling Israeli bank/credit-card exports against YNAB exports.

## Core Goal
Normalize many source export formats (CSV/Excel) into one strict canonical transactions table, then reconcile against YNAB with deterministic matching and transparent scoring.

## Design Principles
- Deterministic runtime engine in Python (`pandas`, tests, fixed rules).
- LLM is **not** used in per-transaction runtime logic.
- LLM is used only for:
  - generating/updating parser code + tests when a new source format appears
  - optional final narrative report text from pre-aggregated metrics
- Full auditability:
  - preserve raw rows and original columns
  - never silently drop/coerce malformed rows
  - collect parse/match issues as explicit artifacts

## Planned Pipeline
1. `import_sources <files...>`
   - Read CSV/XLSX
   - Detect format via signature registry
   - Route to versioned parser
   - Output canonical transactions + audit artifacts
2. `import_ynab <file>`
   - Normalize YNAB CSV to a comparable schema
3. `reconcile`
   - Deterministic candidate generation + scoring
   - Classify: PERFECT, PARTIAL, MAJOR ERROR, MISSING
   - Detect duplicates
4. `export_report`
   - Export machine-readable JSON/CSV summaries
   - Optional narrative text generated from aggregates only

## Canonical Transaction Schema (target)
- `source_institution` (str)
- `source_account_id` (str)
- `source_file_id` (str)
- `source_row_id` (str/int)
- `txn_date` (datetime64[ns], date preferred)
- `posted_date` (datetime64[ns] or NaT)
- `amount` (int, agorot/cents; outflow negative)
- `currency` (str)
- `merchant_raw` (str)
- `description_raw` (str)
- `merchant_normalized` (str or NaN)
- `category_raw` (str or NaN)
- `is_installment` (bool)
- `installment_number` (int or NaN)
- `installment_total` (int or NaN)
- `reference` (str or NaN)
- plus preserved extras/raw original columns (JSON/raw table)

## Matching & Rating (deterministic)
- Candidate window: same amount or near-amount + date window (e.g., ±2 days)
- Stable weighted score with deterministic tie-breakers
- Duplicate detection for many-to-one candidates
- 1–10 registration quality score from explicit formula:
  - reward perfect matches
  - penalize partial, major, and missing (strongest penalty)

## Project Status
Scaffold phase. Core modules, parser registry, matcher, CLI, and tests are next.

## Required Inputs Before Parser Build-Out
- One real header row per institution/source format
- Canonical account naming convention
- Exact YNAB export header row in current usage
