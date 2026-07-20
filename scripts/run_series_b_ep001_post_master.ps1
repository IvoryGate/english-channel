# Post-master pack: subtitles -> compose -> export (Series B episode 001)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$log = "logs/series_b_ep001_post_master.txt"
$err = "logs/series_b_ep001_post_master_err.txt"
New-Item -ItemType Directory -Force -Path logs | Out-Null

Write-Host "Log: $log"
Write-Host "Err: $err"
Write-Host "Starting post-master pipeline..."

$py = (Resolve-Path ".\.conda-env\python.exe").Path
$script = (Resolve-Path ".\workspace\shows\tools\run_episode_post_master.py").Path
$ws = (Resolve-Path ".\workspace\shows\series_b\episode_001").Path

$env:KMP_DUPLICATE_LIB_OK = "TRUE"

& $py $script `
  --show series_b `
  --episode episode_001 `
  --workspace $ws `
  --episode-num 1 `
  2>&1 | Tee-Object -FilePath $log
