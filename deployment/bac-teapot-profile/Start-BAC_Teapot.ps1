$ErrorActionPreference = 'Stop'
$env:HERMES_HOME = Join-Path $env:LOCALAPPDATA 'hermes'
$dmlSource = Join-Path $env:HERMES_HOME 'integrations\daystrom-dml\source'
if (Test-Path (Join-Path $dmlSource 'pyproject.toml')) { $env:DML_SOURCE_DIR = $dmlSource }
$hermesScripts = Join-Path $env:HERMES_HOME 'hermes-agent\venv\Scripts'
$env:Path = $hermesScripts + ';' + (Join-Path $env:HERMES_HOME 'bin') + ';' + $env:Path

function Test-LocalModel($port) {
  try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/v1/models" -TimeoutSec 3 -UseBasicParsing
    return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300)
  } catch { return $false }
}

if (-not (Test-LocalModel 8000) -or -not (Test-LocalModel 8001)) {
  $vllmStart = $null
  if ($env:AEC_DEMO_ROOT) {
    $installedCandidate = Join-Path $env:AEC_DEMO_ROOT 'deployment\wsl-vllm\start_vllm.bat'
    if (Test-Path $installedCandidate) { $vllmStart = $installedCandidate }
  }
  if (-not $vllmStart) { $vllmStart = Join-Path $PSScriptRoot '..\wsl-vllm\start_vllm.bat' }
  if (-not (Test-Path $vllmStart)) { throw "vLLM launcher not found at $vllmStart" }
  Write-Host 'Local model backend is not ready. Starting/checking vLLM containers...'
  & $vllmStart --no-pause
  if ($LASTEXITCODE -ne 0) { throw "Unable to start the local model backend (exit code $LASTEXITCODE)." }
}

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
