#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [switch]$Yes,
  [switch]$SkipDependencies,
  [switch]$SkipPreflight,
  [string]$HermesHome = (Join-Path $env:LOCALAPPDATA 'hermes')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$PackageRoot = $PSScriptRoot
$RepoRoot = Join-Path $PackageRoot 'payload\aec-demo'
$DmlPayload = Join-Path $PackageRoot 'payload\daystrom-dml-source'
$DmlRoot = Join-Path $HermesHome 'integrations\daystrom-dml'
$DmlSource = Join-Path $DmlRoot 'source'
$DmlVenv = Join-Path $DmlRoot '.venv-dml'
$LogRoot = Join-Path $env:ProgramData 'AEC_RTX_SUMMIT\logs'

function Write-Step([string]$Message) {
  Write-Host ''
  Write-Host "==> $Message" -ForegroundColor Cyan
}

function Confirm-Action([string]$Message) {
  if ($Yes) { return $true }
  return (Read-Host "$Message [y/N]").Trim().ToLowerInvariant() -in @('y', 'yes')
}

function Invoke-Checked {
  param([string]$FilePath, [string[]]$ArgumentList)
  & $FilePath @ArgumentList
  if ($LASTEXITCODE -ne 0) { throw "$FilePath exited with code $LASTEXITCODE" }
}

function Resolve-Command {
  param([string]$Name, [string[]]$Candidates = @())
  $command = Get-Command $Name -ErrorAction SilentlyContinue
  if ($command) { return $command.Source }
  foreach ($candidate in $Candidates) {
    if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
  }
  return $null
}

function Install-WingetPackage {
  param([string]$Id, [string]$Label)
  if ($SkipDependencies) { throw "$Label is missing. Rerun without -SkipDependencies or install it manually." }
  $winget = Resolve-Command 'winget.exe'
  if (-not $winget) { throw "$Label is missing and winget.exe is unavailable." }
  if (-not (Confirm-Action "Install $Label with winget?")) { throw "$Label is required." }
  Invoke-Checked $winget @(
    'install', '--id', $Id, '-e',
    '--accept-package-agreements', '--accept-source-agreements'
  )
}

function Test-Http([string]$Uri) {
  try {
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 3
    return $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
  } catch {
    return $false
  }
}

function Ensure-Hermes {
  $hermes = Join-Path $HermesHome 'hermes-agent\venv\Scripts\hermes.exe'
  if (Test-Path -LiteralPath $hermes -PathType Leaf) { return $hermes }
  if ($SkipDependencies) { throw "Hermes is missing at $hermes." }
  if (-not (Confirm-Action 'Install Hermes Agent using the official Nous Research Windows installer?')) {
    throw 'Hermes Agent is required.'
  }
  $installerUri = 'https://hermes-agent.nousresearch.com/install.ps1'
  $temporary = Join-Path ([IO.Path]::GetTempPath()) "hermes-install-$([guid]::NewGuid().ToString('N')).ps1"
  try {
    Invoke-WebRequest -UseBasicParsing -Uri $installerUri -OutFile $temporary
    Invoke-Checked 'powershell.exe' @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $temporary)
  } finally {
    Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
  }
  if (-not (Test-Path -LiteralPath $hermes -PathType Leaf)) {
    throw 'The official Hermes installer completed without producing the expected executable.'
  }
  return $hermes
}

function Ensure-Ollama {
  $ollama = Resolve-Command 'ollama.exe' @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'),
    (Join-Path $env:ProgramFiles 'Ollama\ollama.exe')
  )
  if (-not $ollama) {
    Install-WingetPackage 'Ollama.Ollama' 'Ollama'
    $ollama = Resolve-Command 'ollama.exe' @(
      (Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'),
      (Join-Path $env:ProgramFiles 'Ollama\ollama.exe')
    )
  }
  if (-not $ollama) { throw 'Ollama was not found after installation.' }
  if (-not (Test-Http 'http://127.0.0.1:11434/api/version')) {
    Start-Process -FilePath $ollama -ArgumentList @('serve') -WindowStyle Hidden | Out-Null
    $deadline = (Get-Date).AddSeconds(30)
    do {
      Start-Sleep -Milliseconds 500
      $ready = Test-Http 'http://127.0.0.1:11434/api/version'
    } until ($ready -or (Get-Date) -gt $deadline)
    if (-not $ready) { throw 'Ollama did not become ready on http://127.0.0.1:11434.' }
  }
  $models = (& $ollama list | Out-String).ToLowerInvariant()
  if ($models -notmatch 'qwen3-embedding:0\.6b') {
    Write-Step 'Pull the compact DML embedding model'
    Invoke-Checked $ollama @('pull', 'qwen3-embedding:0.6b')
  } else {
    Write-Host 'Current: qwen3-embedding:0.6b'
  }
}

