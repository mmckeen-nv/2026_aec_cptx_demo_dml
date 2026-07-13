#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [ValidateSet('viewer', 'agent', 'enhancement', 'full')]
  [string]$Tier = 'agent',
  [switch]$InstallDependencies,
  [switch]$Configure,
  [switch]$ProvisionVllm,
  [switch]$StartVllm,
  [string]$PortableBundle,
  [switch]$OfflineOnly,
  [switch]$SkipProfiles,
  [switch]$SkipLaunchers,
  [switch]$SkipPreflight,
  [switch]$Yes,
  [string]$Distro = 'Ubuntu',
  [string]$HermesHome = (Join-Path $env:LOCALAPPDATA 'hermes'),
  [string]$DmlSourceDirectory,
  [string]$LauncherDirectory = [Environment]::GetFolderPath('Desktop')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:InstallerCmdlet = $PSCmdlet
$RepoRoot = $PSScriptRoot
$SetupScript = Join-Path $RepoRoot 'scripts\aec_setup.py'

if (-not $PortableBundle -and (Test-Path -LiteralPath (Join-Path $RepoRoot 'portable-bundle.json'))) {
  $PortableBundle = $RepoRoot
}
if ($PortableBundle) {
  $PortableBundle = (Resolve-Path -LiteralPath $PortableBundle).Path
}
if ($OfflineOnly -and -not $PortableBundle) {
  throw '-OfflineOnly requires a prepared -PortableBundle path.'
}
if ($OfflineOnly -and ($InstallDependencies -or $ProvisionVllm)) {
  throw '-InstallDependencies and -ProvisionVllm require internet access and cannot be combined with -OfflineOnly.'
}

