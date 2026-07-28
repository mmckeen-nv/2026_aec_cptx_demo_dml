param(
  [ValidateSet('Menu', 'Manual', 'Automatic', 'Query', 'Idle')]
  [string]$RunMode = 'Menu',
  [string]$Query,
  [string]$QueryFile
)

$ErrorActionPreference = 'Stop'
$env:HERMES_HOME = Join-Path $env:LOCALAPPDATA 'hermes'
$env:HERMES_PROFILE = 'aec-cptx'
$dmlSource = Join-Path $env:HERMES_HOME 'integrations\daystrom-dml\source'
if (Test-Path (Join-Path $dmlSource 'pyproject.toml')) { $env:DML_SOURCE_DIR = $dmlSource }
$hermesScripts = Join-Path $env:HERMES_HOME 'hermes-agent\venv\Scripts'
$hermesNode = Join-Path $env:HERMES_HOME 'node'
$env:Path = $hermesScripts + ';' + $hermesNode + ';' + (Join-Path $env:HERMES_HOME 'bin') + ';' + $env:Path

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

if ($RunMode -eq 'Menu') {
  Clear-Host
  Write-Host 'Cliff House'
  Write-Host '==========='
  Write-Host '1 - Build the Cliff House manually'
  Write-Host '2 - Build the Cliff House without user input'
  Write-Host ''
  do {
    $menuChoice = (Read-Host 'Select 1 or 2').Trim()
  } until ($menuChoice -in @('1', '2'))
  $RunMode = if ($menuChoice -eq '2') { 'Automatic' } else { 'Manual' }
}
if ($RunMode -eq 'Query' -and $QueryFile) {
  if (-not (Test-Path -LiteralPath $QueryFile -PathType Leaf)) {
    throw "Query file not found at $QueryFile"
  }
  $Query = Get-Content -LiteralPath $QueryFile -Raw
}
if ($RunMode -eq 'Query' -and [string]::IsNullOrWhiteSpace($Query)) {
  throw 'Query mode requires a non-empty -Query value.'
}
$env:AEC_CLIFF_HOUSE_RUN_MODE = $RunMode.ToLowerInvariant()

function Test-LocalModel($port) {
  try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:$port/v1/models" -TimeoutSec 3 -UseBasicParsing
    return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300)
  } catch { return $false }
}

$profileConfig = Join-Path $env:HERMES_HOME 'profiles\aec-cptx\config.yaml'
$profileConfigText = if (Test-Path -LiteralPath $profileConfig) { Get-Content -LiteralPath $profileConfig -Raw } else { '' }
$usesLocalVllm = $profileConfigText -match '(?m)^\s+provider:\s+custom:vllm_local\s*$'

if ($usesLocalVllm -and -not (Test-LocalModel 8000)) {
  $vllmStart = if ($env:AEC_DEMO_ROOT) { Join-Path $env:AEC_DEMO_ROOT 'deployment\wsl-vllm\start_vllm.bat' } else { $null }
  if (-not $vllmStart -or -not (Test-Path $vllmStart)) { $vllmStart = Join-Path $PSScriptRoot '..\wsl-vllm\start_vllm.bat' }
  if (-not (Test-Path $vllmStart)) { throw "vLLM launcher not found at $vllmStart" }
  & $vllmStart --no-pause --single-vlm
  if ($LASTEXITCODE -ne 0) { throw "Unable to start the local model backend (exit code $LASTEXITCODE)." }
}

# DML embeddings run through Ollama in WSL. When Codex replaces vLLM there is
# no long-lived Docker client keeping the distro awake, so hold one lightweight
# WSL session open and start the enabled Ollama service before preflight.
function Test-Ollama {
  try {
    $response = Invoke-WebRequest -Uri 'http://127.0.0.1:11434/api/version' -TimeoutSec 3 -UseBasicParsing
    return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300)
  } catch { return $false }
}

