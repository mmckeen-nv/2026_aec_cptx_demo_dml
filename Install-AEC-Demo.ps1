#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [ValidateSet('viewer', 'agent', 'summit', 'enhancement', 'full')]
  [string]$Tier = 'agent',
  [switch]$InstallDependencies,
  [switch]$Configure,
  [switch]$ProvisionVllm,
  [switch]$StartVllm,
  [string]$PortableBundle,
  [switch]$OfflineOnly,
  [switch]$SkipProfiles,
  [switch]$SkipLaunchers,
  [switch]$SkipControlPlane,
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
$SummitMode = $Tier -eq 'summit'

if ($SummitMode -and ($ProvisionVllm -or $StartVllm)) {
  throw 'The summit tier is remote-inference + DML only. It never provisions or starts vLLM/Qwen containers.'
}

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

function Repair-HermesDmlContinuation {
  param([string]$HermesRoot)

  $compressor = Join-Path $HermesRoot 'hermes-agent\agent\context_compressor.py'
  if (-not (Test-Path -LiteralPath $compressor -PathType Leaf)) {
    Write-Warning "Hermes context compressor not found at $compressor; DML continuation repair was skipped."
    return
  }

  $source = Read-Utf8Text $compressor
  $marker = 'Continue from the Daystrom DML checkpoint. First inspect'
  if ($source.Contains($marker)) {
    Write-Host "Current: Hermes DML continuation repair"
    return
  }
  if (-not $source.Contains('dml_first_enabled')) {
    Write-Warning 'This Hermes installation does not include DML-first compaction; install the supported Hermes/Daystrom integration before applying the continuation repair.'
    return
  }

  $anchor = "        self.compression_count += 1"
  $insert = @'
        # A DML-first tool tail can contain only assistant/tool roles. Several
        # OpenAI-compatible local endpoints reject that shape with
        # "No user query found in messages", so provide a bounded continuation.
        if (
            getattr(self, "dml_first_enabled", False)
            and not any(msg.get("role") == "user" for msg in compressed)
        ):
            compressed.append({
                "role": "user",
                "content": (
                    "Continue from the Daystrom DML checkpoint. First inspect "
                    "the current application state and identify the active "
                    "phase. Do not repeat completed work. Then perform only "
                    "the next bounded remaining action."
                ),
            })

'@
  $anchorIndex = $source.LastIndexOf($anchor, [StringComparison]::Ordinal)
  if ($anchorIndex -lt 0) {
    Write-Warning 'Hermes context compressor layout is not recognized; DML continuation repair was skipped without modifying Hermes.'
    return
  }

  if ($script:InstallerCmdlet.ShouldProcess($compressor, 'Repair DML-first post-compaction continuation')) {
    $backup = "$compressor.bak-dml-continuation-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $compressor -Destination $backup
    $updated = $source.Insert($anchorIndex, $insert)
    Write-Utf8Text $compressor $updated
    Write-Host "Repaired Hermes DML continuation; backup: $backup"
    Write-Warning 'Restart active Hermes sessions before expecting this core repair to take effect.'
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

function Get-NpmCommand {
  $managed = Join-Path $HermesHome 'node\npm.cmd'
  if (Test-Path -LiteralPath $managed -PathType Leaf) { return $managed }
  $command = Get-Command npm.cmd -ErrorAction SilentlyContinue
  if ($command) { return $command.Source }
  return $null
}

function Install-DaystromAecPatch {
  param([string]$DmlSource)
  if (-not $DmlSource) { return }
  $patch = Join-Path $RepoRoot 'deployment\daystrom-dml\aec-agent-memory.patch'
  if (-not (Test-Path -LiteralPath $patch -PathType Leaf)) {
    throw "Daystrom AEC patch is missing: $patch"
  }
  $markers = @(
    @{ Path = 'dml_core\daystrom_dml\dml_adapter.py'; Text = 'mirror_agentic_memory_to_rag' },
    @{ Path = 'dml_core\daystrom_dml\memory_store.py'; Text = 'item_session_id not in' },
    @{ Path = 'dml_mcp\dml_mcp_server.py'; Text = 'Daystrom DML background preload failed' },
    @{ Path = 'integrations\hermes\plugins\daystrom_dml\__init__.py'; Text = 'dcn.iteration_extension' }
  )
  $current = $true
  foreach ($marker in $markers) {
    $target = Join-Path $DmlSource $marker.Path
    if (-not (Test-Path -LiteralPath $target -PathType Leaf) -or
        -not (Read-Utf8Text $target).Contains($marker.Text)) {
      $current = $false
      break
    }
  }
  if ($current) {
    Write-Host 'Current: Daystrom low-latency agent-memory patch'
  } else {
    if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) {
      throw 'Git is required to apply the versioned Daystrom AEC patch.'
    }
    & git.exe -C $DmlSource apply --check $patch
    if ($LASTEXITCODE -ne 0) {
      throw 'The installed Daystrom source is incompatible with deployment\daystrom-dml\aec-agent-memory.patch. Install the SOURCE_VERSIONS.md revision and rerun setup.'
    }
    if ($script:InstallerCmdlet.ShouldProcess($DmlSource, 'Apply the Daystrom low-latency agent-memory patch')) {
      Invoke-Checked 'git.exe' @('-C', $DmlSource, 'apply', $patch)
      Write-Host 'Applied Daystrom low-latency agent-memory patch.'
    }
  }
  $pluginSource = Join-Path $DmlSource 'integrations\hermes\plugins\daystrom_dml\__init__.py'
  $pluginDestination = Join-Path $HermesHome 'plugins\daystrom_dml\__init__.py'
  if (Test-Path -LiteralPath $pluginSource -PathType Leaf) {
    Install-ManagedFile $pluginSource $pluginDestination
  }
}

function Install-AecMissionControl {
  $siteRoot = Join-Path $RepoRoot 'aec-mission-control'
  $packageJson = Join-Path $siteRoot 'package.json'
  if (-not (Test-Path -LiteralPath $packageJson -PathType Leaf)) {
    Write-Warning "AEC Mission Control source is missing: $packageJson"
    return
  }
  $npm = Get-NpmCommand
  if (-not $npm) {
    Write-Warning 'AEC Mission Control requires Node.js/npm. Install Hermes managed Node or Node.js 22.13+ and rerun the installer.'
    return
  }
  if (-not $script:InstallerCmdlet.ShouldProcess($siteRoot, 'Install dependencies and build AEC Mission Control')) {
    return
  }
  if (-not (Test-Path -LiteralPath (Join-Path $siteRoot 'node_modules') -PathType Container)) {
    if ($OfflineOnly) {
      throw 'Offline setup requires aec-mission-control\node_modules or a prepared control-plane build.'
    }
    Invoke-Checked $npm @('--prefix', $siteRoot, 'ci')
  }
  Invoke-Checked $npm @('--prefix', $siteRoot, 'run', 'build')
  if (-not (Test-Path -LiteralPath (Join-Path $siteRoot '.next\BUILD_ID') -PathType Leaf)) {
    throw 'AEC Mission Control build completed without producing .next\BUILD_ID.'
  }
  Write-Host 'AEC Mission Control build: current'
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

function Enable-HermesProfilePlugin {
  param([string]$ProfileConfig, [string]$PluginName)
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  if ($content -match "(?m)^\s*-\s*$([regex]::Escape($PluginName))\s*$") { return }
  $pattern = '(?m)^(\s*enabled:\s*\r?\n)'
  if (-not [regex]::IsMatch($content, $pattern)) {
    Write-Warning "Cannot enable $PluginName because plugins.enabled is absent: $ProfileConfig"
    return
  }
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, "Enable Hermes plugin $PluginName")) {
    $backup = "$ProfileConfig.bak-$PluginName-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    $updated = [regex]::Replace($content, $pattern, "`${1}  - $PluginName`r`n", 1)
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Enabled Hermes plugin $PluginName; backup: $backup"
  }
}

function Disable-HermesProfilePlugin {
  param([string]$ProfileConfig, [string]$PluginName)
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  $pattern = "(?m)^\s*-\s*$([regex]::Escape($PluginName))\s*\r?\n?"
  if (-not [regex]::IsMatch($content, $pattern)) { return }
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, "Disable Hermes plugin $PluginName")) {
    $backup = "$ProfileConfig.bak-disable-$PluginName-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    Write-Utf8Text $ProfileConfig ([regex]::Replace($content, $pattern, ''))
    Write-Host "Disabled Hermes plugin $PluginName; backup: $backup"
  }
}

function Repair-CliffStyleProfileRuntime {
  param([string]$ProfileConfig, [string]$WorkingDirectory)
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  $updated = $content
  # The remote AEC profile can keep its large native context. Smaller local
  # profiles retain the earlier, more aggressive compaction threshold.
  $compressionThreshold = if (
    [IO.Path]::GetFullPath($WorkingDirectory).TrimEnd('\') -eq
    [IO.Path]::GetFullPath($RepoRoot).TrimEnd('\')
  ) { '0.85' } else { '0.5' }
  $updated = [regex]::Replace(
    $updated,
    '(?m)^(  threshold:\s*)[0-9.]+\s*$',
    '${1}' + $compressionThreshold
  )
  $updated = [regex]::Replace($updated, '(?m)^(  target_ratio:\s*)[0-9.]+\s*$', '${1}0.2')
  $cwdYaml = $WorkingDirectory.Replace('\', '/')
  $updated = [regex]::Replace($updated, '(?m)^(  cwd:\s*).*$','${1}' + $cwdYaml)
  if ($updated -eq $content) { return }
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, 'Align Cliff House compaction cadence and demo working directory')) {
    $backup = "$ProfileConfig.bak-cliff-style-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Aligned Cliff-style profile runtime; backup: $backup"
  }
}

function Repair-AecCptxNvidiaRuntime {
  param([string]$ProfileConfig, [switch]$RemoteOnly)
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  $updated = $content
  $modelBlock = @'
model:
  default: aws/anthropic/claude-opus-4-5
  provider: custom:nvidia_claude
  openai_runtime: auto
  context_length: 200000
  max_tokens: 32768
  supports_vision: true
'@
  $providerBlock = if ($RemoteOnly) { @'
custom_providers:
  - name: nvidia_claude
    base_url: https://inference-api.nvidia.com/v1
    api_mode: chat_completions
    key_env: NVIDIA_API_KEY
    model: aws/anthropic/claude-opus-4-5
    models:
      aws/anthropic/claude-opus-4-5:
        context_length: 200000
        supports_vision: true
  - name: nvidia_omni
    base_url: https://inference-api.nvidia.com/v1
    api_mode: chat_completions
    key_env: NVIDIA_API_KEY
    model: nvidia/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
    extra_body:
      chat_template_kwargs:
        enable_thinking: false
    models:
      nvidia/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:
        context_length: 262144
        supports_vision: true
'@ } else { @'
custom_providers:
  - name: nvidia_claude
    base_url: https://inference-api.nvidia.com/v1
    api_mode: chat_completions
    key_env: NVIDIA_API_KEY
    model: aws/anthropic/claude-opus-4-5
    models:
      aws/anthropic/claude-opus-4-5:
        context_length: 200000
        supports_vision: true
  - name: nvidia_omni
    base_url: https://inference-api.nvidia.com/v1
    api_mode: chat_completions
    key_env: NVIDIA_API_KEY
    model: nvidia/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
    extra_body:
      chat_template_kwargs:
        enable_thinking: false
    models:
      nvidia/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:
        context_length: 262144
        supports_vision: true
  - name: vllm_local
    base_url: http://localhost:8000/v1
    api_mode: chat_completions
    model: nvidia/Qwen3.6-35B-A3B-NVFP4
    extra_body:
      chat_template_kwargs:
        enable_thinking: false
    models:
      nvidia/Qwen3.6-35B-A3B-NVFP4:
        context_length: 262144
        supports_vision: true
'@ }
  $auxiliaryBlock = @'
auxiliary:
  vision:
    provider: custom:nvidia_omni
    model: nvidia/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
  compression:
    provider: main
    reasoning_effort: low
  title_generation:
    provider: main
  web_extract:
    provider: main
  goal_judge:
    provider: main
  approval:
    provider: main
  mcp:
    provider: main
  skills_hub:
    provider: main
  profile_describer:
    provider: main
  triage_specifier:
    provider: main
  kanban_decomposer:
    provider: main
  curator:
    provider: main
  tts_audio_tags:
    provider: main
'@
  $updated = [regex]::Replace($updated, '(?ms)^model:\s*\r?\n.*?(?=^\S)', $modelBlock.TrimEnd() + "`r`n", 1)
  if ($updated -match '(?ms)^custom_providers:\s*\r?\n.*?(?=^\S)') {
    $updated = [regex]::Replace($updated, '(?ms)^custom_providers:\s*\r?\n.*?(?=^\S)', $providerBlock.TrimEnd() + "`r`n", 1)
  } else {
    $updated = [regex]::Replace($updated, '(?m)^auxiliary:\s*$', $providerBlock.TrimEnd() + "`r`n" + 'auxiliary:', 1)
  }
  if ($updated -match '(?ms)^auxiliary:\s*\r?\n.*?(?=^\S)') {
    $updated = [regex]::Replace($updated, '(?ms)^auxiliary:\s*\r?\n.*?(?=^\S)', $auxiliaryBlock.TrimEnd() + "`r`n", 1)
  }
  $updated = [regex]::Replace($updated, '(?m)^(  threshold:\s*)[0-9.]+\s*$', '${1}0.85')
  $updated = [regex]::Replace($updated, '(?m)^(  memory_char_limit:\s*)\d+\s*$', '${1}2200')
  $updated = [regex]::Replace($updated, '(?m)^(    top_k:\s*)\d+\s*$', '${1}3')
  $updated = [regex]::Replace($updated, '(?m)^(    max_context_chars:\s*)\d+\s*$', '${1}2200')
  $updated = [regex]::Replace($updated, '(?m)^(    timeout_seconds:\s*)\d+\s*$', '${1}60')
  $updated = [regex]::Replace($updated, '(?m)^(  max_turns:\s*)\d+\s*$', '${1}60')
  $updated = [regex]::Replace($updated, '(?m)^(  max_turns_extension:\s*)\d+\s*$', '${1}30')
  $updated = [regex]::Replace($updated, '(?m)^(  max_turns_hard_cap:\s*)\d+\s*$', '${1}120')
  $updated = [regex]::Replace($updated, '(?m)^(  reasoning_effort:\s*)\S+\s*$', '${1}low')
  if ($updated -notmatch '(?m)^\s+fast_retrieval:\s*true\s*$') {
    $updated = [regex]::Replace($updated, '(?m)^(\s+max_context_chars:\s*2200\s*\r?\n)', "`${1}    fast_retrieval: true`r`n", 1)
  }
  if ($updated -eq $content) { return }
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, 'Configure the NVIDIA-hosted Claude Opus 4.5 and Nemotron Omni AEC runtime')) {
    $backup = "$ProfileConfig.bak-nvidia-hosted-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Configured NVIDIA-hosted Claude Opus 4.5 and Nemotron Omni AEC runtime; backup: $backup"
  }
}