function Write-Step([string]$Message) {
  Write-Host ''
  Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Checked {
  param([string]$FilePath, [string[]]$ArgumentList)
  & $FilePath @ArgumentList
  if ($LASTEXITCODE -ne 0) {
    throw "$FilePath exited with code $LASTEXITCODE"
  }
}

function Get-PythonCommand {
  if (Get-Command py.exe -ErrorAction SilentlyContinue) {
    return [pscustomobject]@{ File = 'py.exe'; Prefix = @('-3') }
  }
  if (Get-Command python.exe -ErrorAction SilentlyContinue) {
    return [pscustomobject]@{ File = 'python.exe'; Prefix = @() }
  }
  if (Get-Command python -ErrorAction SilentlyContinue) {
    return [pscustomobject]@{ File = 'python'; Prefix = @() }
  }
  return $null
}

function Invoke-AecSetup {
  param($Python, [string[]]$ArgumentList)
  $allArgs = @($Python.Prefix) + @($SetupScript) + $ArgumentList
  & $Python.File @allArgs | ForEach-Object { Write-Host $_ }
  return $LASTEXITCODE
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

function Install-ManagedFile {
  param([string]$Source, [string]$Destination)
  if (-not (Test-Path -LiteralPath $Source)) { throw "Managed source not found: $Source" }
  if (Test-Path -LiteralPath $Destination) {
    $same = (Get-FileSha256 $Source) -eq (Get-FileSha256 $Destination)
    if ($same) {
      Write-Host "Current: $Destination"
      return
    }
  }
  if ($script:InstallerCmdlet.ShouldProcess($Destination, 'Install managed launcher file')) {
    $parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    if (Test-Path -LiteralPath $Destination) {
      $backup = "$Destination.bak-$(Get-Date -Format 'yyyyMMddHHmmss')"
      Copy-Item -LiteralPath $Destination -Destination $backup
      Write-Host "Backed up: $backup"
    }
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
    Write-Host "Installed: $Destination"
  }
}

function Install-ManagedText {
  param([string]$Destination, [string]$Content)
  $normalized = $Content.TrimEnd() + "`r`n"
  if ((Test-Path -LiteralPath $Destination) -and
      ((Get-Content -LiteralPath $Destination -Raw) -eq $normalized)) {
    Write-Host "Current: $Destination"
    return
  }
  if ($script:InstallerCmdlet.ShouldProcess($Destination, 'Install managed desktop launcher')) {
    $parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    if (Test-Path -LiteralPath $Destination) {
      $backup = "$Destination.bak-$(Get-Date -Format 'yyyyMMddHHmmss')"
      Copy-Item -LiteralPath $Destination -Destination $backup
      Write-Host "Backed up: $backup"
    }
    Set-Content -LiteralPath $Destination -Value $normalized -Encoding ASCII -NoNewline
    Write-Host "Installed: $Destination"
  }
}

function Get-WslRepoInfo {
  param([string]$WindowsPath, [string]$RequestedDistro)
  if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw 'WSL is not installed or wsl.exe is unavailable.'
  }

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
  if ($LASTEXITCODE -ne 0 -or -not $converted) {
    throw "Could not map repository path into WSL distro '$RequestedDistro': $WindowsPath"
  }
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

function Assert-PortableManifestAssets {
  param([string]$BundlePath, $ManifestData)
  $bundleRoot = [IO.Path]::GetFullPath($BundlePath).TrimEnd('\') + '\'
  foreach ($asset in @($ManifestData.assets)) {
    $relative = ([string]$asset.path).Replace('/', '\')
    $assetPath = [IO.Path]::GetFullPath((Join-Path $BundlePath $relative))
    if (-not $assetPath.StartsWith($bundleRoot, [StringComparison]::OrdinalIgnoreCase)) {
      throw "Portable manifest asset escapes the bundle directory: $($asset.path)"
    }
    if (-not (Test-Path -LiteralPath $assetPath -PathType Leaf)) {
      throw "Portable manifest asset is missing: $assetPath"
    }
    $item = Get-Item -LiteralPath $assetPath
    if ($null -ne $asset.bytes -and $item.Length -ne [long]$asset.bytes) {
      throw "Portable manifest asset size mismatch: $assetPath"
    }
    if ($asset.sha256) {
      $actual = Get-FileSha256 $assetPath
      if ($actual -ne [string]$asset.sha256) {
        throw "Portable manifest asset checksum mismatch: $assetPath"
      }
    }
    Write-Host "Verified: $($asset.path)"
  }
}

function Restore-PortableAssets {
  param([string]$BundlePath, $WslInfo, [switch]$RequireOffline)

  $manifest = Join-Path $BundlePath 'portable-bundle.json'
  if (-not (Test-Path -LiteralPath $manifest)) {
    throw "Portable bundle manifest not found: $manifest"
  }
  $manifestData = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json
  Assert-PortableManifestAssets $BundlePath $manifestData
  $bundleWsl = Get-WslRepoInfo $BundlePath $WslInfo.Distro
  if (-not $WhatIfPreference) { Ensure-WslDriveMounted $bundleWsl }
  $dockerArchive = Join-Path $BundlePath 'offline\docker\vllm-openai.tar'
  $hfArchive = Join-Path $BundlePath 'offline\huggingface-cache.tar'
  $ollamaSource = Join-Path $BundlePath 'offline\ollama\models'

  & wsl.exe -d $WslInfo.Distro -e docker image inspect 'vllm/vllm-openai:latest' *> $null
  $hasDockerImage = $LASTEXITCODE -eq 0
  if (-not $hasDockerImage -and (Test-Path -LiteralPath $dockerArchive)) {
    if ($script:InstallerCmdlet.ShouldProcess($WslInfo.Distro, 'Load bundled vLLM Docker image')) {
      Invoke-Checked 'wsl.exe' @('-d', $WslInfo.Distro, '-e', 'docker', 'load', '-i', "$($bundleWsl.Path)/offline/docker/vllm-openai.tar")
      $hasDockerImage = $true
    }
  }

  $cachePaths = @(
    '/root/.cache/huggingface/hub/models--nvidia--Qwen3.6-35B-A3B-NVFP4/snapshots',
    '/root/.cache/huggingface/hub/models--nvidia--Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4/snapshots'
  )
  $hasModelCache = $true
  foreach ($cachePath in $cachePaths) {
    & wsl.exe -d $WslInfo.Distro -u root -e test -d $cachePath
    if ($LASTEXITCODE -ne 0) { $hasModelCache = $false }
  }
  if (-not $hasModelCache -and (Test-Path -LiteralPath $hfArchive)) {
    if ($script:InstallerCmdlet.ShouldProcess($WslInfo.Distro, 'Restore bundled Hugging Face model cache')) {
      Invoke-Checked 'wsl.exe' @('-d', $WslInfo.Distro, '-u', 'root', '-e', 'mkdir', '-p', '/root/.cache/huggingface')
      Invoke-Checked 'wsl.exe' @('-d', $WslInfo.Distro, '-u', 'root', '-e', 'tar', '-xf', "$($bundleWsl.Path)/offline/huggingface-cache.tar", '-C', '/root/.cache/huggingface')
      $hasModelCache = $true
    }
  }

  if (Test-Path -LiteralPath $ollamaSource) {
    $ollamaDestination = Join-Path $env:USERPROFILE '.ollama\models'
    if ($script:InstallerCmdlet.ShouldProcess($ollamaDestination, 'Merge bundled Ollama model store')) {
      New-Item -ItemType Directory -Path $ollamaDestination -Force | Out-Null
      $copied = 0
      $current = 0
      foreach ($sourceFile in Get-ChildItem -LiteralPath $ollamaSource -File -Recurse -Force) {
        $relative = $sourceFile.FullName.Substring($ollamaSource.Length).TrimStart('\')
        $targetFile = Join-Path $ollamaDestination $relative
        if ((Test-Path -LiteralPath $targetFile -PathType Leaf) -and
            (Get-Item -LiteralPath $targetFile).Length -eq $sourceFile.Length) {
          $current++
          continue
        }
        New-Item -ItemType Directory -Path (Split-Path -Parent $targetFile) -Force | Out-Null
        Copy-Item -LiteralPath $sourceFile.FullName -Destination $targetFile -Force
        $copied++
      }
      Write-Host "Ollama model store: $current current, $copied copied."
    }
  }

  if ($RequireOffline -and -not $hasDockerImage) {
    throw 'Offline bundle does not contain a usable vLLM Docker image.'
  }
  if ($RequireOffline -and -not $hasModelCache) {
    throw 'Offline bundle does not contain both required Hugging Face model snapshots.'
  }
}

if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
  throw 'Install-AEC-Demo.ps1 must run in Windows PowerShell or PowerShell on Windows.'
}

Write-Host 'AEC CPTX Demo Windows Bootstrapper' -ForegroundColor Green
Write-Host "Repository: $RepoRoot"
Write-Host "Tier:       $Tier"
Write-Host "Hermes:     $HermesHome"
if ($PortableBundle) { Write-Host "Bundle:     $PortableBundle" }

Write-Step 'Record the project root for Windows-native Hermes and MCP launchers'
$savedRoot = [Environment]::GetEnvironmentVariable('AEC_DEMO_ROOT', 'User')
if ($savedRoot -ne $RepoRoot) {
  if ($PSCmdlet.ShouldProcess('User environment', "Set AEC_DEMO_ROOT=$RepoRoot")) {
    [Environment]::SetEnvironmentVariable('AEC_DEMO_ROOT', $RepoRoot, 'User')
    $env:AEC_DEMO_ROOT = $RepoRoot
    Write-Host 'AEC_DEMO_ROOT saved for future sessions.'
  }
} else {
  $env:AEC_DEMO_ROOT = $RepoRoot
  Write-Host 'AEC_DEMO_ROOT is already current.'
}

if (-not $DmlSourceDirectory) {
  $installedDml = Join-Path $HermesHome 'integrations\daystrom-dml\source'
  if (Test-Path -LiteralPath (Join-Path $installedDml 'pyproject.toml') -PathType Leaf) {
    $DmlSourceDirectory = $installedDml
  }
}
if ($DmlSourceDirectory) {
  $DmlSourceDirectory = [IO.Path]::GetFullPath($DmlSourceDirectory)
  if (-not (Test-Path -LiteralPath (Join-Path $DmlSourceDirectory 'pyproject.toml') -PathType Leaf)) {
    throw "DML source is not a valid checkout (pyproject.toml missing): $DmlSourceDirectory"
  }
  $savedDml = [Environment]::GetEnvironmentVariable('DML_SOURCE_DIR', 'User')
  if ($savedDml -ne $DmlSourceDirectory) {
    if ($PSCmdlet.ShouldProcess('User environment', "Set DML_SOURCE_DIR=$DmlSourceDirectory")) {
      [Environment]::SetEnvironmentVariable('DML_SOURCE_DIR', $DmlSourceDirectory, 'User')
      Write-Host 'DML_SOURCE_DIR saved for future sessions.'
    }
  }
  $env:DML_SOURCE_DIR = $DmlSourceDirectory
  Write-Host "Daystrom DML source: $DmlSourceDirectory"
}

$python = Get-PythonCommand
if (-not $python -and $InstallDependencies) {
  if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
    throw 'Python is missing and winget.exe is unavailable. Install Python 3.10+ manually.'
  }
  if ($PSCmdlet.ShouldProcess('Python 3.12', 'Install with winget')) {
    Invoke-Checked 'winget.exe' @('install', '--id', 'Python.Python.3.12', '-e', '--accept-package-agreements', '--accept-source-agreements')
    $python = Get-PythonCommand
  }
}
if (-not $python -and (-not $SkipPreflight -or $InstallDependencies -or $Configure)) {
  throw 'Python 3.10+ is required. Re-run with -InstallDependencies or install Python manually.'
}

if ($Configure -and $PSCmdlet.ShouldProcess('config\demo.env', 'Run interactive local configuration')) {
  Write-Step 'Create user-local demo configuration'
  $code = Invoke-AecSetup $python @('--configure')
  if ($code -ne 0) { throw "Configuration exited with code $code" }
}

if ($InstallDependencies -and $PSCmdlet.ShouldProcess($Tier, 'Install supported dependencies')) {
  Write-Step "Install supported dependencies for tier '$Tier'"
  $installArgs = @('--install', '--tier', $Tier)
  if ($Yes) { $installArgs += '--yes' }
  $code = Invoke-AecSetup $python $installArgs
  if ($code -ne 0) {
    Write-Warning 'Some tier requirements still need manual installation or configuration.'
  }
}

$hermesExe = Join-Path $HermesHome 'hermes-agent\venv\Scripts\hermes.exe'
if (-not $SkipProfiles) {
  Write-Step 'Ensure Hermes profiles exist without overwriting live profile data'
  if (-not (Test-Path -LiteralPath $hermesExe)) {
    Write-Warning "Hermes is not installed at $hermesExe; profile creation was skipped."
  } else {
    $profiles = @(
      @{ Name = 'aec-cptx'; Description = 'AEC CPTX architectural visualization operator.' },
      @{ Name = 'bac_teapot'; Description = 'BAC Teapot local-model demo operator.' },
      @{ Name = 'rtx_pro'; Description = 'RTX Pro virtual production local-model operator.' }
    )
    foreach ($profile in $profiles) {
      $profilePath = Join-Path $HermesHome ("profiles\" + $profile.Name)
      if (Test-Path -LiteralPath $profilePath) {
        Write-Host "Current: Hermes profile $($profile.Name)"
        continue
      }
      if ($PSCmdlet.ShouldProcess($profile.Name, 'Create Hermes profile by cloning default')) {
        Invoke-Checked $hermesExe @('profile', 'create', $profile.Name, '--clone', '--clone-from', 'default', '--no-alias', '--description', $profile.Description)
      }
    }
    Write-Host 'Sanitized config examples were not copied over live config.yaml files.'
  }
}

if (-not $SkipLaunchers) {
  Write-Step 'Install managed PowerShell launchers and Desktop shortcuts'
  $bin = Join-Path $HermesHome 'bin'
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\bac-teapot-profile\Start-BAC_Teapot.ps1') (Join-Path $bin 'Start-BAC_Teapot.ps1')
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\rtx-pro-profile\Start-RTX-Pro.ps1') (Join-Path $bin 'Start-RTX-Pro.ps1')
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\aec-cptx-profile\Start-Hermes-AEC-Rhino-DML.ps1') (Join-Path $bin 'Start-Hermes-AEC-Rhino-DML.ps1')

  Install-ManagedText (Join-Path $LauncherDirectory 'BAC_Teapot.bat') @'
@echo off
title BAC_Teapot - Hermes Local Model Demo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\hermes\bin\Start-BAC_Teapot.ps1"
'@
  Install-ManagedText (Join-Path $LauncherDirectory 'RTX Pro.bat') @'
@echo off
title RTX Pro - Hermes Local Model Demo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\hermes\bin\Start-RTX-Pro.ps1"
'@
  Install-ManagedText (Join-Path $LauncherDirectory 'Hermes-AEC-CPTX.bat') @'
@echo off
title AEC CPTX - Hermes Rhino DML
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\hermes\bin\Start-Hermes-AEC-Rhino-DML.ps1"
'@
}

if ($ProvisionVllm -or $StartVllm -or $PortableBundle) {
  $wslRepo = Get-WslRepoInfo $RepoRoot $Distro
  if (-not $WhatIfPreference) { Ensure-WslDriveMounted $wslRepo }
  Write-Host "WSL repository: $($wslRepo.Distro):$($wslRepo.Path)"
}

if ($PortableBundle) {
  Write-Step 'Restore available portable runtime assets'
  Restore-PortableAssets $PortableBundle $wslRepo -RequireOffline:$OfflineOnly
}

if ($ProvisionVllm -and $PSCmdlet.ShouldProcess($wslRepo.Distro, 'Provision Docker and NVIDIA vLLM runtime')) {
  Write-Step 'Provision WSL2 Docker and NVIDIA Container Toolkit'
  Invoke-Checked 'wsl.exe' @('-d', $wslRepo.Distro, '-e', 'bash', "$($wslRepo.Path)/deployment/wsl-vllm/provision-wsl2.sh")
}

if ($StartVllm -and $PSCmdlet.ShouldProcess($wslRepo.Distro, 'Create/start local vLLM model containers')) {
  Write-Step 'Create or start local vLLM model containers'
  Invoke-Checked 'wsl.exe' @('-d', $wslRepo.Distro, '-u', 'root', '-e', 'bash', "$($wslRepo.Path)/deployment/wsl-vllm/run-vllm-qwen36.sh")
  Invoke-Checked 'wsl.exe' @('-d', $wslRepo.Distro, '-u', 'root', '-e', 'bash', "$($wslRepo.Path)/deployment/wsl-vllm/run-vllm-nemotron-vision.sh")
  Invoke-Checked (Join-Path $RepoRoot 'deployment\wsl-vllm\start_vllm.bat') @('--no-pause')
}

$preflightCode = 0
if (-not $SkipPreflight) {
  Write-Step "Run final '$Tier' preflight"
  $preflightCode = Invoke-AecSetup $python @('--check', '--tier', $Tier)
}

Write-Host ''
if ($preflightCode -eq 0) {
  Write-Host 'Bootstrap complete. Required checks passed.' -ForegroundColor Green
} else {
  Write-Warning 'Bootstrap completed, but one or more required checks still need attention.'
}
Write-Host 'Large model downloads, Rhino, and private Daystrom source are never installed implicitly.'
exit $preflightCode
