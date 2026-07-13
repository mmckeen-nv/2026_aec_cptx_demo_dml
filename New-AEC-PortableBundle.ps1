#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [Parameter(Mandatory = $true)]
  [string]$Destination,
  [string]$Distro = 'Ubuntu',
  [switch]$IncludeVllmRuntime,
  [switch]$IncludeOllamaModels,
  [switch]$SkipChecksums
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot

function Invoke-Checked {
  param([string]$FilePath, [string[]]$ArgumentList)
  & $FilePath @ArgumentList
  if ($LASTEXITCODE -ne 0) { throw "$FilePath exited with code $LASTEXITCODE" }
}

function Get-WslPathInfo {
  param([string]$WindowsPath, [string]$RequestedDistro)
  $trimmed = $WindowsPath.TrimStart([char]92)
  $parts = @($trimmed -split '\\')
  if ($parts.Count -ge 3 -and $parts[0] -in @('wsl.localhost', 'wsl$')) {
    return [pscustomobject]@{
      Distro = $parts[1]
      Path = '/' + (($parts | Select-Object -Skip 2) -join '/')
    }
  }
  $converted = (& wsl.exe -d $RequestedDistro -e wslpath -a $WindowsPath | Select-Object -Last 1).Trim()
  if ($LASTEXITCODE -ne 0 -or -not $converted) { throw "Cannot map path into WSL: $WindowsPath" }
  return [pscustomobject]@{ Distro = $RequestedDistro; Path = $converted }
}

function Get-TrackedFiles {
  param([string]$Repository)
  $trimmed = $Repository.TrimStart([char]92)
  $parts = @($trimmed -split '\\')
  if ($parts.Count -ge 3 -and $parts[0] -in @('wsl.localhost', 'wsl$')) {
    $info = Get-WslPathInfo $Repository $Distro
    $files = @(& wsl.exe -d $info.Distro -e git -C $info.Path ls-files)
  } else {
    $files = @(& git.exe -C $Repository ls-files)
  }
  if ($LASTEXITCODE -ne 0 -or -not $files) { throw 'Unable to enumerate tracked repository files.' }
  return $files
}

function Get-SourceCommit {
  param([string]$Repository)
  $trimmed = $Repository.TrimStart([char]92)
  $parts = @($trimmed -split '\\')
  if ($parts.Count -ge 3 -and $parts[0] -in @('wsl.localhost', 'wsl$')) {
    $info = Get-WslPathInfo $Repository $Distro
    $commit = (& wsl.exe -d $info.Distro -e git -C $info.Path rev-parse HEAD | Select-Object -Last 1).Trim()
  } else {
    $commit = (& git.exe -C $Repository rev-parse HEAD | Select-Object -Last 1).Trim()
  }
  if ($LASTEXITCODE -ne 0 -or -not $commit) { throw 'Unable to resolve source commit.' }
  return $commit
}

function Assert-ModelEndpoint {
  param([int]$Port, [string]$ExpectedModel)
  try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/v1/models" -TimeoutSec 10
    $ids = @($response.data | ForEach-Object { $_.id })
    if ($ExpectedModel -notin $ids) {
      throw "Expected model '$ExpectedModel' was not returned by port $Port."
    }
  } catch {
    throw "Model endpoint validation failed on port $Port. Start and verify both models before exporting an offline runtime. $($_.Exception.Message)"
  }
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  throw 'New-AEC-PortableBundle.ps1 must run on Windows.'
}
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue) -and $IncludeVllmRuntime) {
  throw 'WSL is required to export the vLLM runtime.'
}

$Destination = [IO.Path]::GetFullPath($Destination)
if ($Destination.TrimEnd('\') -eq $RepoRoot.TrimEnd('\')) {
  throw 'Destination must be different from the source repository.'
}

$driveRoot = [IO.Path]::GetPathRoot($Destination)
if ($IncludeVllmRuntime -and $driveRoot -match '^[A-Za-z]:\\$') {
  $drive = [IO.DriveInfo]::new($driveRoot)
  if ($drive.DriveFormat -eq 'FAT32') {
    throw 'FAT32 cannot hold the multi-gigabyte model archives. Use NTFS or exFAT.'
  }
  if ($drive.AvailableFreeSpace -lt 64GB) {
    Write-Warning 'Less than 64 GiB is free. The current vLLM image and two model caches require about 53 GiB before repository assets.'
  }
}

Write-Host 'AEC CPTX portable bundle builder' -ForegroundColor Green
Write-Host "Source:      $RepoRoot"
Write-Host "Destination: $Destination"

if ($PSCmdlet.ShouldProcess($Destination, 'Copy tracked portable repository files')) {
  New-Item -ItemType Directory -Path $Destination -Force | Out-Null
  foreach ($relative in Get-TrackedFiles $RepoRoot) {
    $source = Join-Path $RepoRoot $relative
    $target = Join-Path $Destination $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $target) -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $target -Force
  }
}

