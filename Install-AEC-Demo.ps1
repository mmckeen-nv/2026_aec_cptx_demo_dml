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

function Read-Utf8Text {
  param([string]$Path)
  $utf8 = New-Object System.Text.UTF8Encoding($false, $true)
  return [IO.File]::ReadAllText($Path, $utf8)
}

function Write-Utf8Text {
  param([string]$Path, [string]$Content)
  $utf8 = New-Object System.Text.UTF8Encoding($false)
  [IO.File]::WriteAllText($Path, $Content, $utf8)
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

function Repair-DaystromRetrievalPolicy {
  param([string]$ProfileConfig)
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  $pattern = '(?m)^(\s*retrieval_policy:\s*)conditional(\s*(?:#.*)?)$'
  if (-not [regex]::IsMatch($content, $pattern)) { return }
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, 'Set Daystrom DML retrieval_policy to always')) {
    $backup = "$ProfileConfig.bak-dml-policy-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    $updated = [regex]::Replace($content, $pattern, '${1}always${2}')
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Updated Daystrom DML retrieval policy; backup: $backup"
  }
}

function Repair-DaystromStrictPreflight {
  param([string]$ProfileConfig)
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  if ($content -match '(?m)^\s+preflight_strict:\s*true\s*$') { return }
  $pattern = '(?m)^(\s+retrieval_policy:\s*always\s*(?:#.*)?\r?\n)'
  if (-not [regex]::IsMatch($content, $pattern)) { return }
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, 'Require Daystrom provider startup preflight')) {
    $backup = "$ProfileConfig.bak-dml-strict-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    $updated = [regex]::Replace($content, $pattern, "`${1}    preflight_strict: true`r`n", 1)
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Enabled strict Daystrom startup preflight; backup: $backup"
  }
}

function Sync-DaystromProfilePlugin {
  param([string]$ProfilePath)
  $source = Join-Path $HermesHome 'plugins\daystrom_dml'
  $destination = Join-Path $ProfilePath 'plugins\daystrom_dml'
  if (-not (Test-Path -LiteralPath (Join-Path $source '__init__.py') -PathType Leaf)) {
    Write-Warning "Shared Daystrom memory plugin is missing: $source"
    return
  }
  $sourceHash = Get-FileSha256 (Join-Path $source '__init__.py')
  $destinationInit = Join-Path $destination '__init__.py'
  if ((Test-Path -LiteralPath $destinationInit -PathType Leaf) -and
      ((Get-FileSha256 $destinationInit) -eq $sourceHash)) {
    Write-Host "Current: Daystrom profile plugin $destination"
    return
  }
  if ($script:InstallerCmdlet.ShouldProcess($destination, 'Install Daystrom memory provider for named Hermes profile')) {
    New-Item -ItemType Directory -Path $destination -Force | Out-Null
    Get-ChildItem -LiteralPath $source -File -Force |
      Where-Object { $_.Name -notmatch '\.bak' } |
      Copy-Item -Destination $destination -Force
    Write-Host "Installed Daystrom profile plugin: $destination"
  }
}

function Repair-RTXProDmlIsolation {
  param([string]$ProfileConfig)
  Repair-DemoDmlIsolation $ProfileConfig 'vp-studio-01' 'vp-studio-01-runtime-store' 'cma-vp-studio-01' 'dml_mcp_server_vp_studio.cmd' 'cma_mcp_server_vp_studio.cmd'
}

function Repair-DemoApplicationMcps {
  param([string]$ProfileConfig)
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  if ($content -notmatch '(?m)^mcp_servers:\s*$') {
    Write-Warning "Cannot add application MCPs because mcp_servers is absent: $ProfileConfig"
    return
  }
  $blocks = [System.Collections.Generic.List[string]]::new()
  if ($content -notmatch '(?m)^  rhino:\s*$') {
    $router = Get-ChildItem (Join-Path $env:APPDATA 'McNeel\Rhinoceros\packages\8.0\Rhino-MCP-Platform') `
      -Filter rhino-mcp-router.exe -File -Recurse -ErrorAction SilentlyContinue |
      Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
    if ($router) {
      $routerYaml = $router.Replace('\', '/')
      $blocks.Add("  rhino:`n    command: $routerYaml`n    args:`n    - --default-version`n    - '8'`n    connect_timeout: 75`n    timeout: 180")
    }
  }
  if ($content -notmatch '(?m)^  blender:\s*$') {
    $blocks.Add("  blender:`n    command: cmd`n    args:`n    - /c`n    - uvx`n    - blender-mcp`n    connect_timeout: 30`n    env:`n      BLENDER_HOST: localhost`n      BLENDER_PORT: '9876'`n      DISABLE_TELEMETRY: 'true'`n    timeout: 180")
  }
  if ($blocks.Count -eq 0) { return }
  $insert = ($blocks -join "`n") + "`n"
  $updated = [regex]::Replace($content, '(?m)^mcp_servers:\s*$', "mcp_servers:`n$insert", 1)
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, 'Add missing Rhino/Blender MCP registrations')) {
    $backup = "$ProfileConfig.bak-app-mcp-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Added missing application MCP registrations; backup: $backup"
  }
}