function Ensure-AecNvidiaCredential {
  param([string]$ProfilePath)
  $envFile = Join-Path $ProfilePath '.env'
  $existing = if (Test-Path -LiteralPath $envFile -PathType Leaf) { Read-Utf8Text $envFile } else { '' }
  if ($existing -match '(?m)^NVIDIA_API_KEY=\S+\s*$') {
    Write-Host 'Current: NVIDIA API credential is configured for aec-cptx.'
    return
  }
  $credential = $env:NVIDIA_API_KEY
  if (-not $credential -and -not $WhatIfPreference) {
    $secure = Read-Host 'Enter the NVIDIA inference API key for Claude Opus 4.5 and Nemotron Omni' -AsSecureString
    $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { $credential = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
  }
  if (-not $credential) {
    Write-Warning 'NVIDIA_API_KEY is not configured. Set it in the process environment and rerun the installer.'
    return
  }
  if ($script:InstallerCmdlet.ShouldProcess($envFile, 'Store the NVIDIA API key in the ignored Hermes profile environment')) {
    $parent = Split-Path -Parent $envFile
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    $normalized = $existing.TrimEnd()
    if ($normalized) { $normalized += "`r`n" }
    Write-Utf8Text $envFile ($normalized + "NVIDIA_API_KEY=$credential`r`n")
    Write-Host 'Configured NVIDIA API credential for aec-cptx.'
  }
}

function Sync-CliffStyleProfileFiles {
  param([string]$ProfileName, [string]$ProfilePath)
  $deploymentName = switch ($ProfileName) {
    'aec-cptx' { 'aec-cptx-profile' }
    'bac_teapot' { 'bac-teapot-profile' }
    'rtx_pro' { 'rtx-pro-profile' }
    'cliff_hero' { 'cliff-hero-profile' }
    default { return }
  }
  Install-ManagedFile (Join-Path $RepoRoot "deployment\$deploymentName\SOUL.md") (Join-Path $ProfilePath 'SOUL.md')
  if ($ProfileName -eq 'aec-cptx') {
    Install-ManagedFile (Join-Path $RepoRoot 'deployment\aec-cptx-profile\AGENTS.md') (Join-Path $ProfilePath 'AGENTS.md')
  }
}

function Sync-VpExecutionRails {
  param([string]$ProfilePath)
  $pluginSource = Join-Path $RepoRoot 'deployment\plugins\vp_execution_rails'
  $pluginDestination = Join-Path $ProfilePath 'plugins\vp_execution_rails'
  $skillSource = Join-Path $RepoRoot 'demos\virtual_production_studio\skills\vp-studio-rhino-build'
  $skillDestination = Join-Path $ProfilePath 'skills\3d-modeling\vp-studio-rhino-build'
  $comfySkillSource = Join-Path $RepoRoot 'demos\virtual_production_studio\skills\comfyui\comfyui-cookbook'
  $comfySkillDestination = Join-Path $ProfilePath 'skills\comfyui\comfyui-cookbook'
  New-Item -ItemType Directory -Path $pluginDestination -Force | Out-Null
  New-Item -ItemType Directory -Path $skillDestination -Force | Out-Null
  New-Item -ItemType Directory -Path $comfySkillDestination -Force | Out-Null
  Install-ManagedFile (Join-Path $pluginSource 'plugin.yaml') (Join-Path $pluginDestination 'plugin.yaml')
  Install-ManagedFile (Join-Path $pluginSource '__init__.py') (Join-Path $pluginDestination '__init__.py')
  Install-ManagedFile (Join-Path $skillSource 'SKILL.md') (Join-Path $skillDestination 'SKILL.md')
  Install-ManagedFile (Join-Path $RepoRoot 'demos\virtual_production_studio\prompts\01a_locked_scene_manifest.md') (Join-Path $skillDestination 'SCENE_MANIFEST.md')
  Install-ManagedFile (Join-Path $comfySkillSource 'SKILL.md') (Join-Path $comfySkillDestination 'SKILL.md')
  Enable-HermesProfilePlugin (Join-Path $ProfilePath 'config.yaml') 'vp_execution_rails'
}

function Sync-TeapotExecutionRails {
  param([string]$ProfilePath)
  $pluginSource = Join-Path $RepoRoot 'deployment\plugins\teapot_execution_rails'
  $pluginDestination = Join-Path $ProfilePath 'plugins\teapot_execution_rails'
  New-Item -ItemType Directory -Path $pluginDestination -Force | Out-Null
  Install-ManagedFile (Join-Path $pluginSource 'plugin.yaml') (Join-Path $pluginDestination 'plugin.yaml')
  Install-ManagedFile (Join-Path $pluginSource '__init__.py') (Join-Path $pluginDestination '__init__.py')
  Enable-HermesProfilePlugin (Join-Path $ProfilePath 'config.yaml') 'teapot_execution_rails'
}

function Sync-CliffHeroExecutionRails {
  param([string]$ProfilePath)
  $pluginSource = Join-Path $RepoRoot 'deployment\plugins\cliff_hero_execution_rails'
  $pluginDestination = Join-Path $ProfilePath 'plugins\cliff_hero_execution_rails'
  New-Item -ItemType Directory -Path $pluginDestination -Force | Out-Null
  Install-ManagedFile (Join-Path $pluginSource 'plugin.yaml') (Join-Path $pluginDestination 'plugin.yaml')
  Install-ManagedFile (Join-Path $pluginSource '__init__.py') (Join-Path $pluginDestination '__init__.py')
  Enable-HermesProfilePlugin (Join-Path $ProfilePath 'config.yaml') 'cliff_hero_execution_rails'
}

function Repair-TeapotDemoRuntime {
  param([string]$ProfileConfig)
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  $updated = [regex]::Replace($content, '(?ms)^  obs:\s*\r?\n.*?(?=^  \S|^\S|\z)', '')
  $updated = [regex]::Replace($updated, '(?m)^(  nudge_interval:\s*)\d+\s*$', '${1}0')
  $updated = [regex]::Replace($updated, '(?m)^(  creation_nudge_interval:\s*)\d+\s*$', '${1}0')
  if ($updated -eq $content) { return }
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, 'Remove stale OBS MCP and background review forks for BAC Teapot')) {
    $backup = "$ProfileConfig.bak-teapot-runtime-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Hardened BAC Teapot runtime; backup: $backup"
  }
}

