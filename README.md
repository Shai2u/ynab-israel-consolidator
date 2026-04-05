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

## Future Feature: Credit Card Settlement Matching
- Goal: match credit card statement totals/charges against corresponding bank account transactions (card settlement payments).
- Important constraint: settlement dates often do not exactly match card transaction dates, and grouped totals may differ from simple per-day sums.
- Current status: **not implemented in v1 prototype ETL**.
- Planned approach (future):
  - deterministic matching only (amount windows + settlement date windows + explicit tie-break rules),
  - explicit confidence/scoring artifacts,
  - no hidden inference in runtime.

## Product Roadmap

Steps are ordered by dependency. All matching and scoring steps are fully deterministic Python — no LLM in the reconciliation loop. LLM is reserved only for the final reflective reporting step.

---

### Step 1 — YNAB Integration ✅ (partial)
- Normalize YNAB CSV exports to a comparable canonical schema.
- Merge YNAB register with the consolidated source DataFrame into one view.

### Step 2 — Filtering
- Filter the consolidated DataFrame by Date range and/or Account.
- Output a filtered slice usable for reconciliation or review.

### Step 3 — Input Selection (CLI)
- Prompt-based input: choose which source folders to include in a given run.
- Support both interactive prompt and argument-based invocation.

### Step 4 — Auto-detect Source from Input
- Infer source account/format from file signature (header row pattern, filename pattern).
- Match against known registry; fall back to manual selection if unknown.

### Step 5 — Django UI (MVP)
1. File input: upload source files; auto-detect or select from menu; add new sources.
2. Consolidated table view: display all normalized transactions in one paginated table.
3. Filter panel: filter by Account and/or Date range.

**Storage design (cost-first):**
- User uploads are stored in a small ephemeral area (target: ≤ 100 MB per user session).
- Uploaded files and processed outputs are auto-deleted after a short TTL (e.g. 24–48 hours).
- No long-term transaction storage on the server — the source of truth stays with the user's local export files.
- Goal: keep hosting free or near-free (e.g. Railway, Fly.io, Render free tier) with no database storage costs for raw file data.
- If persistent storage is ever needed (e.g. error logs, quality scores), use a minimal append-only table with a row limit, not raw file storage.

### Step 6 — Auto-match & Fingerprinting
- Generate a deterministic fingerprint per transaction (date + amount + payee hash).
- Match source rows against YNAB register rows using fingerprint.
- Color-code rows: perfect match / partial match / unmatched.
- New column: `match_status` (PERFECT / PARTIAL / MISSING / EXTRA).

### Step 7 — Registration Quality Score
- Assign a 1–10 quality score per registration using an explicit weighted formula.
- Reward: perfect date + amount + payee match.
- Penalize: partial match, major mismatch, missing registration (strongest penalty).
- Display score as a column; aggregate into a monthly health metric.

### Step 8 — Fuzzy Matching (Easement)
- Relax matching rules with configurable date window (e.g. ±2 days) and amount tolerance.
- Update fingerprint and scoring to reflect eased match confidence.
- All rules remain deterministic — no hidden inference.

### Step 9 — Error Classification & Learning Log
Classify every non-perfect match into one of these error types (deterministic rules only):

- **a. Not Registered** — source row exists but no corresponding YNAB entry found.
  Critical: user is unaware of the expense or forgot to register it.
- **b. Wrong Account** — registration exists but was booked to the wrong account.
- **c. Small Errors** — registration exists and account is correct but amount is off:
  - Rounding error (registered by memory, e.g. 7 instead of 7.24)
  - Decimal shift (e.g. 7.24 instead of 724)
  - Anagram/transposition error (e.g. 7.42 instead of 7.24)
  - Total mismatch (date matches, row count matches, but amount is simply wrong)

Log every classified error to a structured file/database for pattern analysis:
- Track error type frequency per month.
- Surface patterns: most common mistake, improvement trend, persistent blind spots.

> **Agent boundary**: error detection and logging in Step 9 is fully deterministic.
> The agent enters only in Step 10 to reflect on the logged patterns.

### Step 10 — Credit Card ↔ Bank Settlement Matching
- Deterministic date-window + amount-window matching of credit card monthly totals against bank debit entries.
- Constraint: settlement date ≠ transaction date; grouped totals may not equal simple per-day sums.
- All rules explicit and auditable; no inference.
- See also: [Future Feature: Credit Card Settlement Matching](#future-feature-credit-card-settlement-matching).

### Step 11 — Agent: Habit Reflection (Final Stage)
- The only step where LLM tokens are spent.
- Input: pre-aggregated error logs and quality scores (never raw transaction rows).
- Output: short narrative reflecting on registration habits, month-over-month improvement, and recurring mistake patterns.
- No per-transaction decisions — agent sees summaries only.
- Goal: save money on tokens while still getting actionable personal insight.

---

**End state**: everything above running behind a secured Django web interface, accessible from any device. Script-first mode preserved for power users and debugging.

## YNAB-Oriented Consolidated Columns (Current v1 intent)
- `Ownership`:
  - Who owns the account/transaction context, e.g. `Shai (Private)` or `Shai & Nirit (Joint)`.
- `Account`:
  - Source account identifier from institution context (bank name or credit card vendor).
- `Flag`:
  - Mostly YNAB-native; expected to be empty or default in consolidation v1.
- `Date`:
  - Transaction date, normalized from source-specific formats.
  - Final output format target: `dd/mm/YYYY` (example: `28/03/2026`).
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
