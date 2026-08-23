param()

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$runtimePython = "H:\english-channel\.conda-env\python.exe"
$chapterOneTrace = Join-Path $repoRoot "workspace\classics\persuasion\chapter_001\reports\audio-render.json"

Set-Location -LiteralPath $repoRoot
$env:CLASSICS_VOXCPM_OPTIMIZE = "1"
$env:TRITON_CACHE_DIR = Join-Path $repoRoot "tmp\triton-cache"
$env:TORCHINDUCTOR_CACHE_DIR = Join-Path $repoRoot "tmp\torchinductor-cache"

while (-not (Test-Path -LiteralPath $chapterOneTrace)) {
    Start-Sleep -Seconds 15
}
Start-Sleep -Seconds 20

& $runtimePython scripts\classics.py preview-voice --book persuasion --chapter 1 --segments 004,020 --name production-repair-001 --force
if ($LASTEXITCODE -ne 0) { throw "Chapter 1 repair render failed with exit code $LASTEXITCODE" }

& $runtimePython scripts\classics.py render-audio --book persuasion --chapter 1
if ($LASTEXITCODE -ne 0) { throw "Chapter 1 recomposition failed with exit code $LASTEXITCODE" }

& $runtimePython scripts\classics.py qc-asr --book persuasion --chapter 1
& $runtimePython scripts\classics.py package --book persuasion --chapter 1 --force
if ($LASTEXITCODE -ne 0) { throw "Chapter 1 packaging failed with exit code $LASTEXITCODE" }

& $runtimePython scripts\classics.py produce --book persuasion --chapters 2-3
if ($LASTEXITCODE -ne 0) { throw "Chapters 2-3 production failed with exit code $LASTEXITCODE" }

& $runtimePython scripts\classics.py qc-asr --book persuasion --chapter 2
& $runtimePython scripts\classics.py qc-asr --book persuasion --chapter 3
