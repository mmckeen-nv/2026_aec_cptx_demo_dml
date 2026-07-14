$ErrorActionPreference = 'Stop'
$env:HERMES_HOME = Join-Path $env:LOCALAPPDATA 'hermes'
$env:HERMES_PROFILE = 'aec-cptx'
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
  $vllmStart = if ($env:AEC_DEMO_ROOT) { Join-Path $env:AEC_DEMO_ROOT 'deployment\wsl-vllm\start_vllm.bat' } else { $null }
  if (-not $vllmStart -or -not (Test-Path $vllmStart)) { $vllmStart = Join-Path $PSScriptRoot '..\wsl-vllm\start_vllm.bat' }
  if (-not (Test-Path $vllmStart)) { throw "vLLM launcher not found at $vllmStart" }
  & $vllmStart --no-pause
  if ($LASTEXITCODE -ne 0) { throw "Unable to start the local model backend (exit code $LASTEXITCODE)." }
}

$projectRoot = $env:AEC_DEMO_ROOT
if (-not $projectRoot) { $projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path }
$demoRoot = Join-Path $projectRoot 'demos\cliff_house'
if (-not (Test-Path -LiteralPath $demoRoot -PathType Container)) { throw "Cliff House project not found at $demoRoot" }

$preflight = Join-Path $env:HERMES_HOME 'bin\Test-RTX-Pro-Preflight.ps1'
if (-not (Test-Path $preflight)) { $preflight = Join-Path $projectRoot 'deployment\rtx-pro-profile\Test-RTX-Pro-Preflight.ps1' }
& $preflight -StartServices -SkipComfyUI -ProfileName 'aec-cptx' -ProjectId 'cliff-house-01' `
  -DmlStoreName 'cliff-house-01-runtime-store' -CmaStoreName 'cma-cliff-house-01' `
  -DmlLauncherName 'dml_mcp_server_cliff_house.cmd' -CmaLauncherName 'cma_mcp_server_cliff_house.cmd' `
  -DisplayName 'Cliff House'
if ($LASTEXITCODE -ne 0) { throw "Cliff House preflight failed (exit code $LASTEXITCODE)." }

Set-Location $demoRoot
Write-Host 'Starting Cliff House Hermes session with isolated DML/CMA and ready Rhino/Blender MCP bridges.'
$hermesExe = Join-Path $hermesScripts 'hermes.exe'
if (-not (Test-Path $hermesExe)) { throw "Hermes not found at $hermesExe" }
& $hermesExe -p aec-cptx chat
$code = $LASTEXITCODE
Write-Host "Hermes exited with code $code. Press Enter to close."
Read-Host | Out-Null
exit $code
