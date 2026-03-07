# Tasks

Use this file as the current execution board.

## In Progress
- Define canonical consolidation rules aligned with YNAB-oriented columns.

## Next
- Build `ingest` CLI:
  - Scan CSV/XLSX files (including sheet handling).
  - Run deterministic source detection.
  - Export label-audit table for manual corrections.
- Build `normalize` CLI:
  - Read corrected labels.
  - Parse source files into canonical table.
  - Add required columns: `Ownership`, `Account`, `Memo`, `Outflow`, `Inflow`, `Cleared`.
  - Add date range filter (`--from`, `--to`).
- Add robust date parsing utility for mixed formats.
- Add issue artifact export for parse anomalies (no silent row loss).
- Create first parser fixture set from real Israeli source files.

## Done
- Confirmed remote setup via SSH alias and `origin` remote.
- Verified local branch and remote branch currently match.
- Captured v1 schema intent for YNAB-aligned consolidation fields.
- Added debug `launch.json` template blocks for planned CLIs.
- Added persistent work logging and task tracking docs (`WORKLOG.md`, `TASKS.md`).
- Added S3 multi-machine sync setup doc and cross-platform sync scripts.
- Added `.gitignore` rules to prevent committing private transaction data files.
- Added `.env.example` and private `.env` contract for S3/AWS local configuration.
- Added private ETL practice-data convention (`private_data/`) and init scripts.
- Added canonical account/ownership registry and aligned folder/template labels.
