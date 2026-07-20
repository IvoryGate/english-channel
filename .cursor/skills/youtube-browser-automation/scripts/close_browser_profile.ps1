# Close Chrome processes that lock the project YouTube profile.
# Run before Playwright automation if a prior manual Chrome window was left open.

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$ProfileMarker = "dialogue_podcast_research\youtube_corpus\browser_profile\chrome_user_data"

$targets = Get-CimInstance Win32_Process -Filter "name='chrome.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -like "*$ProfileMarker*" }

if (-not $targets) {
    Write-Host "closed=0 (no Chrome using project profile)"
    exit 0
}

$ids = $targets | Select-Object -ExpandProperty ProcessId -Unique
foreach ($id in $ids) {
    Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
}
Write-Host "closed=$($ids.Count) profile_chrome_pids=$($ids -join ',')"
