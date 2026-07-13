#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [Parameter(Mandatory = $true)]
  [string]$Destination,
  [string]$Distro = 'Ubuntu',
  [switch]$IncludeVllmRuntime,
  [switch]$IncludeOllamaModels,
  [switch]$SkipDmlStores,
  [switch]$ReuseExistingAssets,
  [switch]$SkipChecksums,
  [string]$HermesHome = (Join-Path $env:LOCALAPPDATA 'hermes')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot

function Invoke-Checked {
  param([string]$FilePath, [string[]]$ArgumentList)
  & $FilePath @ArgumentList
  if ($LASTEXITCODE -ne 0) { throw "$FilePath exited with code $LASTEXITCODE" }
}

function Get-FileSha256 {
  param([string]$Path)
  $stream = [IO.File]::OpenRead($Path)
  try {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
      return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '')
    } finally {
      $sha.Dispose()
    }
  } finally {
    $stream.Dispose()
  }
}

function Get-WslPathInfo {
  param([string]$WindowsPath, [string]$RequestedDistro)
  $trimmed = $WindowsPath.TrimStart([char]92)
  $parts = @($trimmed -split '\\')
  if ($parts.Count -ge 3 -and $parts[0] -in @('wsl.localhost', 'wsl$')) {
    return [pscustomobject]@{
      Distro = $parts[1]
      Path = '/' + (($parts | Select-Object -Skip 2) -join '/')
      DriveLetter = $null
      MountRoot = $null
    }
  }
  if ($WindowsPath -match '^(?<drive>[A-Za-z]):(?:\\(?<tail>.*))?$') {
    $drive = $Matches.drive.ToLowerInvariant()
    $mountRoot = "/mnt/$drive"
    $tail = if ($Matches.tail) { '/' + ($Matches.tail -replace '\\', '/') } else { '' }
    return [pscustomobject]@{
      Distro = $RequestedDistro
      Path = $mountRoot + $tail
      DriveLetter = "$($Matches.drive):"
      MountRoot = $mountRoot
    }
  }
  $convertedOutput = @(& wsl.exe -d $RequestedDistro -e wslpath -a $WindowsPath)
  $converted = if ($convertedOutput) { ($convertedOutput | Select-Object -Last 1).Trim() } else { $null }
  if ($LASTEXITCODE -ne 0 -or -not $converted) { throw "Cannot map path into WSL: $WindowsPath" }
  return [pscustomobject]@{
    Distro = $RequestedDistro
    Path = $converted
    DriveLetter = $null
    MountRoot = $null
  }
}

function Ensure-WslDriveMounted {
  param($PathInfo)
  if (-not $PathInfo.DriveLetter) { return }

  & wsl.exe -d $PathInfo.Distro -e mountpoint -q $PathInfo.MountRoot
  if ($LASTEXITCODE -ne 0) {
    Invoke-Checked 'wsl.exe' @('-d', $PathInfo.Distro, '-u', 'root', '-e', 'mkdir', '-p', $PathInfo.MountRoot)
    Invoke-Checked 'wsl.exe' @('-d', $PathInfo.Distro, '-u', 'root', '-e', 'mount', '-t', 'drvfs', $PathInfo.DriveLetter, $PathInfo.MountRoot)
  }

  Invoke-Checked 'wsl.exe' @('-d', $PathInfo.Distro, '-e', 'test', '-d', $PathInfo.Path)
}