function Repair-DemoDmlIsolation {
  param(
    [string]$ProfileConfig,
    [string]$ProjectId,
    [string]$DmlStore,
    [string]$CmaStore,
    [string]$DmlLauncher,
    [string]$CmaLauncher
  )
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  $updated = $content
  $updated = [regex]::Replace($updated, '(?m)^(\s*project_id:\s*)project:[^\s#]+', "`${1}project:$ProjectId")
  $updated = [regex]::Replace($updated, '(?m)^(\s*storage_dir:\s*[^\r\n]*?[\\/]stores[\\/])[^\s#]+', "`${1}$DmlStore")
  $updated = [regex]::Replace($updated, '(?im)^([ \t]*-[ \t]*[^\r\n]*?[\\/]bin[\\/])(?:dml_mcp_server[^\s]*\.cmd)([ \t]*)$', "`${1}$DmlLauncher`${2}")
  $updated = [regex]::Replace($updated, '(?im)^([ \t]*-[ \t]*[^\r\n]*?[\\/]bin[\\/])(?:cma_mcp_server[^\s]*\.cmd)([ \t]*)$', "`${1}$CmaLauncher`${2}")
  if ($updated -eq $content) { return }
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, "Set isolated Daystrom identity project:$ProjectId")) {
    $backup = "$ProfileConfig.bak-$ProjectId-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Isolated project:$ProjectId DML/CMA stores; backup: $backup"
  }
}

function Restore-PortableDaystromStores {
  param([string]$BundlePath, [string]$HermesRoot)
  $sourceRoot = Join-Path $BundlePath 'offline\daystrom\stores'
  if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) { return }
  $destinationRoot = Join-Path $HermesRoot 'integrations\daystrom-dml\stores'
  foreach ($sourceStore in Get-ChildItem -LiteralPath $sourceRoot -Directory -Force) {
    $destination = Join-Path $destinationRoot $sourceStore.Name
    $existingFiles = if (Test-Path -LiteralPath $destination) {
      @(Get-ChildItem -LiteralPath $destination -File -Recurse -Force -ErrorAction SilentlyContinue)
    } else { @() }
    if ($existingFiles.Count -gt 0) {
      Write-Host "Preserved existing Daystrom store: $destination"
      continue
    }
    if ($script:InstallerCmdlet.ShouldProcess($destination, 'Restore portable Daystrom DML/CMA store')) {
      New-Item -ItemType Directory -Path $destination -Force | Out-Null
      Get-ChildItem -LiteralPath $sourceStore.FullName -Force | Copy-Item -Destination $destination -Recurse -Force
      Write-Host "Restored Daystrom store: $destination"
    }
  }
}

