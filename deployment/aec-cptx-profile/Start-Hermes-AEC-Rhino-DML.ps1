$ErrorActionPreference = 'Stop'
$env:HERMES_HOME = Join-Path $env:LOCALAPPDATA 'hermes'
$env:HERMES_PROFILE = 'aec-cptx'
$dmlSource = Join-Path $env:HERMES_HOME 'integrations\daystrom-dml\source'
if (Test-Path (Join-Path $dmlSource 'pyproject.toml')) { $env:DML_SOURCE_DIR = $dmlSource }
$hermesScripts = Join-Path $env:HERMES_HOME 'hermes-agent\venv\Scripts'
$env:Path = $hermesScripts + ';' + (Join-Path $env:HERMES_HOME 'bin') + ';' + $env:Path

function Resolve-AecDemoRoot {
  $candidates = @(
    $env:AEC_DEMO_ROOT,
    [Environment]::GetEnvironmentVariable('AEC_DEMO_ROOT', 'User'),
    [Environment]::GetEnvironmentVariable('AEC_DEMO_ROOT', 'Machine'),
    (Join-Path $PSScriptRoot '..\..'),
    (Join-Path $HOME '2026_aec_cptx_demo_dml'),
    'G:\AEC-CPTX'
  )

  foreach ($candidate in $candidates) {
    if (-not $candidate) { continue }
    try { $resolved = (Resolve-Path -LiteralPath $candidate -ErrorAction Stop).Path } catch { continue }
    if (Test-Path -LiteralPath (Join-Path $resolved 'demos\cliff_house') -PathType Container) {
      return $resolved
    }
  }

  throw 'AEC demo root not found. Set the user environment variable AEC_DEMO_ROOT to the installed project directory.'
}

$projectRoot = Resolve-AecDemoRoot
$env:AEC_DEMO_ROOT = $projectRoot
$env:AEC_DEMO_ID = 'cliff-house-01'
$env:AEC_DEMO_RUN_ID = 'cliff-house-' + (Get-Date -Format 'yyyyMMdd-HHmmss')

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

$demoRoot = Join-Path $projectRoot 'demos\cliff_house'

$preflight = Join-Path $env:HERMES_HOME 'bin\Test-RTX-Pro-Preflight.ps1'
if (-not (Test-Path $preflight)) { $preflight = Join-Path $projectRoot 'deployment\rtx-pro-profile\Test-RTX-Pro-Preflight.ps1' }
& $preflight -StartServices -ProfileName 'aec-cptx' -ProjectId 'cliff-house-01' `
  -DmlStoreName 'cliff-house-01-runtime-store' -CmaStoreName 'cma-cliff-house-01' `
  -DmlLauncherName 'dml_mcp_server_cliff_house.cmd' -CmaLauncherName 'cma_mcp_server_cliff_house.cmd' `
  -DisplayName 'Cliff House'
if ($LASTEXITCODE -ne 0) { throw "Cliff House preflight failed (exit code $LASTEXITCODE)." }

# The pristine Cliff House runs from repository root. Its startup prompt,
# skills index, system prompts, project prompt, and demo rules all resolve from
# this directory; changing cwd to demos/cliff_house silently breaks that rhythm.
Set-Location $projectRoot
Write-Host 'Starting Cliff House from repository root with the pristine prompt/skill/phase rhythm plus advisory DML/CMA.'
$hermesExe = Join-Path $hermesScripts 'hermes.exe'
if (-not (Test-Path $hermesExe)) { throw "Hermes not found at $hermesExe" }
& $hermesExe -p aec-cptx chat
$code = $LASTEXITCODE
Write-Host "Hermes exited with code $code. Press Enter to close."
Read-Host | Out-Null
exit $code
