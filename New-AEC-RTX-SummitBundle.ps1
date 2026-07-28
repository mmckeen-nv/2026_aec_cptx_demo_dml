#requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [Parameter(Mandatory = $true)]
  [string]$Destination,
  [string]$HermesHome = (Join-Path $env:LOCALAPPDATA 'hermes')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$RepoRoot = $PSScriptRoot
$TemplateRoot = Join-Path $RepoRoot 'deployment\AEC_RTX_SUMMIT'
$DmlSource = Join-Path $HermesHome 'integrations\daystrom-dml\source'
$Destination = [IO.Path]::GetFullPath($Destination)

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

if (-not (Test-Path -LiteralPath (Join-Path $DmlSource 'pyproject.toml') -PathType Leaf)) {
  throw "Daystrom source is missing: $DmlSource"
}
if (Test-Path -LiteralPath $Destination) {
  throw "Destination already exists. Choose a new empty directory: $Destination"
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

$forbidden = @(Get-ChildItem -LiteralPath $Destination -File -Recurse -Force | Where-Object {
  $_.Extension -in @('.safetensors', '.gguf', '.tar') -or
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
  inference = 'NVIDIA-hosted Claude Opus 4.5 Chat Completions API (200K context)'
  vision = 'NVIDIA-hosted Nemotron 3 Nano Omni Chat Completions API (262K context)'
  dml_embedding_model = 'qwen3-embedding:0.6b'
  includes_daystrom_source = $true
  includes_dml_runtime_stores = $false
  includes_vllm = $false
  includes_heavy_model_payloads = $false
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
Write-Host 'Heavy models: none'