function Get-WslUncPath {
  param([string]$RequestedDistro, [string]$LinuxPath)
  return "\\wsl.localhost\$RequestedDistro\" + $LinuxPath.TrimStart('/').Replace('/', '\')
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
$bundledDaystromStores = @()
if (-not $SkipDmlStores) {
  $storeRoot = Join-Path $HermesHome 'integrations\daystrom-dml\stores'
  if (-not (Test-Path -LiteralPath $storeRoot -PathType Container)) {
    throw "Daystrom store directory not found: $storeRoot. Use -SkipDmlStores only for a memory-free bundle."
  }
  $activeDaystrom = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -match 'dml_mcp|cma\.mcp_server|hermes-dml-memory'
  })
  if ($activeDaystrom.Count -gt 0) {
    throw 'Daystrom DML/CMA is active. Close all Hermes demo sessions before creating a consistent portable memory snapshot.'
  }
  $portableStoreRoot = Join-Path $Destination 'offline\daystrom\stores'
  $storeNames = @(
    'vp-studio-01-runtime-store', 'cma-vp-studio-01',
    'teapot-01-runtime-store', 'cma-teapot-01',
    'cliff-house-01-runtime-store', 'cma-cliff-house-01',
    'aec-cptx-runtime-store', 'cma-store'
  )
  foreach ($storeName in $storeNames) {
    $sourceStore = Join-Path $storeRoot $storeName
    if (-not (Test-Path -LiteralPath $sourceStore -PathType Container)) { continue }
    $destinationStore = Join-Path $portableStoreRoot $storeName
    if ($PSCmdlet.ShouldProcess($destinationStore, 'Copy portable Daystrom DML/CMA store')) {
      New-Item -ItemType Directory -Path $destinationStore -Force | Out-Null
      Get-ChildItem -LiteralPath $sourceStore -Force | Copy-Item -Destination $destinationStore -Recurse -Force
    }
    $bundledDaystromStores += $storeName
  }
  if ($bundledDaystromStores.Count -eq 0) {
    throw "No project Daystrom stores were found under $storeRoot. Use -SkipDmlStores only for a memory-free bundle."
  }
}
if ($IncludeVllmRuntime) {
  $dockerDir = Join-Path $Destination 'offline\docker'
  if ($PSCmdlet.ShouldProcess($dockerDir, 'Create portable runtime directory')) {
    New-Item -ItemType Directory -Path $dockerDir -Force | Out-Null
  }
  $dockerArchive = Join-Path $dockerDir 'vllm-openai.tar'
  $hfArchive = Join-Path $Destination 'offline\huggingface-cache.tar'

  if ($ReuseExistingAssets) {
    foreach ($archive in @($dockerArchive, $hfArchive)) {
      if (-not (Test-Path -LiteralPath $archive -PathType Leaf) -or (Get-Item -LiteralPath $archive).Length -eq 0) {
        throw "Cannot reuse missing or empty runtime archive: $archive"
      }
    }
    Write-Host 'Reusing existing vLLM runtime archives.'
  } else {
    Assert-ModelEndpoint 8000 'nvidia/Qwen3.6-35B-A3B-NVFP4'
    Assert-ModelEndpoint 8001 'nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4'
    $bundleWsl = Get-WslPathInfo $Destination $Distro
    if (-not $WhatIfPreference) { Ensure-WslDriveMounted $bundleWsl }

    Invoke-Checked 'wsl.exe' @('-d', $bundleWsl.Distro, '-e', 'docker', 'image', 'inspect', '--format', '{{.Id}}', 'vllm/vllm-openai:latest')
    foreach ($cachePath in @(
        '/root/.cache/huggingface/hub/models--nvidia--Qwen3.6-35B-A3B-NVFP4/snapshots',
        '/root/.cache/huggingface/hub/models--nvidia--Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4/snapshots')) {
      Invoke-Checked 'wsl.exe' @('-d', $bundleWsl.Distro, '-u', 'root', '-e', 'test', '-d', $cachePath)
    }

    $stageRoot = "/tmp/aec-portable-$([guid]::NewGuid().ToString('N'))"
    $stageDocker = "$stageRoot/vllm-openai.tar"
    $stageHf = "$stageRoot/huggingface-cache.tar"
    if (-not $WhatIfPreference) {
      Invoke-Checked 'wsl.exe' @('-d', $bundleWsl.Distro, '-e', 'mkdir', '-p', $stageRoot)
    }
    try {
      if ($PSCmdlet.ShouldProcess($dockerArchive, 'Export vLLM Docker image')) {
        Invoke-Checked 'wsl.exe' @('-d', $bundleWsl.Distro, '-e', 'docker', 'save', '-o', $stageDocker, 'vllm/vllm-openai:latest')
        Invoke-Checked 'wsl.exe' @('-d', $bundleWsl.Distro, '-e', 'test', '-s', $stageDocker)
        Copy-Item -LiteralPath (Get-WslUncPath $bundleWsl.Distro $stageDocker) -Destination $dockerArchive -Force
        if (-not (Test-Path -LiteralPath $dockerArchive) -or (Get-Item -LiteralPath $dockerArchive).Length -eq 0) {
          throw "Docker archive copy failed: $dockerArchive"
        }
      }
      if ($PSCmdlet.ShouldProcess($hfArchive, 'Archive Hugging Face model cache')) {
        Invoke-Checked 'wsl.exe' @('-d', $bundleWsl.Distro, '-u', 'root', '-e', 'tar', '-cf', $stageHf, '-C', '/root/.cache/huggingface', '.')
        Invoke-Checked 'wsl.exe' @('-d', $bundleWsl.Distro, '-u', 'root', '-e', 'test', '-s', $stageHf)
        Copy-Item -LiteralPath (Get-WslUncPath $bundleWsl.Distro $stageHf) -Destination $hfArchive -Force
        if (-not (Test-Path -LiteralPath $hfArchive) -or (Get-Item -LiteralPath $hfArchive).Length -eq 0) {
          throw "Hugging Face cache archive copy failed: $hfArchive"
        }
      }
    } finally {
      if (-not $WhatIfPreference -and $stageRoot -match '^/tmp/aec-portable-[0-9a-f]{32}$') {
        Invoke-Checked 'wsl.exe' @('-d', $bundleWsl.Distro, '-u', 'root', '-e', 'rm', '-rf', $stageRoot)
      }
    }
  }
  $assets += $dockerArchive, $hfArchive
}

