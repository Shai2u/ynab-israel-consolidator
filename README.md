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

## Future Direction (Product + Workflow)
- Start as a script-first ETL pipeline for speed and control.
- Auto-identify file source labels (bank/card format) without manual pre-labeling.
- Produce an audit step where labeling can be reviewed and corrected.
- After labels are approved, normalize all sources into one long consolidated dataframe.
- Handle common ETL cases deterministically in pandas first; use agent support only as fallback for persistent anomalies.
- Reuse the same deterministic core later behind a Django UI.
- Support date-range filtering in both script mode and future UI mode.

## YNAB-Oriented Consolidated Columns (Current v1 intent)
- `Ownership`:
  - Who owns the account/transaction context, e.g. `Shai` or `Shai & Nirit - Joint`.
- `Account`:
  - Source account identifier from institution context (bank name or credit card vendor).
- `Flag`:
  - Mostly YNAB-native; expected to be empty or default in consolidation v1.
- `Date`:
  - Transaction date, normalized from source-specific formats.
- `Payee`:
  - Main transaction description/action field.
- `Category Group/Category`, `Category Group`, `Category`:
  - Kept empty in v1 external-source consolidation flow.
- `Memo`:
  - Extra contextual field built from source data via concatenation/conditional formatting rules.
- `Outflow` / `Inflow`:
  - Directional amounts (`Outflow` = money spent, `Inflow` = money received).
- `Cleared`:
  - Audit/status field used to evaluate reconciliation quality and registration accuracy.

## Project Operating Docs
- `WORKLOG.md`:
  - Session-by-session log (date/time, machine, editor, tasks completed, next tasks).
  - Append one entry at the end of every working session.
- `TASKS.md`:
  - Single source of truth for current TODO, in-progress, and done items.
  - Keep items short and actionable.
- `SCHEMA.md`:
  - Current consolidation schema contract and field-level normalization rules.
- `ACCOUNT_REGISTRY.md`:
  - Canonical bank/card account names and ownership labels for ETL mapping.
- `S3_SETUP.md`:
  - How to share datasets/artifacts across machines using S3 securely.
- `PRACTICE_DATA.md`:
  - How to organize private ETL practice datasets outside Git tracking.

These docs are intended to keep work synchronized across machines (macOS/Windows) and editors (Cursor/VSCode).

## Data Privacy Rule
- Private transaction files must not be committed to GitHub.
- `.gitignore` blocks common financial data paths and file types (`csv`, `xls`, `xlsx`), including `private_data/`.
- Use S3 for cross-machine data sharing, and keep code/documentation in Git.

## Private `.env` Contract
Store machine-specific values in `.env` (private, untracked), based on `.env.example`:
- `YNAB_CONSOLIDATOR_S3_BUCKET` (required)
- `AWS_PROFILE` (recommended)
- `AWS_REGION` (optional if profile already defines it)
- `YNAB_CONSOLIDATOR_S3_PREFIX` (optional; defaults to project data prefix)

Do not store transaction content, exported CSV/XLSX data, or long-lived AWS keys in Git-tracked files.