function Install-DaystromRuntime {
  $uv = Resolve-Command 'uv.exe' @(
    (Join-Path $env:USERPROFILE '.local\bin\uv.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\uv\uv.exe')
  )
  if (-not $uv) {
    Install-WingetPackage 'astral-sh.uv' 'uv'
    $uv = Resolve-Command 'uv.exe' @(
      (Join-Path $env:USERPROFILE '.local\bin\uv.exe'),
      (Join-Path $env:LOCALAPPDATA 'Programs\uv\uv.exe')
    )
  }
  if (-not $uv) { throw 'uv was not found after installation.' }
  if (-not (Test-Path -LiteralPath (Join-Path $DmlPayload 'pyproject.toml') -PathType Leaf)) {
    throw "Bundled Daystrom source is incomplete: $DmlPayload"
  }
  if (-not (Test-Path -LiteralPath (Join-Path $DmlSource 'pyproject.toml') -PathType Leaf)) {
    if ($PSCmdlet.ShouldProcess($DmlSource, 'Install bundled Daystrom source')) {
      New-Item -ItemType Directory -Path $DmlRoot -Force | Out-Null
      Copy-Item -LiteralPath $DmlPayload -Destination $DmlSource -Recurse
    }
  } else {
    Write-Host "Preserving existing Daystrom source: $DmlSource"
  }
  $dmlPython = Join-Path $DmlVenv 'Scripts\python.exe'
  if (-not (Test-Path -LiteralPath $dmlPython -PathType Leaf)) {
    Write-Step 'Create the isolated Daystrom Python runtime'
    Invoke-Checked $uv @('venv', $DmlVenv, '--python', '3.11')
  }
  Write-Step 'Install Daystrom DML/CMA dependencies'
  Invoke-Checked $uv @('pip', 'install', '--python', $dmlPython, '--editable', "${DmlSource}[mcp]")
  Invoke-Checked $dmlPython @('-c', 'import daystrom_dml, dml_mcp, cma, mcp; print("Daystrom runtime imports: PASS")')

  $configDir = Join-Path $DmlRoot 'config'
  $binDir = Join-Path $DmlRoot 'bin'
  New-Item -ItemType Directory -Path $configDir, $binDir -Force | Out-Null
  Copy-Item -LiteralPath (Join-Path $PackageRoot 'aec-cptx-portable.yaml') `
    -Destination (Join-Path $configDir 'aec-cptx-portable.yaml') -Force
  Copy-Item -LiteralPath (Join-Path $PackageRoot 'hermes-dml-memory.cmd') `
    -Destination (Join-Path $binDir 'hermes-dml-memory.cmd') -Force
}

if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot 'Install-AEC-Demo.ps1') -PathType Leaf)) {
  throw "AEC Summit payload is incomplete: $RepoRoot"
}

New-Item -ItemType Directory -Path $LogRoot -Force | Out-Null
$logPath = Join-Path $LogRoot ("install-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
Start-Transcript -Path $logPath -Force | Out-Null
try {
  Write-Host 'AEC RTX Summit lightweight deployment' -ForegroundColor Green
  Write-Host 'Inference: NVIDIA-hosted Claude Opus 4.5 Chat Completions API (200K context)'
  Write-Host 'Vision:    NVIDIA-hosted Nemotron 3 Nano Omni (262K context)'
  Write-Host 'Memory:    Daystrom DML + qwen3-embedding:0.6b'
  Write-Host 'Excluded:  vLLM, Qwen chat/vision containers, Hugging Face caches, model archives'

  if (-not (Resolve-Command 'git.exe')) { Install-WingetPackage 'Git.Git' 'Git' }
  if (-not (Resolve-Command 'python.exe') -and -not (Resolve-Command 'py.exe')) {
    Install-WingetPackage 'Python.Python.3.12' 'Python 3.12'
  }
  Ensure-Hermes | Out-Null
  Ensure-Ollama
  Install-DaystromRuntime

  Write-Step 'Configure the AEC Summit Hermes profile and Mission Control'
  $arguments = @(
    '-NoProfile', '-ExecutionPolicy', 'Bypass',
    '-File', (Join-Path $RepoRoot 'Install-AEC-Demo.ps1'),
    '-Tier', 'summit',
    '-DmlSourceDirectory', $DmlSource
  )
  if ($Yes) { $arguments += '-Yes' }
  if ($SkipPreflight) { $arguments += '-SkipPreflight' }
  Invoke-Checked 'powershell.exe' $arguments

  Write-Host ''
  Write-Host 'AEC RTX Summit deployment is ready.' -ForegroundColor Green
  Write-Host 'No heavyweight inference model was downloaded or copied.'
  Write-Host "Installer log: $logPath"
  exit 0
} catch {
  Write-Host ''
  Write-Host ("ERROR: " + $_.Exception.Message) -ForegroundColor Red
  Write-Host "Installer log: $logPath" -ForegroundColor Yellow
  exit 1
} finally {
  try { Stop-Transcript | Out-Null } catch { }
}
