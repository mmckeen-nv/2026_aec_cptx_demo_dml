#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [Parameter(Mandatory = $true)]
  [string]$Destination,
  [string]$HermesHome = (Join-Path $env:LOCALAPPDATA 'hermes'),
  [string]$ComfyRoot = (Join-Path $env:USERPROFILE 'ComfyUI'),
  [string]$RhinoCoreInstaller,
  [string]$RhinoLanguagePackInstaller,
  [string]$BlenderArm64Installer,
  [string]$BlenderX64Installer
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot
$TemplateRoot = Join-Path $RepoRoot 'deployment\AEC_RTX_SUMMIT'
$DmlSource = Join-Path $HermesHome 'integrations\daystrom-dml\source'
$Destination = [IO.Path]::GetFullPath($Destination)
$ComfyRoot = [IO.Path]::GetFullPath($ComfyRoot)
$ComfyModels = @(
  [ordered]@{
    name = 'flux-2-klein-base-4b-fp8.safetensors'
    relative_path = 'diffusion_models\flux-2-klein-base-4b-fp8.safetensors'
    bytes = 4089498488L
    sha256 = '44bab3a86fe98b85d21dd2a4729ebdc3ae51fb8a39f76e457e18c724219e6840'
  },
  [ordered]@{
    name = 'qwen_3_4b.safetensors'
    relative_path = 'text_encoders\qwen_3_4b.safetensors'
    bytes = 8044982048L
    sha256 = '6c671498573ac2f7a5501502ccce8d2b08ea6ca2f661c458e708f36b36edfc5a'
  },
  [ordered]@{
    name = 'flux2-vae.safetensors'
    relative_path = 'vae\flux2-vae.safetensors'
    bytes = 336213556L
    sha256 = 'd64f3a68e1cc4f9f4e29b6e0da38a0204fe9a49f2d4053f0ec1fa1ca02f9c4b5'
  }
)
$RhinoHero = [ordered]@{
  relative_path = 'demos\cliff_house\hero\cliff_house_HERO_RHINO_MODEL.3dm'
  bytes = 15985322L
  sha256 = '029a9b8e338a12c3babef2a7a2c95f385475c0ffe09da8700fa8ade8ab2ea637'
  objects = 559
}
$ApplicationInstallers = @(
  [ordered]@{
    name = 'Rhino 8 core'
    source = $RhinoCoreInstaller
    relative_path = 'rhino\rhino.msi'
    signer_pattern = 'ROBERT MCNEEL'
  },
  [ordered]@{
    name = 'Rhino 8 English language pack'
    source = $RhinoLanguagePackInstaller
    relative_path = 'rhino\LanguagePack-en-us.msi'
    signer_pattern = 'ROBERT MCNEEL'
  },
  [ordered]@{
    name = 'Blender 5.2 ARM64'
    source = $BlenderArm64Installer
    relative_path = 'blender\blender-5.2.0-windows-arm64.msi'
    signer_pattern = 'BLENDER'
  },
  [ordered]@{
    name = 'Blender 5.2 x64'
    source = $BlenderX64Installer
    relative_path = 'blender\blender-5.2.0-windows-x64.msi'
    signer_pattern = 'BLENDER'
  }
)

function Copy-ManagedFile([string]$Source, [string]$Target) {
  if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
    throw "Required bundle source is missing: $Source"
  }
  New-Item -ItemType Directory -Path (Split-Path -Parent $Target) -Force | Out-Null
  Copy-Item -LiteralPath $Source -Destination $Target -Force
}