function Seed-DemoDmlKnowledge {
  param([string]$DemoName, [string]$StoreName, [string]$ProjectId)
  $python = Join-Path $HermesHome 'integrations\daystrom-dml\.venv-dml\Scripts\python.exe'
  $config = Join-Path $HermesHome 'integrations\daystrom-dml\config\aec-cptx-portable.yaml'
  $knowledge = Join-Path $RepoRoot "demos\$DemoName\knowledge\dml"
  $storage = Join-Path $HermesHome "integrations\daystrom-dml\stores\$StoreName"
  $seedScript = Join-Path $RepoRoot 'scripts\seed_demo_dml.py'
  if (-not (Test-Path -LiteralPath $python -PathType Leaf) -or
      -not (Test-Path -LiteralPath $config -PathType Leaf) -or
      -not (Test-Path -LiteralPath $knowledge -PathType Container)) { return }
  if ($script:InstallerCmdlet.ShouldProcess($storage, "Seed durable $DemoName DML knowledge")) {
    & $python $seedScript --config $config --storage $storage --knowledge $knowledge --tenant-id aec-cptx --client-id citizen-snips-aec-demo --project-id $ProjectId
    if ($LASTEXITCODE -ne 0) {
      Write-Warning "DML knowledge seed for $DemoName failed; the installer preserved the store and can be rerun after the embedding service is ready."
    }
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
  Restore-PortableDaystromStores $BundlePath $HermesHome
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

$dmlBin = Join-Path $HermesHome 'integrations\daystrom-dml\bin'
if (Test-Path -LiteralPath $dmlBin -PathType Container) {
  Write-Step 'Install isolated RTX Pro DML and CMA launchers'
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\rtx-pro-profile\dml_mcp_server_vp_studio.cmd') (Join-Path $dmlBin 'dml_mcp_server_vp_studio.cmd')
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\rtx-pro-profile\cma_mcp_server_vp_studio.cmd') (Join-Path $dmlBin 'cma_mcp_server_vp_studio.cmd')
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\bac-teapot-profile\dml_mcp_server_teapot.cmd') (Join-Path $dmlBin 'dml_mcp_server_teapot.cmd')
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\bac-teapot-profile\cma_mcp_server_teapot.cmd') (Join-Path $dmlBin 'cma_mcp_server_teapot.cmd')
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\aec-cptx-profile\dml_mcp_server_cliff_house.cmd') (Join-Path $dmlBin 'dml_mcp_server_cliff_house.cmd')
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\aec-cptx-profile\cma_mcp_server_cliff_house.cmd') (Join-Path $dmlBin 'cma_mcp_server_cliff_house.cmd')
  foreach ($store in @('vp-studio-01-runtime-store', 'cma-vp-studio-01', 'teapot-01-runtime-store', 'cma-teapot-01', 'cliff-house-01-runtime-store', 'cma-cliff-house-01')) {
    New-Item -ItemType Directory -Path (Join-Path $HermesHome "integrations\daystrom-dml\stores\$store") -Force | Out-Null
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
        Repair-DaystromRetrievalPolicy (Join-Path $profilePath 'config.yaml')
        Repair-DaystromStrictPreflight (Join-Path $profilePath 'config.yaml')
        Sync-DaystromProfilePlugin $profilePath
        Repair-DemoApplicationMcps (Join-Path $profilePath 'config.yaml')
        if ($profile.Name -eq 'rtx_pro') { Repair-RTXProDmlIsolation (Join-Path $profilePath 'config.yaml') }
        if ($profile.Name -eq 'bac_teapot') { Repair-DemoDmlIsolation (Join-Path $profilePath 'config.yaml') 'teapot-01' 'teapot-01-runtime-store' 'cma-teapot-01' 'dml_mcp_server_teapot.cmd' 'cma_mcp_server_teapot.cmd' }
        if ($profile.Name -eq 'aec-cptx') { Repair-DemoDmlIsolation (Join-Path $profilePath 'config.yaml') 'cliff-house-01' 'cliff-house-01-runtime-store' 'cma-cliff-house-01' 'dml_mcp_server_cliff_house.cmd' 'cma_mcp_server_cliff_house.cmd' }
        continue
      }
      if ($PSCmdlet.ShouldProcess($profile.Name, 'Create Hermes profile by cloning default')) {
        Invoke-Checked $hermesExe @('profile', 'create', $profile.Name, '--clone', '--clone-from', 'default', '--no-alias', '--description', $profile.Description)
        Repair-DaystromRetrievalPolicy (Join-Path $profilePath 'config.yaml')
        Repair-DaystromStrictPreflight (Join-Path $profilePath 'config.yaml')
        Sync-DaystromProfilePlugin $profilePath
        Repair-DemoApplicationMcps (Join-Path $profilePath 'config.yaml')
        if ($profile.Name -eq 'rtx_pro') { Repair-RTXProDmlIsolation (Join-Path $profilePath 'config.yaml') }
        if ($profile.Name -eq 'bac_teapot') { Repair-DemoDmlIsolation (Join-Path $profilePath 'config.yaml') 'teapot-01' 'teapot-01-runtime-store' 'cma-teapot-01' 'dml_mcp_server_teapot.cmd' 'cma_mcp_server_teapot.cmd' }
        if ($profile.Name -eq 'aec-cptx') { Repair-DemoDmlIsolation (Join-Path $profilePath 'config.yaml') 'cliff-house-01' 'cliff-house-01-runtime-store' 'cma-cliff-house-01' 'dml_mcp_server_cliff_house.cmd' 'cma_mcp_server_cliff_house.cmd' }
      }
    }
    Write-Host 'Sanitized config examples were not copied over live config.yaml files; only the required DML retrieval policy is migrated.'
  }
}

if (-not $SkipLaunchers) {
  Write-Step 'Install managed PowerShell launchers and Desktop shortcuts'
  $bin = Join-Path $HermesHome 'bin'
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\bac-teapot-profile\Start-BAC_Teapot.ps1') (Join-Path $bin 'Start-BAC_Teapot.ps1')
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\rtx-pro-profile\Start-RTX-Pro.ps1') (Join-Path $bin 'Start-RTX-Pro.ps1')
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\rtx-pro-profile\Test-RTX-Pro-Preflight.ps1') (Join-Path $bin 'Test-RTX-Pro-Preflight.ps1')
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

Write-Step 'Seed repository-owned knowledge into demo DML stores'
Seed-DemoDmlKnowledge 'virtual_production_studio' 'vp-studio-01-runtime-store' 'project:vp-studio-01'
Seed-DemoDmlKnowledge 'cliff_house' 'cliff-house-01-runtime-store' 'project:cliff-house-01'
Seed-DemoDmlKnowledge 'teapot' 'teapot-01-runtime-store' 'project:teapot-01'

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
