# Batch-render Series B episode turns (hardware-safe: reload model every N turns).
# Do not use ErrorAction Stop around python — VoxCPM logs to stderr.
$Repo = "h:\english-channel"
$Py = "$Repo\.conda-env\python.exe"
$Manifest = "$Repo\workspace\shows\series_b\episode_001\000_episode_001.episode_manifest.json"
$Ws = "$Repo\workspace\shows\series_b\episode_001"
$Log = "$Repo\logs\series_b_episode_001_render.log"
$BatchSize = 10
$Total = 134

New-Item -ItemType Directory -Force -Path (Split-Path $Log) | Out-Null
Remove-Item Env:PYTORCH_CUDA_ALLOC_CONF -ErrorAction SilentlyContinue
$env:KMP_DUPLICATE_LIB_OK = "TRUE"

function Get-MissingIds {
  $missing = New-Object System.Collections.Generic.List[string]
  for ($i = 1; $i -le $Total; $i++) {
    $wav = Join-Path $Ws ("turn_{0:d3}.wav" -f $i)
    if (-not (Test-Path $wav)) {
      [void]$missing.Add(("p{0:d3}" -f $i))
    }
  }
  return $missing
}

$start = Get-Date
Add-Content -Path $Log -Value "[$start] resume batch render start" -Encoding utf8

while ($true) {
  $missing = @(Get-MissingIds)
  if ($missing.Count -eq 0) {
    Add-Content -Path $Log -Value "[$(Get-Date)] all $Total turns present" -Encoding utf8
    break
  }
  $endIdx = [Math]::Min($BatchSize, $missing.Count) - 1
  $batch = @($missing[0..$endIdx])
  $seg = ($batch -join ",")
  Add-Content -Path $Log -Value "[$(Get-Date)] batch $($batch[0])..$($batch[-1]) remaining=$($missing.Count)" -Encoding utf8

  $argList = @(
    "-u",
    "$Repo\workspace\shows\tools\render_episode.py",
    "--manifest", $Manifest,
    "--device", "cuda",
    "--segments", $seg
  )
  $p = Start-Process -FilePath $Py -ArgumentList $argList -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput "$Repo\logs\series_b_batch_stdout.txt" `
    -RedirectStandardError "$Repo\logs\series_b_batch_stderr.txt"
  Get-Content "$Repo\logs\series_b_batch_stdout.txt","$Repo\logs\series_b_batch_stderr.txt" -ErrorAction SilentlyContinue |
    Add-Content -Path $Log -Encoding utf8

  $code = $p.ExitCode
  Add-Content -Path $Log -Value "[$(Get-Date)] batch exit=$code" -Encoding utf8
  if ($code -ne 0) {
    $next = @(Get-MissingIds) | Select-Object -First 1
    Add-Content -Path $Log -Value "[$(Get-Date)] STOP after failure; resume later from $next" -Encoding utf8
    exit $code
  }
  Start-Sleep -Seconds 3
}

Add-Content -Path $Log -Value "[$(Get-Date)] done elapsed=$((Get-Date) - $start)" -Encoding utf8
exit 0
