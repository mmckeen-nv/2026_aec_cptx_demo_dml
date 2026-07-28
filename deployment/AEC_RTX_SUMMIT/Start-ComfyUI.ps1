#requires -Version 5.1
[CmdletBinding()]
param(
  [switch]$Foreground,
  [string]$ComfyRoot = (Join-Path $env:USERPROFILE 'ComfyUI')
)

$ErrorActionPreference = 'Stop'
$python = Join-Path $ComfyRoot '.venv\Scripts\python.exe'
$main = Join-Path $ComfyRoot 'main.py'
$logDir = Join-Path $ComfyRoot 'logs'
$stdoutLog = Join-Path $logDir 'comfyui.stdout.log'
$stderrLog = Join-Path $logDir 'comfyui.stderr.log'

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
  throw "ComfyUI Python was not found: $python"
}
if (-not (Test-Path -LiteralPath $main -PathType Leaf)) {
  throw "ComfyUI entry point was not found: $main"
}

try {
  $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8188/system_stats' -TimeoutSec 3
  if ($response.StatusCode -eq 200) {
    Write-Host 'COMFYUI_READY existing=true url=http://127.0.0.1:8188'
    return
  }
} catch {
  # Launch below.
}

$arguments = @(
  $main,
  '--listen', '127.0.0.1',
  '--port', '8188',
  '--highvram',
  '--disable-async-offload',
  '--disable-pinned-memory',
  '--disable-cuda-malloc'
)
if ($Foreground) {
  Set-Location $ComfyRoot
  & $python @arguments
  exit $LASTEXITCODE
}

New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$process = Start-Process -FilePath $python -ArgumentList $arguments `
  -WorkingDirectory $ComfyRoot -WindowStyle Hidden -PassThru `
  -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog

$deadline = (Get-Date).AddMinutes(3)
do {
  Start-Sleep -Seconds 2
  if ($process.HasExited) {
    throw "ComfyUI exited with code $($process.ExitCode). See $stderrLog"
  }
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:8188/system_stats' -TimeoutSec 3
    if ($response.StatusCode -eq 200) {
      Write-Host "COMFYUI_READY pid=$($process.Id) url=http://127.0.0.1:8188"
      return
    }
  } catch {
    # Models and nodes may still be initializing.
  }
} while ((Get-Date) -lt $deadline)

throw "Timed out waiting for ComfyUI. See $stderrLog"
