[CmdletBinding()]
param(
  [switch]$BuildOnly,
  [switch]$SmokeTest
)

$ErrorActionPreference = 'Stop'

function Resolve-AecDemoRoot {
  if ($env:AEC_DEMO_ROOT -and (Test-Path -LiteralPath $env:AEC_DEMO_ROOT -PathType Container)) {
    return (Resolve-Path -LiteralPath $env:AEC_DEMO_ROOT).Path
  }

  $configured = [Environment]::GetEnvironmentVariable('AEC_DEMO_ROOT', 'User')
  if ($configured -and (Test-Path -LiteralPath $configured -PathType Container)) {
    return (Resolve-Path -LiteralPath $configured).Path
  }

  throw 'AEC_DEMO_ROOT is not configured. Rerun the AEC RTX Summit installer.'
}

function Set-HermesDesktopProfile {
  param([Parameter(Mandatory)][string]$Profile)

  $desktopState = Join-Path $env:APPDATA 'Hermes'
  New-Item -ItemType Directory -Path $desktopState -Force | Out-Null
  $profilePath = Join-Path $desktopState 'active-profile.json'
  $json = @{ profile = $Profile } | ConvertTo-Json
  [IO.File]::WriteAllText($profilePath, $json, [Text.UTF8Encoding]::new($false))
  return $profilePath
}

$repoRoot = Resolve-AecDemoRoot
$hermesHome = Join-Path $env:LOCALAPPDATA 'hermes'
$hermesExe = Join-Path $hermesHome 'hermes-agent\venv\Scripts\hermes.exe'
$profileRoot = Join-Path $hermesHome 'profiles\aec-cptx'

if (-not (Test-Path -LiteralPath $hermesExe -PathType Leaf)) {
  throw "Hermes is not installed at $hermesExe."
}
if (-not (Test-Path -LiteralPath $profileRoot -PathType Container)) {
  throw "The Hermes profile 'aec-cptx' is missing. Rerun the AEC demo installer."
}
if (-not (Test-Path -LiteralPath (Join-Path $repoRoot 'deployment\aec-cptx-profile\config.example.yaml') -PathType Leaf)) {
  throw "The AEC demo payload is incomplete at $repoRoot."
}

$profileState = Set-HermesDesktopProfile -Profile 'aec-cptx'
$env:HERMES_HOME = $hermesHome
$env:HERMES_PROFILE = 'aec-cptx'
$env:AEC_DEMO_ID = 'cliff-house-01'
$env:AEC_DEMO_ROOT = $repoRoot

if ($SmokeTest) {
  Write-Host "HERMES_DESKTOP_LAUNCHER_SMOKE_PASS root=$repoRoot profile=aec-cptx state=$profileState"
  exit 0
}

$arguments = @('desktop', '--cwd', $repoRoot)
if ($BuildOnly) {
  $arguments += '--build-only'
  Write-Host 'Building the Hermes Windows frontend. This is a one-time installation step...'
} else {
  Write-Host 'Opening Hermes for the AEC Cliff House profile...'
  Write-Host 'Quick demo:    Run the Cliff House quick demo'
  Write-Host 'Automatic run: Run the Cliff House build automatically'
  Write-Host 'Manual run:    Build the Cliff House manually'
}

& $hermesExe @arguments
exit $LASTEXITCODE
