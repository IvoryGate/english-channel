# Series B episode 001 — full pack (QC → master → subs → compose → export)
# Run in YOUR terminal (Cursor terminal panel or external PowerShell).
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$log = Join-Path (Get-Location) "logs\series_b_ep001_pack.log"
New-Item -ItemType Directory -Force -Path logs | Out-Null

Write-Host "Log: $log"
Write-Host ""

& .\.conda-env\python.exe -u scripts\run_episode_pack.py `
  --show series_b `
  --episode episode_001 `
  --workspace workspace\shows\series_b\episode_001 `
  --episode-num 1 `
  --log $log `
  --skip-master `
  --qc-no-asr

Write-Host ""
Write-Host "Done. Log: $log"
