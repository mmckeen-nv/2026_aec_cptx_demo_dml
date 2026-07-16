$ErrorActionPreference = 'Stop'
$env:HERMES_HOME = Join-Path $env:LOCALAPPDATA 'hermes'
$env:HERMES_PROFILE = 'cliff_hero'
$dmlSource = Join-Path $env:HERMES_HOME 'integrations\daystrom-dml\source'
if (Test-Path (Join-Path $dmlSource 'pyproject.toml')) { $env:DML_SOURCE_DIR = $dmlSource }
$hermesScripts = Join-Path $env:HERMES_HOME 'hermes-agent\venv\Scripts'
$env:Path = $hermesScripts + ';' + (Join-Path $env:HERMES_HOME 'bin') + ';' + $env:Path

function Resolve-AecDemoRoot {
  $candidates = @($env:AEC_DEMO_ROOT, [Environment]::GetEnvironmentVariable('AEC_DEMO_ROOT','User'),
    [Environment]::GetEnvironmentVariable('AEC_DEMO_ROOT','Machine'), (Join-Path $PSScriptRoot '..\..'),
    (Join-Path $HOME '2026_aec_cptx_demo_dml'), 'G:\AEC-CPTX')
  foreach($candidate in $candidates){
    if(-not $candidate){continue}
    try{$resolved=(Resolve-Path -LiteralPath $candidate -ErrorAction Stop).Path}catch{continue}
    if(Test-Path -LiteralPath (Join-Path $resolved 'demos\cliff_house\hero\cliff_house_02_HERO.blend')){return $resolved}
  }
  throw 'AEC demo root with Cliff HERO scene not found.'
}

$projectRoot=Resolve-AecDemoRoot
$env:AEC_DEMO_ROOT=$projectRoot
$env:AEC_DEMO_ID='cliff-house-hero-01'
$env:AEC_DEMO_RUN_ID='cliff-hero-' + (Get-Date -Format 'yyyyMMdd-HHmmss')

function Test-Http($uri){try{$r=Invoke-WebRequest -Uri $uri -TimeoutSec 3 -UseBasicParsing;return $r.StatusCode -ge 200 -and $r.StatusCode -lt 300}catch{return $false}}
if(-not (Test-Http 'http://127.0.0.1:8000/v1/models') -or -not (Test-Http 'http://127.0.0.1:8001/v1/models')){
  $start=Join-Path $projectRoot 'deployment\wsl-vllm\start_vllm.bat'
  if(-not (Test-Path $start)){throw "vLLM launcher not found: $start"}
  & $start --no-pause
  if($LASTEXITCODE -ne 0){throw "Unable to start local models (exit $LASTEXITCODE)."}
}

$preflight=Join-Path $env:HERMES_HOME 'bin\Test-RTX-Pro-Preflight.ps1'
if(-not (Test-Path $preflight)){$preflight=Join-Path $projectRoot 'deployment\rtx-pro-profile\Test-RTX-Pro-Preflight.ps1'}
& $preflight -StartServices -ProfileName 'cliff_hero' -ProjectId 'cliff-house-hero-01' `
  -DmlStoreName 'cliff-house-hero-runtime-store' -CmaStoreName 'cma-cliff-house-hero-01' `
  -DmlLauncherName 'dml_mcp_server_cliff_hero.cmd' -CmaLauncherName 'cma_mcp_server_cliff_hero.cmd' `
  -DisplayName 'Cliff House HERO quick render'
if($LASTEXITCODE -ne 0){throw "Cliff HERO preflight failed (exit $LASTEXITCODE)."}

$demoRoot=Join-Path $projectRoot 'demos\cliff_house\hero'
Set-Location $demoRoot
Write-Host ''
Write-Host '============================================================'
Write-Host ' Cliff House HERO - Blender to ComfyUI Quick Lane'
Write-Host ' Profile: cliff_hero (independent session/logs/DML)'
Write-Host ' Source: cliff_house_02_HERO.blend (verified, read-only input)'
Write-Host ' Note: only one Hermes session may mutate Blender port 9876 at a time.'
Write-Host '============================================================'
$hermesExe=Join-Path $hermesScripts 'hermes.exe'
if(-not (Test-Path $hermesExe)){throw "Hermes not found: $hermesExe"}
& $hermesExe -p cliff_hero chat
$code=$LASTEXITCODE
Write-Host "Hermes exited with code $code. Press Enter to close."
Read-Host | Out-Null
exit $code