function Ensure-DemoMemoryMcps {
  param([string]$ProfileConfig, [string]$DmlLauncher, [string]$CmaLauncher)
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  $mcp = [regex]::Match($content, '(?ms)^mcp_servers:\s*\r?\n(?<body>.*?)(?=^\S|\z)')
  if (-not $mcp.Success) { return }
  $blocks = [System.Collections.Generic.List[string]]::new()
  if ($mcp.Groups['body'].Value -notmatch '(?m)^  daystrom_dml:\s*$') {
    $path = "$env:LOCALAPPDATA/hermes/integrations/daystrom-dml/bin/$DmlLauncher"
    $blocks.Add("  daystrom_dml:`r`n    command: cmd`r`n    args:`r`n    - /c`r`n    - $path`r`n    connect_timeout: 30`r`n    timeout: 180")
  }
  if ($mcp.Groups['body'].Value -notmatch '(?m)^  cma:\s*$') {
    $path = "$env:LOCALAPPDATA/hermes/integrations/daystrom-dml/bin/$CmaLauncher"
    $blocks.Add("  cma:`r`n    command: cmd`r`n    args:`r`n    - /c`r`n    - $path`r`n    connect_timeout: 30`r`n    timeout: 180")
  }
  if ($blocks.Count -eq 0) { return }
  $insert = ($blocks -join "`r`n") + "`r`n"
  $updated = [regex]::Replace($content, '(?m)^mcp_servers:\s*$', "mcp_servers:`r`n$insert", 1)
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, 'Add isolated Daystrom DML and CMA MCP registrations')) {
    $backup = "$ProfileConfig.bak-memory-mcps-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Added isolated memory MCPs; backup: $backup"
  }
}

