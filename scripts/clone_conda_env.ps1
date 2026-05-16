param(
  [string]$SourceEnv = "base",
  [string]$TargetPrefix = ".conda-env"
)

$ErrorActionPreference = "Stop"

if (Test-Path $TargetPrefix) {
  Write-Host "Project conda environment already exists at $TargetPrefix"
  Write-Host "Remove it manually if you want to recreate it."
  exit 0
}

Write-Host "Cloning conda environment '$SourceEnv' to '$TargetPrefix'..."
conda create --prefix $TargetPrefix --clone $SourceEnv -y

Write-Host "Project environment ready:"
Write-Host "$TargetPrefix\python.exe"
Write-Host "Verify with:"
Write-Host "$TargetPrefix\python.exe apps/worker-py/scripts/check_env.py"
