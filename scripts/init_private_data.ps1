$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$paths = @(
    "private_data",
    "private_data/incoming",
    "private_data/incoming/bank_leumi_private_shai",
    "private_data/incoming/bank_hapoalim_private_shai",
    "private_data/incoming/mizrachi_joint",
    "private_data/incoming/max_uniq_joint",
    "private_data/incoming/isracard_4054_joint",
    "private_data/incoming/mastercard_4779_private",
    "private_data/incoming/mastercard_7353_private",
    "private_data/labeled",
    "private_data/normalized",
    "private_data/issues"
)

foreach ($path in $paths) {
    $fullPath = Join-Path $repoRoot $path
    if (-not (Test-Path $fullPath)) {
        New-Item -ItemType Directory -Path $fullPath | Out-Null
        Write-Host "Created: $path"
    } else {
        Write-Host "Exists:  $path"
    }
}

Write-Host "Private data workspace ready."