function Repair-CliffHeroLocalRuntime {
  param([string]$ProfileConfig)
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  $updated = $content
  $modelBlock = @'
model:
  default: nvidia/Qwen3.6-35B-A3B-NVFP4
  provider: custom:vllm_local
  base_url: http://localhost:8000/v1
  context_length: 262144
  api_mode: chat_completions
'@
  $updated = [regex]::Replace($updated, '(?ms)^model:\s*\r?\n.*?(?=^\S)', $modelBlock.TrimEnd() + "`r`n", 1)
  if ($updated -notmatch '(?m)^  vllm_local:\s*$') {
    $providerBlock = @'
  vllm_local:
    name: Local vLLM (WSL2 Docker)
    api: http://localhost:8000/v1
    key_env: VLLM_API_KEY
    default_model: nvidia/Qwen3.6-35B-A3B-NVFP4
    transport: chat_completions
    context_length: 262144
  vllm_vision:
    name: Local vLLM Vision (WSL2 Docker, GPU1)
    api: http://localhost:8001/v1
    key_env: VLLM_API_KEY
    default_model: nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4
    transport: chat_completions
    context_length: 65536
'@
    $updated = [regex]::Replace($updated, '(?m)^providers:\s*$', "providers:`r`n" + $providerBlock.TrimEnd(), 1)
  }
  $auxBlock = @'
auxiliary:
  vision:
    provider: custom:vllm_vision
    model: nvidia/Nemotron-3-Nano-Omni-30B-A3B-Reasoning-NVFP4
    base_url: http://localhost:8001/v1
    temperature: 0.2
    max_tokens: 512
    extra_body:
      top_k: 1
      chat_template_kwargs:
        enable_thinking: false
  compression:
    provider: custom:vllm_local
    model: nvidia/Qwen3.6-35B-A3B-NVFP4
  title_generation:
    provider: custom:vllm_local
    model: nvidia/Qwen3.6-35B-A3B-NVFP4
  approval:
    provider: custom:vllm_local
    model: nvidia/Qwen3.6-35B-A3B-NVFP4
  mcp:
    provider: custom:vllm_local
    model: nvidia/Qwen3.6-35B-A3B-NVFP4
  skills_hub:
    provider: custom:vllm_local
    model: nvidia/Qwen3.6-35B-A3B-NVFP4
'@
  $updated = [regex]::Replace($updated, '(?ms)^auxiliary:\s*\r?\n.*?(?=^\S)', $auxBlock.TrimEnd() + "`r`n", 1)
  $updated = [regex]::Replace($updated, '(?ms)^  obs:\s*\r?\n.*?(?=^  \S|^\S|\z)', '')
  # Repair profiles previously migrated by the older OBS regex, which could
  # leave plugins.enabled indented under mcp_servers.
  $updated = [regex]::Replace(
    $updated,
    '(?m)^  enabled:\s*\r?\n  - daystrom_dml\s*\r?\n  disabled:\s*\[\]\s*$',
    "plugins:`r`n  enabled:`r`n  - daystrom_dml`r`n  disabled: []"
  )
  $updated = [regex]::Replace($updated, '(?m)^(  nudge_interval:\s*)\d+\s*$', '${1}0')
  $updated = [regex]::Replace($updated, '(?m)^(  creation_nudge_interval:\s*)\d+\s*$', '${1}0')
  if ($updated -notmatch '(?ms)^mcp_servers:\s*\r?\n.*?^  daystrom_dml:\s*$') {
    $dml = "$env:LOCALAPPDATA/hermes/integrations/daystrom-dml/bin/dml_mcp_server_cliff_hero.cmd"
    $block = "  daystrom_dml:`r`n    command: cmd`r`n    args:`r`n    - /c`r`n    - $dml`r`n    connect_timeout: 30`r`n    timeout: 180`r`n"
    $updated = [regex]::Replace($updated, '(?m)^mcp_servers:\s*$', "mcp_servers:`r`n$block", 1)
  }
  if ($updated -notmatch '(?m)^  cma:\s*$') {
    $cma = "$env:LOCALAPPDATA/hermes/integrations/daystrom-dml/bin/cma_mcp_server_cliff_hero.cmd"
    $block = "  cma:`r`n    command: cmd`r`n    args:`r`n    - /c`r`n    - $cma`r`n    connect_timeout: 30`r`n    timeout: 180`r`n"
    $updated = [regex]::Replace($updated, '(?m)^mcp_servers:\s*$', "mcp_servers:`r`n$block", 1)
  }
  if ($updated -eq $content) { return }
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, 'Pin Cliff HERO to local Qwen/Nemotron and isolated memory MCPs')) {
    $backup = "$ProfileConfig.bak-cliff-hero-local-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Pinned Cliff HERO to local models and memory MCPs; backup: $backup"
  }
}

