# Open YouTube Studio branding page in project Chrome profile for manual avatar upload.

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..\..")).Path
$ProfileDir = Join-Path $RepoRoot "workspace\dialogue_podcast_research\youtube_corpus\browser_profile\chrome_user_data"
$AvatarJpg = Join-Path $RepoRoot "workspace\dialogue_podcast_research\youtube_corpus\branding\channel_avatar_elr_800.jpg"
$ChannelId = "UC9QpAkVpv8l1ZQ3X4UtU37A"
$Url = "https://studio.youtube.com/channel/$ChannelId/editing/images"

New-Item -ItemType Directory -Force -Path $ProfileDir | Out-Null

$ChromeCandidates = @(
    "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)

$Chrome = $ChromeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $Chrome) {
    Write-Error "Google Chrome not found."
}

Write-Host "avatar=$AvatarJpg"
Write-Host "studio=$Url"
Write-Host ""
Write-Host "Steps:"
Write-Host "  1. In Studio -> Branding -> Profile picture -> Upload"
Write-Host "  2. Select channel_avatar_elr_800.jpg"
Write-Host "  3. Adjust crop if needed -> Done -> Publish"
Write-Host ""

if (Test-Path $AvatarJpg) {
    Start-Process explorer.exe -ArgumentList "/select,`"$AvatarJpg`""
}

Start-Process -FilePath $Chrome -ArgumentList @(
    "--user-data-dir=$ProfileDir",
    "--new-window",
    $Url
)

Write-Host "done=chrome_launched"