if ($IncludeOllamaModels) {
  $ollamaDestination = Join-Path $Destination 'offline\ollama\models'
  if ($ReuseExistingAssets) {
    if (-not (Test-Path -LiteralPath $ollamaDestination -PathType Container)) {
      throw "Cannot reuse missing Ollama model store: $ollamaDestination"
    }
    Write-Host 'Reusing existing Ollama model store.'
  } else {
    $ollamaSource = Join-Path $env:USERPROFILE '.ollama\models'
    if (-not (Test-Path -LiteralPath $ollamaSource)) { throw "Ollama model store not found: $ollamaSource" }
    if ($PSCmdlet.ShouldProcess($ollamaDestination, 'Copy Ollama model store')) {
      New-Item -ItemType Directory -Path $ollamaDestination -Force | Out-Null
      Get-ChildItem -LiteralPath $ollamaSource -Force | Copy-Item -Destination $ollamaDestination -Recurse -Force
    }
  }
}

if (-not $SkipDmlStores) {
  $portableStoreRoot = Join-Path $Destination 'offline\daystrom\stores'
  if (Test-Path -LiteralPath $portableStoreRoot -PathType Container) {
    $assets += @(Get-ChildItem -LiteralPath $portableStoreRoot -File -Recurse -Force | ForEach-Object { $_.FullName })
  }
}

$commit = Get-SourceCommit $RepoRoot
$assetInfo = @()
foreach ($asset in $assets) {
  if (-not (Test-Path -LiteralPath $asset)) { continue }
  $item = Get-Item -LiteralPath $asset
  $hash = $null
  if (-not $SkipChecksums) { $hash = Get-FileSha256 $asset }
  $assetInfo += [ordered]@{
    path = $asset.Substring($Destination.Length).TrimStart('\') -replace '\\', '/'
    bytes = $item.Length
    sha256 = $hash
  }
}

$manifest = [ordered]@{
  schema_version = 2
  created_utc = (Get-Date).ToUniversalTime().ToString('o')
  source_commit = $commit
  includes_vllm_runtime = [bool]$IncludeVllmRuntime
  includes_ollama_models = [bool]$IncludeOllamaModels
  includes_daystrom_stores = -not [bool]$SkipDmlStores
  daystrom_stores = @($bundledDaystromStores)
  assets = $assetInfo
  notes = 'Project DML/CMA state is bundled by default. Windows, WSL2, the NVIDIA host driver, and private Daystrom source are not bundled.'
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
