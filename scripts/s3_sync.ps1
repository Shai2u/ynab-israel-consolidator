param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("up", "down")]
    [string]$Direction
)

$ErrorActionPreference = "Stop"

$bucket = $env:YNAB_CONSOLIDATOR_S3_BUCKET
if (-not $bucket) {
    throw "Missing env var YNAB_CONSOLIDATOR_S3_BUCKET"
}

$prefix = $env:YNAB_CONSOLIDATOR_S3_PREFIX
if (-not $prefix) {
    $prefix = "ynab-israel-consolidator/data/"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$localData = Join-Path $repoRoot "data"
$s3Path = "s3://$bucket/$prefix"

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw "AWS CLI not found. Install AWS CLI first."
}

if (-not (Test-Path $localData)) {
    New-Item -ItemType Directory -Path $localData | Out-Null
}

if ($Direction -eq "up") {
    Write-Host "Uploading $localData -> $s3Path"
    aws s3 sync "$localData" "$s3Path" --exact-timestamps
} else {
    Write-Host "Downloading $s3Path -> $localData"
    aws s3 sync "$s3Path" "$localData" --exact-timestamps
}

Write-Host "Sync complete."