function Repair-RTXProDmlIsolation {
  param([string]$ProfileConfig)
  Repair-DemoDmlIsolation $ProfileConfig 'vp-studio-01' 'vp-studio-01-runtime-store' 'cma-vp-studio-01' 'dml_mcp_server_vp_studio.cmd' 'cma_mcp_server_vp_studio.cmd'
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  $updated = $content
  # The demo uses Daystrom synchronized turns; Hermes' separate background
  # memory/skill review forks only consume iterations and have repeatedly
  # generated invalid skill writes during live demos.
  $updated = [regex]::Replace($updated, '(?m)^(  nudge_interval:\s*)\d+\s*$', '${1}0')
  $updated = [regex]::Replace($updated, '(?m)^(  creation_nudge_interval:\s*)\d+\s*$', '${1}0')
  # RTX Pro does not use the inherited, stale WSL OBS wrapper. Its PowerShell
  # banner corrupts MCP stdio and floods startup with JSON-RPC errors.
  $updated = [regex]::Replace($updated, '(?ms)^  obs:\s*\r?\n.*?(?=^  \S|\z)', '')
  if ($updated -eq $content) { return }
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, 'Disable background review forks and stale OBS MCP for RTX Pro')) {
    $backup = "$ProfileConfig.bak-rtx-demo-runtime-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Hardened RTX Pro demo runtime; backup: $backup"
  }
}