function Copy-FilteredTree {
  param([string]$Source, [string]$Target, [string[]]$ExcludedSegments = @())
  if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    throw "Required bundle directory is missing: $Source"
  }
  $sourceRoot = [IO.Path]::GetFullPath($Source).TrimEnd('\')
  foreach ($file in Get-ChildItem -LiteralPath $sourceRoot -File -Recurse -Force) {
    $relative = $file.FullName.Substring($sourceRoot.Length).TrimStart('\')
    $segments = @($relative -split '[\\/]')
    if ($segments | Where-Object { $_ -in $ExcludedSegments }) { continue }
    if ($file.Name -match '\.(log|pyc)$') { continue }
    Copy-ManagedFile $file.FullName (Join-Path $Target $relative)
  }
}

function Copy-ChunkedFile {
  param(
    [string]$Source,
    [string]$TargetBase,
    [long]$ChunkBytes = 2GB
  )
  New-Item -ItemType Directory -Path (Split-Path -Parent $TargetBase) -Force | Out-Null
  $input = [IO.File]::OpenRead($Source)
  try {
    $buffer = New-Object byte[] (16MB)
    $partNumber = 1
    while ($input.Position -lt $input.Length) {
      $partPath = '{0}.part{1:d3}' -f $TargetBase, $partNumber
      $output = [IO.File]::Create($partPath)
      try {
        $written = 0L
        while ($written -lt $ChunkBytes -and $input.Position -lt $input.Length) {
          $remaining = [Math]::Min([long]$buffer.Length, $ChunkBytes - $written)
          $read = $input.Read($buffer, 0, [int]$remaining)
          if ($read -le 0) { break }
          $output.Write($buffer, 0, $read)
          $written += $read
        }
      } finally {
        $output.Dispose()
      }
      $partNumber++
    }
  } finally {
    $input.Dispose()
  }
}

function Get-VerifiedInstallerMetadata {
  param([Collections.IDictionary]$Installer)
  if ([string]::IsNullOrWhiteSpace($Installer.source) -or
      -not (Test-Path -LiteralPath $Installer.source -PathType Leaf)) {
    throw ("Required offline installer is missing for {0}. Pass its path to the bundle generator." -f
      $Installer.name)
  }
  $source = [IO.Path]::GetFullPath($Installer.source)
  if ([IO.Path]::GetExtension($source) -notin @('.msi', '.exe')) {
    throw "Unsupported installer type for $($Installer.name): $source"
  }
  $signature = Get-AuthenticodeSignature -LiteralPath $source
  $signer = if ($signature.SignerCertificate) { $signature.SignerCertificate.Subject } else { '' }
  if ($signature.Status -ne 'Valid' -or $signer -notmatch $Installer.signer_pattern) {
    throw "Authenticode verification failed for $($Installer.name): status=$($signature.Status) signer=$signer"
  }
  $file = Get-Item -LiteralPath $source
  return [ordered]@{
    name = $Installer.name
    relative_path = $Installer.relative_path.Replace('\', '/')
    bytes = $file.Length
    sha256 = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
    signer = $signer
    file_version = $file.VersionInfo.FileVersion
  }
}

if (-not (Test-Path -LiteralPath (Join-Path $DmlSource 'pyproject.toml') -PathType Leaf)) {
  throw "Daystrom source is missing: $DmlSource"
}
if (-not (Test-Path -LiteralPath (Join-Path $ComfyRoot 'main.py') -PathType Leaf)) {
  throw "ComfyUI source is missing: $ComfyRoot"
}
foreach ($model in $ComfyModels) {
  $source = Join-Path (Join-Path $ComfyRoot 'models') $model.relative_path
  if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
    throw "Required ComfyUI model is missing: $source"
  }
  $file = Get-Item -LiteralPath $source
  if ($file.Length -ne $model.bytes) {
    throw "ComfyUI model size mismatch: $source"
  }
  $hash = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($hash -ne $model.sha256) {
    throw "ComfyUI model SHA-256 mismatch: $source"
  }
}
$rhinoHeroSource = Join-Path $RepoRoot $RhinoHero.relative_path
if (-not (Test-Path -LiteralPath $rhinoHeroSource -PathType Leaf)) {
  throw "Required Rhino HERO model is missing: $rhinoHeroSource"
}
$rhinoHeroFile = Get-Item -LiteralPath $rhinoHeroSource
$rhinoHeroHash = (Get-FileHash -LiteralPath $rhinoHeroSource -Algorithm SHA256).Hash.ToLowerInvariant()
if ($rhinoHeroFile.Length -ne $RhinoHero.bytes -or $rhinoHeroHash -ne $RhinoHero.sha256) {
  throw "Rhino HERO model integrity mismatch: $rhinoHeroSource"
}
$ApplicationInstallerMetadata = @(
  $ApplicationInstallers | ForEach-Object { Get-VerifiedInstallerMetadata $_ }
)
if (Test-Path -LiteralPath $Destination) {
  throw "Destination already exists. Choose a new empty directory: $Destination"
}
$destinationDrive = [IO.DriveInfo]::new([IO.Path]::GetPathRoot($Destination))
$modelBytes = [long](($ComfyModels | ForEach-Object { $_.bytes } | Measure-Object -Sum).Sum)
$applicationInstallerBytes = [long]((
  $ApplicationInstallerMetadata | ForEach-Object { $_.bytes } | Measure-Object -Sum
).Sum)
$requiredBundleBytes = $modelBytes + $applicationInstallerBytes + 2GB
if ($destinationDrive.AvailableFreeSpace -lt $requiredBundleBytes) {
  throw ("The destination needs at least {0:N1} GiB free; only {1:N1} GiB is available." -f
    ($requiredBundleBytes / 1GB), ($destinationDrive.AvailableFreeSpace / 1GB))
}
if (-not $PSCmdlet.ShouldProcess($Destination, 'Build the lightweight AEC RTX Summit installer')) {
  exit 0
}

New-Item -ItemType Directory -Path $Destination -Force | Out-Null
foreach ($name in @(
  'Setup-AEC-RTX-Summit.cmd',
  'Install-AEC-RTX-Summit.ps1',
  'aec-cptx-portable.yaml',
  'hermes-dml-memory.cmd',
  'Start-ComfyUI.ps1',
  'README.md'
)) {
  Copy-ManagedFile (Join-Path $TemplateRoot $name) (Join-Path $Destination $name)
}

$payload = Join-Path $Destination 'payload\aec-demo'
foreach ($name in @('Install-AEC-Demo.ps1', 'Install-AEC-Demo.cmd', 'README.md', 'SETUP.md')) {
  Copy-ManagedFile (Join-Path $RepoRoot $name) (Join-Path $payload $name)
}

Copy-FilteredTree (Join-Path $RepoRoot 'deployment\aec-cptx-profile') (Join-Path $payload 'deployment\aec-cptx-profile')
Copy-FilteredTree (Join-Path $RepoRoot 'deployment\aec-control-plane') (Join-Path $payload 'deployment\aec-control-plane')
Copy-FilteredTree (Join-Path $RepoRoot 'deployment\plugins\aec_demo_controller') (Join-Path $payload 'deployment\plugins\aec_demo_controller') @('__pycache__')
Copy-FilteredTree (Join-Path $RepoRoot 'deployment\daystrom-dml') (Join-Path $payload 'deployment\daystrom-dml')
Copy-ManagedFile (Join-Path $RepoRoot 'deployment\rtx-pro-profile\Test-RTX-Pro-Preflight.ps1') (Join-Path $payload 'deployment\rtx-pro-profile\Test-RTX-Pro-Preflight.ps1')
Copy-FilteredTree (Join-Path $RepoRoot 'scripts') (Join-Path $payload 'scripts') @('__pycache__')
Copy-FilteredTree (Join-Path $RepoRoot 'knowledge') (Join-Path $payload 'knowledge') @('__pycache__')
Copy-FilteredTree (Join-Path $RepoRoot 'hermes') (Join-Path $payload 'hermes')
Copy-FilteredTree (Join-Path $RepoRoot 'skills') (Join-Path $payload 'skills') @('__pycache__')
Copy-FilteredTree (Join-Path $RepoRoot 'system_prompts') (Join-Path $payload 'system_prompts')
Copy-FilteredTree (Join-Path $RepoRoot 'demos\cliff_house') (Join-Path $payload 'demos\cliff_house') @('__pycache__', 'renders', 'video_source')
Copy-ManagedFile (Join-Path $RepoRoot 'aa_demo_versions\cliff_house_02\user_prompts\project_prompt.md') (Join-Path $payload 'aa_demo_versions\cliff_house_02\user_prompts\project_prompt.md')

$siteSource = Join-Path $RepoRoot 'aec-mission-control'
$siteTarget = Join-Path $payload 'aec-mission-control'
foreach ($name in @('package.json', 'package-lock.json', 'next.config.ts', 'tsconfig.json', 'postcss.config.mjs', 'eslint.config.mjs', 'README.md')) {
  $source = Join-Path $siteSource $name
  if (Test-Path -LiteralPath $source -PathType Leaf) {
    Copy-ManagedFile $source (Join-Path $siteTarget $name)
  }
}
foreach ($name in @('app', 'lib', 'public', 'tests', '.openai')) {
  $source = Join-Path $siteSource $name
  if (Test-Path -LiteralPath $source -PathType Container) {
    Copy-FilteredTree $source (Join-Path $siteTarget $name) @('__pycache__', '.next', 'node_modules', '.control')
  }
}

Copy-FilteredTree $DmlSource (Join-Path $Destination 'payload\daystrom-dml-source') @(
  '.git', '.venv', '.pytest_cache', '__pycache__', 'node_modules', 'stores'
)

$comfySourceTarget = Join-Path $Destination 'payload\comfyui-source'
Copy-FilteredTree $ComfyRoot $comfySourceTarget @(
  '.git', '.github', '.venv', '__pycache__', '.pytest_cache', 'alembic_db',
  'custom_nodes', 'input', 'logs', 'models', 'output', 'temp', 'tests',
  'tests-unit', 'user'
)
foreach ($model in $ComfyModels) {
  $source = Join-Path (Join-Path $ComfyRoot 'models') $model.relative_path
  $targetBase = Join-Path (Join-Path $Destination 'payload\comfyui-models') $model.relative_path
  Copy-ChunkedFile $source $targetBase
}
for ($index = 0; $index -lt $ApplicationInstallers.Count; $index++) {
  $installer = $ApplicationInstallers[$index]
  $metadata = $ApplicationInstallerMetadata[$index]
  $target = Join-Path (Join-Path $Destination 'payload\application-installers') `
    $metadata.relative_path.Replace('/', '\')
  Copy-ManagedFile $installer.source $target
}

$forbidden = @(Get-ChildItem -LiteralPath $Destination -File -Recurse -Force | Where-Object {
  $_.Extension -eq '.safetensors' -or
  $_.Extension -in @('.gguf', '.tar') -or
  $_.FullName -match '[\\/](huggingface|wsl-vllm|models--nvidia)[\\/]'
})
if ($forbidden.Count -gt 0) {
  throw "Forbidden heavyweight model/runtime payload detected: $($forbidden[0].FullName)"
}

$sourceCommit = (& git.exe -C $RepoRoot rev-parse HEAD | Select-Object -Last 1).Trim()
$manifest = [ordered]@{
  package = 'AEC_RTX_SUMMIT'
  created_at = (Get-Date).ToString('o')
  source_commit = $sourceCommit
  inference = 'NVIDIA-hosted GPT-5.6 Sol Responses API (1.05M context)'
  vision = 'NVIDIA-hosted Nemotron 3 Nano Omni Chat Completions API (262K context)'
  dml_embedding_model = 'qwen3-embedding:0.6b'
  includes_daystrom_source = $true
  includes_dml_runtime_stores = $false
  includes_comfyui = $true
  comfyui_source_commit = (& git.exe -C $ComfyRoot rev-parse HEAD | Select-Object -Last 1).Trim()
  includes_flux2_model_payload = $true
  comfyui_models = $ComfyModels
  rhino_hero = $RhinoHero
  includes_rhino_8_offline_installer = $true
  includes_blender_5_2_offline_installers = $true
  application_installers = $ApplicationInstallerMetadata
  includes_vllm = $false
  includes_unrelated_heavy_model_payloads = $false
}
$manifest | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Destination 'bundle-manifest.json') -Encoding UTF8

$checksums = foreach ($file in Get-ChildItem -LiteralPath $Destination -File -Recurse -Force | Sort-Object FullName) {
  $relative = $file.FullName.Substring($Destination.TrimEnd('\').Length).TrimStart('\').Replace('\', '/')
  if ($relative -eq 'SHA256SUMS.txt') { continue }
  '{0} *{1}' -f (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant(), $relative
}
$checksums | Set-Content -LiteralPath (Join-Path $Destination 'SHA256SUMS.txt') -Encoding ASCII

$measure = Get-ChildItem -LiteralPath $Destination -File -Recurse -Force | Measure-Object Length -Sum
Write-Host ''
Write-Host 'AEC RTX Summit bundle complete.' -ForegroundColor Green
Write-Host "Destination: $Destination"
Write-Host "Files:       $($measure.Count)"
Write-Host ("Size:        {0:N1} MiB" -f ($measure.Sum / 1MB))
Write-Host 'Models:      FLUX.2 Klein 4B FP8 + Qwen 3 4B encoder + FLUX.2 VAE'
Write-Host 'Applications: Rhino 8 core + English language pack; Blender 5.2 ARM64 + x64'
