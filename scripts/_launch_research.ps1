$ErrorActionPreference = "Continue"
Set-Location "h:\english-channel"
$py = ".conda-env\python.exe"
if (-not (Test-Path $py)) { $py = "python" }
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$log = "logs\research_refresh_maxandmia_$ts.log"
"start: $((Get-Date).ToString('o'))" | Out-File -FilePath $log -Encoding utf8
& $py -u scripts\run_research_refresh.py --channel maxandmiapodcast *>&1 | Tee-Object -FilePath $log
"exit=$LASTEXITCODE" | Out-File -FilePath $log -Encoding utf8 -Append
"done: $((Get-Date).ToString('o'))" | Out-File -FilePath $log -Encoding utf8 -Append