function Repair-DemoApplicationMcps {
  param([string]$ProfileConfig, [bool]$IncludeRhino = $true)
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  if ($content -notmatch '(?m)^mcp_servers:\s*$') {
    Write-Warning "Cannot add application MCPs because mcp_servers is absent: $ProfileConfig"
    return
  }
  $withoutRhino = if ($IncludeRhino) { $content } else {
    [regex]::Replace($content, '(?ms)^  rhino:\s*\r?\n.*?(?=^  \S|\z)', '')
  }
  $removedRhino = $withoutRhino -ne $content
  $content = $withoutRhino
  # Hermes requires args to be a YAML sequence. `hermes config set` can
  # accidentally serialize a JSON array as one scalar string, which prevents
  # every affected MCP from starting even though the text looks list-like.
  $serializedArgsPattern = '(?m)^(?<indent>[ \t]+)args:\s*''(?<json>\[.*\])''\s*$'
  $normalized = [regex]::Replace($content, $serializedArgsPattern, [System.Text.RegularExpressions.MatchEvaluator]{
    param($match)
    try { $values = @($match.Groups['json'].Value | ConvertFrom-Json -ErrorAction Stop) } catch { return $match.Value }
    $indent = $match.Groups['indent'].Value
    $lines = [System.Collections.Generic.List[string]]::new()
    $lines.Add("${indent}args:")
    foreach ($value in $values) {
      $escaped = ([string]$value).Replace("'", "''")
      $lines.Add("${indent}- '$escaped'")
    }
    return ($lines -join "`n")
  })
  $repairedSerializedArgs = $normalized -ne $content
  $content = $normalized
  # MCP stdio validation also requires every env value to be a string. YAML
  # otherwise converts these common Blender values to int/bool before Hermes
  # can start the server.
  $typedEnv = [regex]::Replace($content, '(?m)^(\s+BLENDER_PORT:\s*)(?:[''\"])?9876(?:[''\"])?\s*$', "`${1}'9876'")
  $typedEnv = [regex]::Replace($typedEnv, '(?m)^(\s+DISABLE_TELEMETRY:\s*)(?:[''\"])?true(?:[''\"])?\s*$', "`${1}'true'")
  $repairedEnvTypes = $typedEnv -ne $content
  $content = $typedEnv
  $blocks = [System.Collections.Generic.List[string]]::new()
  if ($IncludeRhino -and $content -notmatch '(?m)^  rhino:\s*$') {
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
  if ($blocks.Count -eq 0 -and -not $repairedSerializedArgs -and -not $repairedEnvTypes -and -not $removedRhino) { return }
  $updated = $content
  if ($blocks.Count -gt 0) {
    $insert = ($blocks -join "`n") + "`n"
    $updated = [regex]::Replace($content, '(?m)^mcp_servers:\s*$', "mcp_servers:`n$insert", 1)
  }
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, 'Repair demo-specific Blender/Rhino MCP registrations and MCP argument types')) {
    $backup = "$ProfileConfig.bak-app-mcp-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Repaired application MCP registrations; backup: $backup"
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
  param(
    [string]$DemoName,
    [string]$StoreName,
    [string]$ProjectId,
    [string]$KnowledgePath,
    [string]$TenantId = 'aec-cptx',
    [string]$ClientId = 'citizen-snips-aec-demo'
  )
  $python = Join-Path $HermesHome 'integrations\daystrom-dml\.venv-dml\Scripts\python.exe'
  $config = Join-Path $HermesHome 'integrations\daystrom-dml\config\aec-cptx-portable.yaml'
  $knowledge = if ($KnowledgePath) { Join-Path $RepoRoot $KnowledgePath } else { Join-Path $RepoRoot "demos\$DemoName\knowledge\dml" }
  $storage = Join-Path $HermesHome "integrations\daystrom-dml\stores\$StoreName"
  $seedScript = Join-Path $RepoRoot 'scripts\seed_demo_dml.py'
  if (-not (Test-Path -LiteralPath $python -PathType Leaf) -or
      -not (Test-Path -LiteralPath $config -PathType Leaf) -or
      -not (Test-Path -LiteralPath $knowledge -PathType Container)) { return }
  if ($script:InstallerCmdlet.ShouldProcess($storage, "Seed durable $DemoName DML knowledge")) {
    & $python $seedScript --config $config --storage $storage --knowledge $knowledge --tenant-id $TenantId --client-id $ClientId --project-id $ProjectId
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
  Write-Step 'Apply the verified Daystrom agent-memory runtime fixes'
  Install-DaystromAecPatch $DmlSourceDirectory
}

function Ensure-AecDaystromMemoryConfig {
  param([string]$ProfileConfig)
  if (-not (Test-Path -LiteralPath $ProfileConfig -PathType Leaf)) { return }
  $content = Read-Utf8Text $ProfileConfig
  $integration = (Join-Path $HermesHome 'integrations\daystrom-dml').Replace('\', '/')
  $memoryBlock = @"
memory:
  memory_enabled: true
  user_profile_enabled: true
  provider: daystrom_dml
  memory_char_limit: 2200
  user_char_limit: 1375
  nudge_interval: 0
  flush_min_turns: 6
  daystrom_dml:
    integration_dir: $integration
    launcher: $integration/bin/hermes-dml-memory.cmd
    venv_python: $integration/.venv-dml/Scripts/python.exe
    source_dir: $integration/source
    storage_dir: $integration/stores/cliff-house-01-rhino-store
    config_path: $integration/config/aec-cptx-portable.yaml
    retrieval_policy: always
    enable_personality: false
    top_k: 3
    max_context_chars: 2200
    fast_retrieval: true
    embedding_model: qwen3-embedding:0.6b
    ollama_base_url: http://127.0.0.1:11434
    preflight_strict: true
    timeout_seconds: 60
    project_id: project:cliff-house-01
    sync_turns: false
    dcn:
      mode: active_read
"@
  if ($content -match '(?ms)^memory:\s*\r?\n.*?(?=^\S|\z)') {
    $updated = [regex]::Replace($content, '(?ms)^memory:\s*\r?\n.*?(?=^\S|\z)', $memoryBlock.TrimEnd() + "`r`n", 1)
  } else {
    $updated = $content.TrimEnd() + "`r`n`r`n" + $memoryBlock.TrimEnd() + "`r`n"
  }
  if ($updated -eq $content) { return }
  if ($script:InstallerCmdlet.ShouldProcess($ProfileConfig, 'Configure the compact Daystrom agent-memory provider')) {
    $backup = "$ProfileConfig.bak-daystrom-memory-$(Get-Date -Format 'yyyyMMddHHmmss')"
    Copy-Item -LiteralPath $ProfileConfig -Destination $backup
    Write-Utf8Text $ProfileConfig $updated
    Write-Host "Configured compact Daystrom agent memory; backup: $backup"
  }
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
  Write-Step 'Install isolated DML and CMA launchers'
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\aec-cptx-profile\dml_mcp_server_cliff_house.cmd') (Join-Path $dmlBin 'dml_mcp_server_cliff_house.cmd')
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\aec-cptx-profile\cma_mcp_server_cliff_house.cmd') (Join-Path $dmlBin 'cma_mcp_server_cliff_house.cmd')
  if (-not $SummitMode) {
    Install-ManagedFile (Join-Path $RepoRoot 'deployment\rtx-pro-profile\dml_mcp_server_vp_studio.cmd') (Join-Path $dmlBin 'dml_mcp_server_vp_studio.cmd')
    Install-ManagedFile (Join-Path $RepoRoot 'deployment\rtx-pro-profile\cma_mcp_server_vp_studio.cmd') (Join-Path $dmlBin 'cma_mcp_server_vp_studio.cmd')
    Install-ManagedFile (Join-Path $RepoRoot 'deployment\bac-teapot-profile\dml_mcp_server_teapot.cmd') (Join-Path $dmlBin 'dml_mcp_server_teapot.cmd')
    Install-ManagedFile (Join-Path $RepoRoot 'deployment\bac-teapot-profile\cma_mcp_server_teapot.cmd') (Join-Path $dmlBin 'cma_mcp_server_teapot.cmd')
    Install-ManagedFile (Join-Path $RepoRoot 'deployment\cliff-hero-profile\dml_mcp_server_cliff_hero.cmd') (Join-Path $dmlBin 'dml_mcp_server_cliff_hero.cmd')
    Install-ManagedFile (Join-Path $RepoRoot 'deployment\cliff-hero-profile\cma_mcp_server_cliff_hero.cmd') (Join-Path $dmlBin 'cma_mcp_server_cliff_hero.cmd')
  }
  $stores = if ($SummitMode) {
    @('cliff-house-01-rhino-store', 'cma-cliff-house-01')
  } else {
    @('vp-studio-01-runtime-store', 'cma-vp-studio-01', 'teapot-01-runtime-store', 'cma-teapot-01', 'cliff-house-01-rhino-store', 'cma-cliff-house-01', 'cliff-house-hero-runtime-store', 'cma-cliff-house-hero-01')
  }
  foreach ($store in $stores) {
    New-Item -ItemType Directory -Path (Join-Path $HermesHome "integrations\daystrom-dml\stores\$store") -Force | Out-Null
  }
}

$hermesExe = Join-Path $HermesHome 'hermes-agent\venv\Scripts\hermes.exe'
Repair-HermesDmlContinuation $HermesHome
if (-not $SkipProfiles) {
  Write-Step 'Ensure Hermes profiles exist without overwriting live profile data'
  if (-not (Test-Path -LiteralPath $hermesExe)) {
    Write-Warning "Hermes is not installed at $hermesExe; profile creation was skipped."
  } else {
    $profiles = if ($SummitMode) {
      @(@{ Name = 'aec-cptx'; Description = 'AEC RTX Summit remote-inference architectural operator with compact DML memory.' })
    } else {
      @(
        @{ Name = 'aec-cptx'; Description = 'AEC CPTX architectural visualization operator.' },
        @{ Name = 'bac_teapot'; Description = 'BAC Teapot local-model demo operator.' },
        @{ Name = 'rtx_pro'; Description = 'RTX Pro virtual production local-model operator.' },
        @{ Name = 'cliff_hero'; Description = 'Cliff House HERO Blender-to-Comfy quick demo.' }
      )
    }
    foreach ($profile in $profiles) {
      $profilePath = Join-Path $HermesHome ("profiles\" + $profile.Name)
      if (Test-Path -LiteralPath $profilePath) {
        Write-Host "Current: Hermes profile $($profile.Name)"
        Repair-DaystromRetrievalPolicy (Join-Path $profilePath 'config.yaml')
        Repair-DaystromStrictPreflight (Join-Path $profilePath 'config.yaml')
        Sync-DaystromProfilePlugin $profilePath
        Disable-HermesProfilePlugin (Join-Path $profilePath 'config.yaml') 'aec_demo_controller'
        Repair-DemoApplicationMcps (Join-Path $profilePath 'config.yaml') ($profile.Name -notin @('bac_teapot', 'cliff_hero'))
        if ($profile.Name -eq 'rtx_pro') {
          Repair-RTXProDmlIsolation (Join-Path $profilePath 'config.yaml')
          Sync-VpExecutionRails $profilePath
        }
        if ($profile.Name -eq 'bac_teapot') {
          Repair-DemoDmlIsolation (Join-Path $profilePath 'config.yaml') 'teapot-01' 'teapot-01-runtime-store' 'cma-teapot-01' 'dml_mcp_server_teapot.cmd' 'cma_mcp_server_teapot.cmd'
          Repair-TeapotDemoRuntime (Join-Path $profilePath 'config.yaml')
          Ensure-DemoMemoryMcps (Join-Path $profilePath 'config.yaml') 'dml_mcp_server_teapot.cmd' 'cma_mcp_server_teapot.cmd'
          Sync-TeapotExecutionRails $profilePath
        }
        if ($profile.Name -eq 'aec-cptx') {
          Ensure-AecDaystromMemoryConfig (Join-Path $profilePath 'config.yaml')
          Repair-DemoDmlIsolation (Join-Path $profilePath 'config.yaml') 'cliff-house-01' 'cliff-house-01-rhino-store' 'cma-cliff-house-01' 'dml_mcp_server_cliff_house.cmd' 'cma_mcp_server_cliff_house.cmd'
          Ensure-DemoMemoryMcps (Join-Path $profilePath 'config.yaml') 'dml_mcp_server_cliff_house.cmd' 'cma_mcp_server_cliff_house.cmd'
        }
        if ($profile.Name -eq 'cliff_hero') { Repair-DemoDmlIsolation (Join-Path $profilePath 'config.yaml') 'cliff-house-hero-01' 'cliff-house-hero-runtime-store' 'cma-cliff-house-hero-01' 'dml_mcp_server_cliff_hero.cmd' 'cma_mcp_server_cliff_hero.cmd' }
        if ($profile.Name -eq 'cliff_hero') {
          Repair-CliffHeroLocalRuntime (Join-Path $profilePath 'config.yaml')
          Ensure-DemoMemoryMcps (Join-Path $profilePath 'config.yaml') 'dml_mcp_server_cliff_hero.cmd' 'cma_mcp_server_cliff_hero.cmd'
          Sync-CliffHeroExecutionRails $profilePath
        }
        $workingDirectory = if ($profile.Name -eq 'aec-cptx') { $RepoRoot } elseif ($profile.Name -eq 'rtx_pro') { Join-Path $RepoRoot 'demos\virtual_production_studio' } elseif ($profile.Name -eq 'cliff_hero') { Join-Path $RepoRoot 'demos\cliff_house\hero' } else { Join-Path $RepoRoot 'demos\teapot' }
        Repair-CliffStyleProfileRuntime (Join-Path $profilePath 'config.yaml') $workingDirectory
        if ($profile.Name -eq 'aec-cptx') {
          Repair-AecCptxNvidiaRuntime (Join-Path $profilePath 'config.yaml') -RemoteOnly:$SummitMode
          Ensure-AecNvidiaCredential $profilePath
        }
        Sync-CliffStyleProfileFiles $profile.Name $profilePath
        continue
      }
      if ($PSCmdlet.ShouldProcess($profile.Name, 'Create Hermes profile by cloning default')) {
        Invoke-Checked $hermesExe @('profile', 'create', $profile.Name, '--clone', '--clone-from', 'default', '--no-alias', '--description', $profile.Description)
        Repair-DaystromRetrievalPolicy (Join-Path $profilePath 'config.yaml')
        Repair-DaystromStrictPreflight (Join-Path $profilePath 'config.yaml')
        Sync-DaystromProfilePlugin $profilePath
        Disable-HermesProfilePlugin (Join-Path $profilePath 'config.yaml') 'aec_demo_controller'
        Repair-DemoApplicationMcps (Join-Path $profilePath 'config.yaml') ($profile.Name -notin @('bac_teapot', 'cliff_hero'))
        if ($profile.Name -eq 'rtx_pro') {
          Repair-RTXProDmlIsolation (Join-Path $profilePath 'config.yaml')
          Sync-VpExecutionRails $profilePath
        }
        if ($profile.Name -eq 'bac_teapot') {
          Repair-DemoDmlIsolation (Join-Path $profilePath 'config.yaml') 'teapot-01' 'teapot-01-runtime-store' 'cma-teapot-01' 'dml_mcp_server_teapot.cmd' 'cma_mcp_server_teapot.cmd'
          Repair-TeapotDemoRuntime (Join-Path $profilePath 'config.yaml')
          Ensure-DemoMemoryMcps (Join-Path $profilePath 'config.yaml') 'dml_mcp_server_teapot.cmd' 'cma_mcp_server_teapot.cmd'
          Sync-TeapotExecutionRails $profilePath
        }
        if ($profile.Name -eq 'aec-cptx') {
          Ensure-AecDaystromMemoryConfig (Join-Path $profilePath 'config.yaml')
          Repair-DemoDmlIsolation (Join-Path $profilePath 'config.yaml') 'cliff-house-01' 'cliff-house-01-rhino-store' 'cma-cliff-house-01' 'dml_mcp_server_cliff_house.cmd' 'cma_mcp_server_cliff_house.cmd'
          Ensure-DemoMemoryMcps (Join-Path $profilePath 'config.yaml') 'dml_mcp_server_cliff_house.cmd' 'cma_mcp_server_cliff_house.cmd'
        }
        if ($profile.Name -eq 'cliff_hero') { Repair-DemoDmlIsolation (Join-Path $profilePath 'config.yaml') 'cliff-house-hero-01' 'cliff-house-hero-runtime-store' 'cma-cliff-house-hero-01' 'dml_mcp_server_cliff_hero.cmd' 'cma_mcp_server_cliff_hero.cmd' }
        if ($profile.Name -eq 'cliff_hero') {
          Repair-CliffHeroLocalRuntime (Join-Path $profilePath 'config.yaml')
          Ensure-DemoMemoryMcps (Join-Path $profilePath 'config.yaml') 'dml_mcp_server_cliff_hero.cmd' 'cma_mcp_server_cliff_hero.cmd'
          Sync-CliffHeroExecutionRails $profilePath
        }
        $workingDirectory = if ($profile.Name -eq 'aec-cptx') { $RepoRoot } elseif ($profile.Name -eq 'rtx_pro') { Join-Path $RepoRoot 'demos\virtual_production_studio' } elseif ($profile.Name -eq 'cliff_hero') { Join-Path $RepoRoot 'demos\cliff_house\hero' } else { Join-Path $RepoRoot 'demos\teapot' }
        Repair-CliffStyleProfileRuntime (Join-Path $profilePath 'config.yaml') $workingDirectory
        if ($profile.Name -eq 'aec-cptx') {
          Repair-AecCptxNvidiaRuntime (Join-Path $profilePath 'config.yaml') -RemoteOnly:$SummitMode
          Ensure-AecNvidiaCredential $profilePath
        }
        Sync-CliffStyleProfileFiles $profile.Name $profilePath
      }
    }
    Write-Host 'Sanitized config examples were not copied over live config.yaml files; only the required DML retrieval policy is migrated.'
  }
}

if (-not $SkipControlPlane -and $Tier -in @('agent', 'summit', 'full')) {
  Write-Step 'Build the AEC Mission Control dashboard'
  Install-AecMissionControl
}

if (-not $SkipLaunchers) {
  Write-Step 'Install managed PowerShell launchers and Desktop shortcuts'
  $bin = Join-Path $HermesHome 'bin'
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\rtx-pro-profile\Test-RTX-Pro-Preflight.ps1') (Join-Path $bin 'Test-RTX-Pro-Preflight.ps1')
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\aec-cptx-profile\Start-Hermes-AEC-Rhino-DML.ps1') (Join-Path $bin 'Start-Hermes-AEC-Rhino-DML.ps1')
  Install-ManagedFile (Join-Path $RepoRoot 'deployment\aec-control-plane\Start-AEC-Control-Plane.ps1') (Join-Path $bin 'Start-AEC-Control-Plane.ps1')

  if (-not $SummitMode) {
    Install-ManagedFile (Join-Path $RepoRoot 'deployment\bac-teapot-profile\Start-BAC_Teapot.ps1') (Join-Path $bin 'Start-BAC_Teapot.ps1')
    Install-ManagedFile (Join-Path $RepoRoot 'deployment\rtx-pro-profile\Start-RTX-Pro.ps1') (Join-Path $bin 'Start-RTX-Pro.ps1')
    Install-ManagedFile (Join-Path $RepoRoot 'deployment\cliff-hero-profile\Start-Cliff-Hero-Quick.ps1') (Join-Path $bin 'Start-Cliff-Hero-Quick.ps1')
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
  }
  Install-ManagedText (Join-Path $LauncherDirectory 'Hermes-AEC-CPTX.bat') @'
@echo off
title AEC CPTX - Hermes Rhino DML
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\hermes\bin\Start-Hermes-AEC-Rhino-DML.ps1"
'@
  Install-ManagedText (Join-Path $LauncherDirectory 'AEC_CLIFFHOUSE_CLI.bat') @'
@echo off
setlocal
title AEC Cliff House - Hermes CLI
set "HERMES_HOME=%LOCALAPPDATA%\hermes"
set "HERMES_PROFILE=aec-cptx"
set "AEC_DEMO_ID=cliff-house-01"
if not defined AEC_DEMO_ROOT (
  for /f "tokens=2,*" %%A in ('reg query HKCU\Environment /v AEC_DEMO_ROOT 2^>nul ^| findstr /i AEC_DEMO_ROOT') do set "AEC_DEMO_ROOT=%%B"
)
if not defined AEC_DEMO_ROOT (
  echo AEC_DEMO_ROOT is not configured. Rerun the AEC RTX Summit installer.
  pause
  exit /b 2
)
if not exist "%AEC_DEMO_ROOT%\deployment\aec-cptx-profile\config.example.yaml" (
  echo The installed AEC demo payload is missing: %AEC_DEMO_ROOT%
  pause
  exit /b 3
)
if not exist "%HERMES_HOME%\hermes-agent\venv\Scripts\hermes.exe" (
  echo Hermes is not installed under %HERMES_HOME%.
  pause
  exit /b 4
)
cd /d "%AEC_DEMO_ROOT%"
"%HERMES_HOME%\hermes-agent\venv\Scripts\hermes.exe" -p "%HERMES_PROFILE%" --cli
set "HERMES_EXIT=%ERRORLEVEL%"
if not "%HERMES_EXIT%"=="0" (
  echo.
  echo Hermes exited with code %HERMES_EXIT%.
  pause
)
exit /b %HERMES_EXIT%
'@
  Install-ManagedText (Join-Path $LauncherDirectory 'AEC Mission Control.bat') @'
@echo off
title AEC Mission Control
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\hermes\bin\Start-AEC-Control-Plane.ps1"
'@
  if (-not $SummitMode) {
    Install-ManagedText (Join-Path $LauncherDirectory 'Cliff_HERO_Quick.bat') @'
@echo off
title Cliff House HERO - Blender to ComfyUI Quick Demo
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%LOCALAPPDATA%\hermes\bin\Start-Cliff-Hero-Quick.ps1"
'@
  }
}

if ($ProvisionVllm -or $StartVllm -or $PortableBundle) {
  $wslRepo = Get-WslRepoInfo $RepoRoot $Distro
  if (-not $WhatIfPreference) { Ensure-WslDriveMounted $wslRepo }
  Write-Host "WSL repository: $($wslRepo.Distro):$($wslRepo.Path)"
}

if ($ProvisionVllm -and $PSCmdlet.ShouldProcess($wslRepo.Distro, 'Provision Docker and NVIDIA vLLM runtime')) {
  Write-Step 'Provision WSL2 Docker and NVIDIA Container Toolkit'
  $provisionArgs = @('-d', $wslRepo.Distro, '-u', 'root', '-e')
  $bundledImage = if ($PortableBundle) { Join-Path $PortableBundle 'offline\docker\vllm-openai.tar' } else { $null }
  if ($bundledImage -and (Test-Path -LiteralPath $bundledImage -PathType Leaf)) {
    $provisionArgs += @('env', 'AEC_SKIP_VLLM_PULL=1')
  }
  $provisionArgs += @('bash', "$($wslRepo.Path)/deployment/wsl-vllm/provision-wsl2.sh")
  Invoke-Checked 'wsl.exe' $provisionArgs
}

if ($PortableBundle) {
  Write-Step 'Restore available portable runtime assets'
  Restore-PortableAssets $PortableBundle $wslRepo -RequireOffline:$OfflineOnly
}

Write-Step 'Seed repository-owned knowledge into demo DML stores'
Seed-DemoDmlKnowledge 'cliff_house' 'cliff-house-01-rhino-store' 'project:cliff-house-01' 'knowledge\dml\tool_memory_v2' 'openclaw' 'snips2'
if (-not $SummitMode) {
  Seed-DemoDmlKnowledge 'virtual_production_studio' 'vp-studio-01-runtime-store' 'project:vp-studio-01'
  Seed-DemoDmlKnowledge 'cliff_house' 'cliff-house-hero-runtime-store' 'project:cliff-house-hero-01'
  Seed-DemoDmlKnowledge 'teapot' 'teapot-01-runtime-store' 'project:teapot-01'
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
if ($SummitMode) {
  Write-Host 'AEC RTX Summit mode installed remote Claude Opus 4.5 + compact DML; no local vLLM/Qwen chat or vision containers were provisioned.'
} else {
  Write-Host 'Large model downloads, Rhino, and private Daystrom source are never installed implicitly.'
}
exit $preflightCode
