# Practice Data Workflow (Private)

Use this for ETL development datasets (not model training).  
Preferred term in this project: **practice datasets** or **ETL development fixtures**.

## Goal
- Keep real/private transaction files organized for iterative ETL building.
- Keep all such files out of GitHub.
- Allow repeatable runs across multiple machines.

## Local Folder Convention
Create this local structure in repo root (all ignored by Git):

```text
private_data/
  incoming/
    bank_leumi_private_shai/
    bank_hapoalim_private_shai/
    mizrachi_joint/
    max_uniq_joint/
    isracard_4054_joint/
    mastercard_4779_private/
    mastercard_7353_private/
  labeled/
    manifest.csv
  normalized/
  issues/
```

Notes:
- `incoming/`: raw files as exported from institutions.
- `labeled/manifest.csv`: your reviewed source labels and metadata.
- `normalized/`: ETL outputs for inspection.
- `issues/`: parse errors and anomaly reports.

## Naming Convention (Recommended)
- Source files:
  - `<source>_<account>_<yyyy-mm>.csv`
  - `<source>_<account>_<yyyy-mm>.xlsx`
- Examples:
  - `leumi_shai_2026-02.xlsx`
  - `isracard_4054_joint_2026-01.csv`

## Cross-Machine Flow
- Keep code/docs in Git.
- Keep private data in `private_data/` locally.
- Use S3 sync scripts for sharing data between machines when needed.

## Safety Rules
- Never commit files from `private_data/`.
- Never paste raw transaction rows into tracked markdown files.
- Use sanitized examples only if you later add test fixtures.
