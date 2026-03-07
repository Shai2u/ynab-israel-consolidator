# Work Log

Session notes for cross-machine and cross-editor continuity.

## Entry Template
- Date:
- Time:
- Timezone:
- Machine: (mac personal / windows org)
- Editor: (Cursor / VSCode)
- Branch:
- Goal:
- Tasks completed:
  - 
- Decisions:
  - 
- Files touched:
  - 
- Open issues:
  - 
- Next session tasks:
  - 

---

## 2026-03-05
- Date: 2026-03-05
- Time: evening
- Timezone: local
- Machine: windows org
- Editor: Cursor
- Branch: `main`
- Goal: define ingestion module direction and operational workflow.
- Tasks completed:
  - Configured and verified Git remote usage with SSH alias (`origin`).
  - Confirmed local `main` matches `origin/main`.
  - Defined phase-1 ingestion strategy: auto detect source, audit/fix labels, normalize into one table.
  - Captured initial YNAB-style target columns and field intent.
  - Added `launch.json` debug template blocks for planned CLI commands.
  - Added `SCHEMA.md` with v1 consolidated field contract and normalization rules.
  - Added S3 sharing setup documentation and sync wrapper scripts for Windows/macOS.
  - Added `.gitignore` policy to block private CSV/XLSX and data folders from Git.
  - Added `.env.example` template and private `.env` keys contract for local machine config.
  - Added private practice-data convention doc and folder bootstrap scripts.
  - Added canonical account registry and updated ownership labels to private/joint naming.
  - Added final date output requirement: `dd/mm/YYYY`.
- Decisions:
  - Keep runtime deterministic (pandas ETL first); agent fallback is optional and controlled.
  - Keep category fields empty for now in consolidated output.
  - Use `Memo` for concatenated/conditional extra source data.
  - Include `Ownership` and `Account` as required columns in normalization.
  - Final consolidated date output should be `dd/mm/YYYY`.
- Files touched:
  - `README.md`
  - `SCHEMA.md`
  - `S3_SETUP.md`
  - `.gitignore`
  - `.env.example`
  - `PRACTICE_DATA.md`
  - `ACCOUNT_REGISTRY.md`
  - `scripts/s3_sync.ps1`
  - `scripts/s3_sync.sh`
  - `scripts/init_private_data.ps1`
  - `scripts/init_private_data.sh`
  - `AGENTS.md` (reviewed policy boundaries)
- Open issues:
  - No parser code scaffold implemented yet.
  - No fixtures for Israeli account exports added yet.
- Next session tasks:
  - Add initial CLI scaffold (`ingest`, `normalize`, `issues`).
  - Add detector + label-audit CSV flow.
  - Add first source parser + tests using sample files.
