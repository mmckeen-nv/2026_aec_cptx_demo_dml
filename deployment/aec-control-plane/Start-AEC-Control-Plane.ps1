$ErrorActionPreference = 'Stop'

function Resolve-AecDemoRoot {
  $candidates = @(
    $env:AEC_DEMO_ROOT,
    [Environment]::GetEnvironmentVariable('AEC_DEMO_ROOT', 'User'),
    [Environment]::GetEnvironmentVariable('AEC_DEMO_ROOT', 'Machine'),
    (Join-Path $PSScriptRoot '..\..')
  )
  foreach ($candidate in $candidates) {
    if (-not $candidate) { continue }
    try { $resolved = (Resolve-Path -LiteralPath $candidate -ErrorAction Stop).Path } catch { continue }
    if (Test-Path -LiteralPath (Join-Path $resolved 'aec-mission-control\package.json') -PathType Leaf) {
      return $resolved
    }
  }
  throw 'AEC demo root not found. Set the user environment variable AEC_DEMO_ROOT to the repository directory.'
}

$projectRoot = Resolve-AecDemoRoot
$siteRoot = Join-Path $projectRoot 'aec-mission-control'
$npm = Join-Path $env:LOCALAPPDATA 'hermes\node\npm.cmd'
$url = 'http://127.0.0.1:3210'

if (-not (Test-Path -LiteralPath $siteRoot -PathType Container)) {
  throw "AEC Control Plane is missing at $siteRoot"
}
if (-not (Test-Path -LiteralPath $npm -PathType Leaf)) {
  $npmCommand = Get-Command npm.cmd -ErrorAction SilentlyContinue
  if (-not $npmCommand) { throw "Node runtime is missing at $npm and npm.cmd is not on PATH." }
  $npm = $npmCommand.Source
}
if (-not (Test-Path -LiteralPath (Join-Path $siteRoot '.next\BUILD_ID') -PathType Leaf)) {
  throw "AEC Control Plane has not been built. Rerun Install-AEC-Demo.cmd."
}

$listening = Get-NetTCPConnection -LocalPort 3210 -State Listen -ErrorAction SilentlyContinue
if (-not $listening) {
  $stdout = Join-Path $siteRoot '.control-plane.log'
  $stderr = Join-Path $siteRoot '.control-plane-error.log'
  Start-Process -FilePath $npm `
    -ArgumentList @('run', 'start', '--', '-H', '127.0.0.1', '-p', '3210') `
    -WorkingDirectory $siteRoot `
    -RedirectStandardOutput $stdout `
    -RedirectStandardError $stderr `
    -WindowStyle Hidden | Out-Null

  $deadline = (Get-Date).AddSeconds(30)
  do {
    Start-Sleep -Milliseconds 350
    $listening = Get-NetTCPConnection -LocalPort 3210 -State Listen -ErrorAction SilentlyContinue
  } until ($listening -or (Get-Date) -gt $deadline)

  if (-not $listening) {
    throw "AEC Control Plane did not start. Review $stderr"
  }
}

Start-Process $url
