$ErrorActionPreference = 'Stop'
$env:HERMES_HOME = Join-Path $env:LOCALAPPDATA 'hermes'
$env:HERMES_PROFILE = 'rtx_pro'
$dmlSource = Join-Path $env:HERMES_HOME 'integrations\daystrom-dml\source'
if (Test-Path (Join-Path $dmlSource 'pyproject.toml')) { $env:DML_SOURCE_DIR = $dmlSource }
$hermesScripts = Join-Path $env:HERMES_HOME 'hermes-agent\venv\Scripts'
$env:Path = $hermesScripts + ';' + (Join-Path $env:HERMES_HOME 'bin') + ';' + $env:Path

function Resolve-AecDemoRoot {
  $candidates = @($env:AEC_DEMO_ROOT, [Environment]::GetEnvironmentVariable('AEC_DEMO_ROOT', 'User'), [Environment]::GetEnvironmentVariable('AEC_DEMO_ROOT', 'Machine'), (Join-Path $PSScriptRoot '..\..'), (Join-Path $HOME '2026_aec_cptx_demo_dml'), 'G:\AEC-CPTX')
  foreach ($candidate in $candidates) {
    if (-not $candidate) { continue }
    try { $resolved = (Resolve-Path -LiteralPath $candidate -ErrorAction Stop).Path } catch { continue }
    if (Test-Path -LiteralPath (Join-Path $resolved 'demos\virtual_production_studio') -PathType Container) { return $resolved }
  }
  throw 'AEC demo root not found. Set the user environment variable AEC_DEMO_ROOT to the installed project directory.'
}

$projectRoot = Resolve-AecDemoRoot
$env:AEC_DEMO_ROOT = $projectRoot

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

$studioRoot = Join-Path $projectRoot 'demos\virtual_production_studio'
if (-not (Test-Path -LiteralPath $studioRoot -PathType Container)) { throw "Virtual production project not found at $studioRoot" }
$env:AEC_DEMO_ID = 'vp-studio-01'
$env:AEC_DEMO_RUN_ID = 'vp-studio-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
$rhinoTemplate = Join-Path $studioRoot 'source\vp_studio_01_template.3dm'
if (-not (Test-Path -LiteralPath $rhinoTemplate -PathType Leaf)) { throw "VP Studio Rhino template not found at $rhinoTemplate" }

$preflight = Join-Path $PSScriptRoot 'Test-RTX-Pro-Preflight.ps1'
if (-not (Test-Path -LiteralPath $preflight)) {
  $preflight = Join-Path $projectRoot 'deployment\rtx-pro-profile\Test-RTX-Pro-Preflight.ps1'
}
if (-not (Test-Path -LiteralPath $preflight)) { throw "RTX Pro preflight not found at $preflight" }
& $preflight -StartServices -RhinoTemplatePath $rhinoTemplate
if ($LASTEXITCODE -ne 0) { throw "RTX Pro preflight failed (exit code $LASTEXITCODE)." }

Set-Location $studioRoot

Write-Host ''
Write-Host '============================================================'
Write-Host ' RTX Pro - Virtual Production Studio Hermes'
Write-Host ' Profile: rtx_pro'
Write-Host ' Chat: nvidia/Qwen3.6-35B-A3B-NVFP4 (:8000)'
Write-Host ' Vision: Nemotron-3-Nano-Omni-30B-A3B (:8001)'
Write-Host ' Project: VP Studio 01 (Rhino -> Blender -> ComfyUI)'
Write-Host ' DML: active-read + synchronized project learning'
Write-Host ' Workflow: original Cliff House agent-led phase rhythm'
Write-Host ' Enhancement: SDXL depth -> FLUX.2 Klein reference refinement'
Write-Host '============================================================'
Write-Host ''

$hermesExe = Join-Path $hermesScripts 'hermes.exe'
if (-not (Test-Path $hermesExe)) { throw "Hermes not found at $hermesExe" }
& $hermesExe -p rtx_pro chat
$code = $LASTEXITCODE
Write-Host ''
Write-Host "Hermes exited with code $code. Press Enter to close."
Read-Host | Out-Null
exit $code