$assets = @()
if ($IncludeVllmRuntime) {
  Assert-ModelEndpoint 8000 'nvidia/Qwen3.6-35B-A3B-NVFP4'
  Assert-ModelEndpoint 8001 'nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4'
  $bundleWsl = Get-WslPathInfo $Destination $Distro
  $dockerDir = Join-Path $Destination 'offline\docker'
  if ($PSCmdlet.ShouldProcess($dockerDir, 'Create portable runtime directory')) {
    New-Item -ItemType Directory -Path $dockerDir -Force | Out-Null
  }
  $dockerArchive = Join-Path $dockerDir 'vllm-openai.tar'
  $hfArchive = Join-Path $Destination 'offline\huggingface-cache.tar'

  Invoke-Checked 'wsl.exe' @('-d', $bundleWsl.Distro, '-e', 'docker', 'image', 'inspect', '--format', '{{.Id}}', 'vllm/vllm-openai:latest')
  foreach ($cachePath in @(
      '/root/.cache/huggingface/hub/models--nvidia--Qwen3.6-35B-A3B-NVFP4/snapshots',
      '/root/.cache/huggingface/hub/models--nvidia--Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4/snapshots')) {
    Invoke-Checked 'wsl.exe' @('-d', $bundleWsl.Distro, '-u', 'root', '-e', 'test', '-d', $cachePath)
  }

  if ($PSCmdlet.ShouldProcess($dockerArchive, 'Export vLLM Docker image')) {
    Invoke-Checked 'wsl.exe' @('-d', $bundleWsl.Distro, '-e', 'docker', 'save', '-o', "$($bundleWsl.Path)/offline/docker/vllm-openai.tar", 'vllm/vllm-openai:latest')
  }
  if ($PSCmdlet.ShouldProcess($hfArchive, 'Archive Hugging Face model cache')) {
    Invoke-Checked 'wsl.exe' @('-d', $bundleWsl.Distro, '-u', 'root', '-e', 'tar', '-cf', "$($bundleWsl.Path)/offline/huggingface-cache.tar", '-C', '/root/.cache/huggingface', '.')
  }
  $assets += $dockerArchive, $hfArchive
}

if ($IncludeOllamaModels) {
  $ollamaSource = Join-Path $env:USERPROFILE '.ollama\models'
  $ollamaDestination = Join-Path $Destination 'offline\ollama\models'
  if (-not (Test-Path -LiteralPath $ollamaSource)) { throw "Ollama model store not found: $ollamaSource" }
  if ($PSCmdlet.ShouldProcess($ollamaDestination, 'Copy Ollama model store')) {
    New-Item -ItemType Directory -Path $ollamaDestination -Force | Out-Null
    Get-ChildItem -LiteralPath $ollamaSource -Force | Copy-Item -Destination $ollamaDestination -Recurse -Force
  }
}

$commit = Get-SourceCommit $RepoRoot
$assetInfo = @()
foreach ($asset in $assets) {
  if (-not (Test-Path -LiteralPath $asset)) { continue }
  $item = Get-Item -LiteralPath $asset
  $hash = $null
  if (-not $SkipChecksums) { $hash = (Get-FileHash -LiteralPath $asset -Algorithm SHA256).Hash }
  $assetInfo += [ordered]@{
    path = $asset.Substring($Destination.Length).TrimStart('\') -replace '\\', '/'
    bytes = $item.Length
    sha256 = $hash
  }
}

$manifest = [ordered]@{
  schema_version = 1
  created_utc = (Get-Date).ToUniversalTime().ToString('o')
  source_commit = $commit
  includes_vllm_runtime = [bool]$IncludeVllmRuntime
  includes_ollama_models = [bool]$IncludeOllamaModels
  assets = $assetInfo
  notes = 'Windows, WSL2, the NVIDIA host driver, and private Daystrom source are not bundled.'
}
$manifestPath = Join-Path $Destination 'portable-bundle.json'
if ($PSCmdlet.ShouldProcess($manifestPath, 'Write portable bundle manifest')) {
  $manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
}

Write-Host ''
Write-Host 'Portable bundle complete.' -ForegroundColor Green
Write-Host "Run Install-AEC-Demo.cmd from $Destination on the target Windows machine."
if ($IncludeVllmRuntime) {
  Write-Host 'For a disconnected install, pass: -OfflineOnly -StartVllm'
}
