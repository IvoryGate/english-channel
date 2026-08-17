# Resume episode_003 — delegates to resume_episode_production.py (GPU lock, resume-safe).
# Skips series whose mp4 already exists; batch-size 1 enforced.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

$py = ".\.conda-env\python.exe"
& $py scripts/resume_episode_production.py `
    --episode episode_003 `
    --episode-num 3 `
    --detach
exit $LASTEXITCODE
