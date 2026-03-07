#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: bash ./scripts/s3_sync.sh <up|down>"
  exit 1
fi

DIRECTION="$1"
if [[ "$DIRECTION" != "up" && "$DIRECTION" != "down" ]]; then
  echo "Direction must be 'up' or 'down'"
  exit 1
fi

if [[ -z "${YNAB_CONSOLIDATOR_S3_BUCKET:-}" ]]; then
  echo "Missing env var YNAB_CONSOLIDATOR_S3_BUCKET"
  exit 1
fi

S3_PREFIX="${YNAB_CONSOLIDATOR_S3_PREFIX:-ynab-israel-consolidator/data/}"

if ! command -v aws >/dev/null 2>&1; then
  echo "AWS CLI not found. Install AWS CLI first."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCAL_DATA="$REPO_ROOT/data"
S3_PATH="s3://${YNAB_CONSOLIDATOR_S3_BUCKET}/${S3_PREFIX}"

mkdir -p "$LOCAL_DATA"

if [[ "$DIRECTION" == "up" ]]; then
  echo "Uploading $LOCAL_DATA -> $S3_PATH"
  aws s3 sync "$LOCAL_DATA" "$S3_PATH" --exact-timestamps
else
  echo "Downloading $S3_PATH -> $LOCAL_DATA"
  aws s3 sync "$S3_PATH" "$LOCAL_DATA" --exact-timestamps
fi

echo "Sync complete."
