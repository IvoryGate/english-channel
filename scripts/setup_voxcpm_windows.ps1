param(
  [string]$Python = "python",
  [string]$TorchIndexUrl = "https://download.pytorch.org/whl/cu128",
  [switch]$UseHfMirror
)

$ErrorActionPreference = "Stop"

if ($UseHfMirror) {
  $env:HF_ENDPOINT = "https://hf-mirror.com"
}

Write-Host "Creating Python virtual environment..."
& $Python -m venv .venv

$venvPython = ".\.venv\Scripts\python.exe"
$venvPip = ".\.venv\Scripts\pip.exe"

Write-Host "Upgrading pip..."
& $venvPython -m pip install --upgrade pip

Write-Host "Installing PyTorch CUDA wheel..."
& $venvPip install torch torchvision torchaudio --index-url $TorchIndexUrl

Write-Host "Installing VoxCPM worker dependencies..."
& $venvPip install -r apps/worker-py/requirements.txt

Write-Host "Checking environment..."
& $venvPython apps/worker-py/scripts/check_env.py

Write-Host "Setup complete. To run smoke test:"
Write-Host ".\.venv\Scripts\python.exe apps/worker-py/scripts/smoke_voxcpm2.py --device cuda"
