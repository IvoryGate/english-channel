param(
  [string]$SourceEnv = "base",
  [string]$EnvPrefix = ".conda-env",
  [string]$ModelDir = "pretrained_models/VoxCPM2",
  [switch]$UseHfMirror,
  [switch]$SkipModelDownload
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $ProjectRoot

if ($UseHfMirror) {
  $env:HF_ENDPOINT = "https://hf-mirror.com"
}

$python = Join-Path $ProjectRoot "$EnvPrefix\python.exe"

if (-not (Test-Path $python)) {
  Write-Host "Cloning conda environment '$SourceEnv' into project path '$EnvPrefix' ..."
  & conda create --prefix $EnvPrefix --clone $SourceEnv -y
}

Write-Host "Checking project-local runtime ..."
& $python -c "import torch; from voxcpm import VoxCPM; print('torch', torch.__version__); print('cuda', torch.cuda.is_available()); print('device', torch.cuda.get_device_name(0) if torch.cuda.is_available() else None); print('voxcpm import ok')"
& $python apps/worker-py/scripts/check_env.py

if (-not $SkipModelDownload) {
  Write-Host "Downloading VoxCPM2 into $ModelDir ..."
  New-Item -ItemType Directory -Force -Path (Split-Path $ModelDir) | Out-Null
  & $python apps/worker-py/scripts/download_voxcpm2.py --local-dir $ModelDir
}

Write-Host ""
Write-Host "Project runtime ready."
Write-Host "Python: $python"
Write-Host "Model:  $ModelDir"
Write-Host "Smoke:  $python apps/worker-py/scripts/smoke_voxcpm2.py --device cuda --model-id $ModelDir"