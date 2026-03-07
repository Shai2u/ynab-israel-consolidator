#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

paths=(
  "private_data"
  "private_data/incoming"
  "private_data/incoming/bank_leumi_private_shai"
  "private_data/incoming/bank_hapoalim_private_shai"
  "private_data/incoming/mizrachi_joint"
  "private_data/incoming/max_uniq_joint"
  "private_data/incoming/isracard_4054_joint"
  "private_data/incoming/mastercard_4779_private"
  "private_data/incoming/mastercard_7353_private"
  "private_data/labeled"
  "private_data/normalized"
  "private_data/issues"
)

for path in "${paths[@]}"; do
  full_path="$REPO_ROOT/$path"
  if [[ ! -d "$full_path" ]]; then
    mkdir -p "$full_path"
    echo "Created: $path"
  else
    echo "Exists:  $path"
  fi
done

echo "Private data workspace ready."
