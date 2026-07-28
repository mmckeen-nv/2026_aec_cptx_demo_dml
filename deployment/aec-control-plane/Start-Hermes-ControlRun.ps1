param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('Manual', 'Automatic', 'Query', 'Idle')]
  [string]$Mode,
  [string]$QueryFile,
  [Parameter(Mandatory = $true)]
  [string]$ReceiptPath
)

$ErrorActionPreference = 'Stop'
$launcher = Join-Path $env:LOCALAPPDATA 'hermes\bin\Start-Hermes-AEC-Rhino-DML.ps1'
if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
  throw "Hermes AEC launcher is missing at $launcher"
}
if ($Mode -eq 'Query' -and (-not $QueryFile -or -not (Test-Path -LiteralPath $QueryFile -PathType Leaf))) {
  throw 'Query mode requires an existing query file.'
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$siteRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$logRoot = Join-Path $siteRoot 'aec-mission-control'
$stdout = Join-Path $logRoot "hermes-control-$stamp.log"
$stderr = Join-Path $logRoot "hermes-control-$stamp.err.log"

$argumentLine = '-NoProfile -ExecutionPolicy Bypass -File "{0}" -RunMode {1}' -f $launcher, $Mode
if ($Mode -eq 'Query') {
  $argumentLine += ' -QueryFile "{0}"' -f $QueryFile
}

$start = @{
  FilePath = 'powershell.exe'
  ArgumentList = $argumentLine
  WorkingDirectory = $siteRoot
  PassThru = $true
}
if ($Mode -ne 'Manual') {
  $start.WindowStyle = 'Hidden'
  $start.RedirectStandardOutput = $stdout
  $start.RedirectStandardError = $stderr
}

$process = Start-Process @start
$receipt = @{
  pid = $process.Id
  mode = $Mode
  started_at = (Get-Date).ToString('o')
  stdout = if ($Mode -eq 'Manual') { $null } else { $stdout }
  stderr = if ($Mode -eq 'Manual') { $null } else { $stderr }
}
$receipt | ConvertTo-Json -Compress | Set-Content -LiteralPath $ReceiptPath -Encoding UTF8
