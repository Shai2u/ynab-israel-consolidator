# S3 Setup For Multi-Machine Workflow

Use Git for code and S3 for shared data/artifacts between machines.

## What to Store in S3
- Raw source files (CSV/XLSX) for ingestion.
- Audit artifacts (label review tables, parse issues).
- Processed outputs (canonical tables, reports).

Recommended prefixes inside bucket:
- `raw/`
- `audit/`
- `processed/`
- `reports/`

## Prerequisites
- AWS CLI installed on each machine.
- Auth configured via AWS profile/SSO (recommended) or IAM user credentials.
- Existing bucket (you already created one).

## Environment Variables (No Secrets in Repo)
Set these locally on each machine:
- `YNAB_CONSOLIDATOR_S3_BUCKET` (required)
- `AWS_PROFILE` (recommended)
- `AWS_REGION` (optional if profile already has one)
- `YNAB_CONSOLIDATOR_S3_PREFIX` (optional, defaults to `ynab-israel-consolidator/data/`)

PowerShell example (current session):
```powershell
$env:YNAB_CONSOLIDATOR_S3_BUCKET = "your-bucket-name"
$env:AWS_PROFILE = "your-profile"
$env:AWS_REGION = "eu-west-1"
$env:YNAB_CONSOLIDATOR_S3_PREFIX = "ynab-israel-consolidator/data/"
```

Bash/zsh example (current session):
```bash
export YNAB_CONSOLIDATOR_S3_BUCKET="your-bucket-name"
export AWS_PROFILE="your-profile"
export AWS_REGION="eu-west-1"
export YNAB_CONSOLIDATOR_S3_PREFIX="ynab-israel-consolidator/data/"
```

## Sync Scripts
Two wrappers are provided:
- Windows: `scripts/s3_sync.ps1`
- macOS/Linux: `scripts/s3_sync.sh`

Both scripts sync local `data/` with:
- `s3://$YNAB_CONSOLIDATOR_S3_BUCKET/$YNAB_CONSOLIDATOR_S3_PREFIX`

### Upload local data to S3
PowerShell:
```powershell
./scripts/s3_sync.ps1 up
```

Bash/zsh:
```bash
bash ./scripts/s3_sync.sh up
```

### Download shared data from S3
PowerShell:
```powershell
./scripts/s3_sync.ps1 down
```

Bash/zsh:
```bash
bash ./scripts/s3_sync.sh down
```

## Safety Notes
- Do not commit credentials, keys, or secret tokens.
- Prefer short-lived credentials (`aws sso login`) over long-lived keys.
- Bucket access should be least-privilege (only needed read/write prefixes).
- Code remains in Git; S3 is for datasets/artifacts.
