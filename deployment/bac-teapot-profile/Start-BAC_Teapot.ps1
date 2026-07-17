$ErrorActionPreference = 'Stop'
$env:HERMES_HOME = Join-Path $env:LOCALAPPDATA 'hermes'
$env:HERMES_PROFILE = 'bac_teapot'
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
    if (Test-Path -LiteralPath (Join-Path $resolved 'demos\teapot') -PathType Container) {
      return $resolved
    }
  }
  throw 'AEC demo root not found. Set the user environment variable AEC_DEMO_ROOT to the installed project directory.'
}

$projectRoot = Resolve-AecDemoRoot
$env:AEC_DEMO_ROOT = $projectRoot
$env:AEC_DEMO_ID = 'teapot-01'
$env:AEC_DEMO_RUN_ID = 'teapot-' + (Get-Date -Format 'yyyyMMdd-HHmmss')

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

$demoRoot = Join-Path $projectRoot 'demos\teapot'
$bacHeroMaster = Join-Path $demoRoot 'hero\BAC_TEAPOT_HERO.blend'
if (-not (Test-Path -LiteralPath $bacHeroMaster -PathType Leaf)) {
  throw "BAC HERO master is missing: $bacHeroMaster. Restore the installation payload or run git lfs pull."
}
$bacHeroBytes = (Get-Item -LiteralPath $bacHeroMaster).Length
if ($bacHeroBytes -ne 1548410063) {
  throw "BAC HERO master is incomplete (actual=$bacHeroBytes expected=1548410063): $bacHeroMaster. Run git lfs pull before launching."
}
foreach ($relative in @('work', 'renders', 'blender_assets')) {
  New-Item -ItemType Directory -Force -Path (Join-Path $demoRoot $relative) | Out-Null
}
$preflight = Join-Path $env:HERMES_HOME 'bin\Test-RTX-Pro-Preflight.ps1'
if (-not (Test-Path $preflight)) { $preflight = Join-Path $projectRoot 'deployment\rtx-pro-profile\Test-RTX-Pro-Preflight.ps1' }
& $preflight -StartServices -SkipRhino -ProfileName 'bac_teapot' -ProjectId 'teapot-01' `
  -DmlStoreName 'teapot-01-runtime-store' -CmaStoreName 'cma-teapot-01' `
  -DmlLauncherName 'dml_mcp_server_teapot.cmd' -CmaLauncherName 'cma_mcp_server_teapot.cmd' `
  -DisplayName 'BAC Teapot'
if ($LASTEXITCODE -ne 0) { throw "BAC Teapot preflight failed (exit code $LASTEXITCODE)." }
Set-Location $demoRoot
Write-Host ''
Write-Host '============================================================'
Write-Host ' BAC_Teapot - Blender Interactive Demo'
Write-Host ' Profile: bac_teapot'
Write-Host ' Model: nvidia/Qwen3.6-35B-A3B-NVFP4 (local vLLM, Docker/WSL2)'
Write-Host ' Vision: Nemotron-3-Nano-Omni-30B-A3B (local vLLM, Docker/WSL2)'
Write-Host ' Endpoint: http://localhost:8000/v1 (chat), :8001 (vision)'
Write-Host ' Flow: official 1987 Utah data -> Blender canonical build -> material interaction'
Write-Host ' Optional enhancement: SDXL depth -> FLUX.2 Klein on explicit request'
Write-Host ' HERO house: demos/teapot/hero/BAC_TEAPOT_HERO.blend'
Write-Host ' Target: first material interaction in under five minutes'
Write-Host ' Start gate: waiting for you to say "let''s build a Utah teapot"'
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
