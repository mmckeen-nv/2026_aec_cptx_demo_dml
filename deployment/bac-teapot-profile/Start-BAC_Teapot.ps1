$ErrorActionPreference = 'Stop'
$env:HERMES_HOME = Join-Path $env:LOCALAPPDATA 'hermes'
$hermesScripts = Join-Path $env:HERMES_HOME 'hermes-agent\venv\Scripts'
$env:Path = $hermesScripts + ';' + (Join-Path $env:HERMES_HOME 'bin') + ';' + $env:Path
Set-Location $env:USERPROFILE
Write-Host ''
Write-Host '============================================================'
Write-Host ' BAC_Teapot - Hermes Profile'
Write-Host ' Profile: bac_teapot'
Write-Host ' Model: nvidia/Qwen3.6-35B-A3B-NVFP4 (local vLLM, Docker/WSL2)'
Write-Host ' Vision: Nemotron-3-Nano-Omni-30B-A3B (local vLLM, Docker/WSL2)'
Write-Host ' Endpoint: http://localhost:8000/v1 (chat), :8001 (vision)'
Write-Host '============================================================'
Write-Host ''
$hermesExe = Join-Path $hermesScripts 'hermes.exe'
if (-not (Test-Path $hermesExe)) { throw "Hermes not found at $hermesExe" }
& $hermesExe -p bac_teapot chat
$code = $LASTEXITCODE
Write-Host ''
Write-Host "Hermes exited with code $code. Press Enter to close."
Read-Host | Out-Null
exit $code