if (-not (Test-Ollama)) {
  Start-Process -FilePath "$env:SystemRoot\System32\wsl.exe" `
    -ArgumentList @('-d', 'Ubuntu', '-u', 'root', '--', 'sleep', 'infinity') `
    -WindowStyle Hidden | Out-Null
  & "$env:SystemRoot\System32\wsl.exe" -d Ubuntu -u root -- systemctl start ollama
  $ollamaDeadline = (Get-Date).AddSeconds(30)
  while (-not (Test-Ollama) -and (Get-Date) -lt $ollamaDeadline) {
    Start-Sleep -Milliseconds 750
  }
  if (-not (Test-Ollama)) { throw 'Unable to start the Ollama embedding backend in WSL.' }
}

$demoRoot = Join-Path $projectRoot 'demos\cliff_house'

$geometryValidator = Join-Path $projectRoot 'scripts\validate_cliff_house_geometry_contract.py'
& (Join-Path $hermesScripts 'python.exe') $geometryValidator
if ($LASTEXITCODE -ne 0) { throw "Cliff House geometry-contract validation failed (exit code $LASTEXITCODE)." }

$preflight = Join-Path $env:HERMES_HOME 'bin\Test-RTX-Pro-Preflight.ps1'
if (-not (Test-Path $preflight)) { $preflight = Join-Path $projectRoot 'deployment\rtx-pro-profile\Test-RTX-Pro-Preflight.ps1' }
& $preflight -StartServices -SkipRhinoLaunch -SingleVlm -ProfileName 'aec-cptx' -ProjectId 'cliff-house-01' `
  -DmlStoreName 'cliff-house-01-rhino-store' -CmaStoreName 'cma-cliff-house-01' `
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
if ($RunMode -eq 'Idle') {
  Write-Host 'Preflight passed. Starting the resident Hermes coordinator in idle mode.'
  $residentWorker = Join-Path $projectRoot 'deployment\aec-control-plane\hermes_resident_worker.py'
  $residentQueue = Join-Path $projectRoot 'aec-mission-control\.control'
  & (Join-Path $hermesScripts 'python.exe') $residentWorker `
    --hermes-exe $hermesExe --profile 'aec-cptx' --repo $projectRoot `
    --queue-dir $residentQueue --start-idle
} elseif ($RunMode -eq 'Automatic') {
  $automaticPromptPath = Join-Path $projectRoot 'deployment\aec-cptx-profile\cliff-house-automatic-run.txt'
  if (-not (Test-Path -LiteralPath $automaticPromptPath -PathType Leaf)) {
    throw "Automatic-run prompt not found at $automaticPromptPath"
  }
  Write-Host 'Automatic mode selected. Hermes will run through the final stylized frame without review gates.'
  $residentWorker = Join-Path $projectRoot 'deployment\aec-control-plane\hermes_resident_worker.py'
  $residentQueue = Join-Path $projectRoot 'aec-mission-control\.control'
  & (Join-Path $hermesScripts 'python.exe') $residentWorker `
    --hermes-exe $hermesExe --profile 'aec-cptx' --repo $projectRoot `
    --queue-dir $residentQueue --initial-prompt-file $automaticPromptPath
} elseif ($RunMode -eq 'Query') {
  Write-Host 'Hermes instruction selected. The submitted task will run with the full AEC profile.'
  $residentWorker = Join-Path $projectRoot 'deployment\aec-control-plane\hermes_resident_worker.py'
  $residentQueue = Join-Path $projectRoot 'aec-mission-control\.control'
  $residentInitialPrompt = Join-Path $residentQueue ('resident-initial-' + $env:AEC_DEMO_RUN_ID + '.txt')
  New-Item -ItemType Directory -Path $residentQueue -Force | Out-Null
  Set-Content -LiteralPath $residentInitialPrompt -Value $Query -Encoding UTF8
  & (Join-Path $hermesScripts 'python.exe') $residentWorker `
    --hermes-exe $hermesExe --profile 'aec-cptx' --repo $projectRoot `
    --queue-dir $residentQueue --initial-prompt-file $residentInitialPrompt
} else {
  Write-Host 'Manual mode selected. Hermes will use object-by-object phases and operator review gates.'
  & $hermesExe -p aec-cptx chat
}
$code = $LASTEXITCODE
if ($RunMode -eq 'Manual') {
  Write-Host "Hermes exited with code $code. Press Enter to close."
  Read-Host | Out-Null
} else {
  Write-Host "Hermes exited with code $code."
}
exit $code
