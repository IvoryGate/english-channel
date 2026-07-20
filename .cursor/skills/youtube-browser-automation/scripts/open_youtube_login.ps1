# Open Google Chrome with the project YouTube profile (no Playwright automation flags).
# Use this when Google blocks "This browser or app may not be secure".

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path

$ProfileDir = Join-Path $RepoRoot "workspace\dialogue_podcast_research\youtube_corpus\browser_profile\chrome_user_data"
New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

$ChromeCandidates = @(
    "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)

$Chrome = $ChromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Chrome) {
    Write-Error "Google Chrome not found. Install Chrome, then rerun this script."
}

$Url = "https://studio.youtube.com/"
Write-Host "profile=$ProfileDir"
Write-Host "Opening Chrome for manual YouTube login..."
Write-Host "1. Sign in with your channel Google account"
Write-Host "2. Confirm YouTube Studio loads"
Write-Host "3. Close Chrome when done (cookies stay in profile dir)"

Start-Process -FilePath $Chrome -ArgumentList @(
    "--user-data-dir=$ProfileDir",
    "--new-window",
    $Url
)

Write-Host "done=chrome_launched"
