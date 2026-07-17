[CmdletBinding()]
param(
  [switch]$StartServices,
  [switch]$SkipRhino,
  [switch]$SkipComfyUI,
  [int]$WaitSeconds = 30,
  [string]$ProfileName = 'rtx_pro',
  [string]$ProjectId = 'vp-studio-01',
  [string]$DmlStoreName = 'vp-studio-01-runtime-store',
  [string]$CmaStoreName = 'cma-vp-studio-01',
  [string]$DmlLauncherName = 'dml_mcp_server_vp_studio.cmd',
  [string]$CmaLauncherName = 'cma_mcp_server_vp_studio.cmd',
  [string]$DisplayName = 'RTX Pro virtual-production',
  [string]$RhinoTemplatePath = ''
)

$ErrorActionPreference = 'Stop'
$hermesHome = Join-Path $env:LOCALAPPDATA 'hermes'
$profileRoot = Join-Path $hermesHome ("profiles\" + $ProfileName)
$profileConfig = Join-Path $profileRoot 'config.yaml'
$results = [System.Collections.Generic.List[object]]::new()

function Add-Result {
  param([string]$Name, [bool]$Passed, [string]$Detail, [bool]$Required = $true)
  $results.Add([pscustomobject]@{ Check = $Name; Passed = $Passed; Required = $Required; Detail = $Detail })
}

function Test-TcpPort {
  param([int]$Port)
  try {
    $client = [Net.Sockets.TcpClient]::new()
    $task = $client.ConnectAsync('127.0.0.1', $Port)
    if (-not $task.Wait(1500)) { $client.Dispose(); return $false }
    $ok = $client.Connected
    $client.Dispose()
    return $ok
  } catch { return $false }
}

function Wait-TcpPort {
  param([int]$Port)
  $deadline = (Get-Date).AddSeconds($WaitSeconds)
  do {
    if (Test-TcpPort $Port) { return $true }
    Start-Sleep -Milliseconds 750
  } while ((Get-Date) -lt $deadline)
  return $false
}

function Test-HttpEndpoint {
  param([string]$Uri)
  try {
    $response = Invoke-WebRequest -Uri $Uri -TimeoutSec 3 -UseBasicParsing
    return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300)
  } catch { return $false }
}

$configText = if (Test-Path -LiteralPath $profileConfig) { Get-Content -LiteralPath $profileConfig -Raw } else { '' }
Add-Result "$DisplayName profile config" ($configText.Length -gt 0) $profileConfig

$requiredMcps = if ($SkipRhino) { @('blender', 'daystrom_dml', 'cma') } else { @('rhino', 'blender', 'daystrom_dml', 'cma') }
foreach ($name in $requiredMcps) {
  $registered = $configText -match "(?m)^  $([regex]::Escape($name)):\s*$"
  Add-Result "MCP registration: $name" $registered $(if ($registered) { "configured in $ProfileName" } else { "missing from $ProfileName config.yaml" })
}
if ($SkipRhino) {
  $rhinoAbsent = $configText -notmatch '(?m)^  rhino:\s*$'
  Add-Result 'Rhino MCP absent for Blender-only profile' $rhinoAbsent $(if ($rhinoAbsent) { 'no Rhino MCP will be launched' } else { 'remove inherited Rhino MCP registration from this Blender-only profile' })
}
$serializedMcpArgs = $configText -match '(?m)^\s+args:\s+[''\"]\['
Add-Result 'MCP arguments use YAML lists' (-not $serializedMcpArgs) $(if ($serializedMcpArgs) { 'one or more MCP args values are serialized JSON strings; rerun installer repair before Hermes' } else { 'MCP args are typed lists' })
$blenderConfigMatch = [regex]::Match($configText, '(?ms)^  blender:\s*\r?\n(?<body>.*?)(?=^  \S|\z)')
$blenderConfigBody = if ($blenderConfigMatch.Success) { $blenderConfigMatch.Groups['body'].Value } else { '' }
$blenderStringEnv = ($blenderConfigBody -match '(?m)^\s+BLENDER_PORT:\s*[''\"]9876[''\"]\s*$') -and
  ($blenderConfigBody -match '(?m)^\s+DISABLE_TELEMETRY:\s*[''\"]true[''\"]\s*$')
Add-Result 'Blender MCP environment values are strings' $blenderStringEnv $(if ($blenderStringEnv) { 'BLENDER_PORT and DISABLE_TELEMETRY are quoted strings' } else { 'quote Blender MCP env values; YAML int/bool values are rejected by Hermes' })
$backgroundReviewDisabled = ($configText -match '(?m)^  nudge_interval:\s*0\s*$') -and
  ($configText -match '(?m)^  creation_nudge_interval:\s*0\s*$')
Add-Result 'Demo background review forks disabled' $backgroundReviewDisabled $(if ($backgroundReviewDisabled) { 'Daystrom synchronized turns remain active without post-turn skill-review forks' } else { 'set memory.nudge_interval and skills.creation_nudge_interval to 0 for demo reliability' })
$obsAbsent = $configText -notmatch '(?m)^  obs:\s*$'
Add-Result 'Stale OBS MCP absent' $obsAbsent $(if ($obsAbsent) { 'no inherited PowerShell stdio noise' } else { 'remove the stale WSL OBS MCP block from RTX Pro' })

$policyChecks = @{
  'DML retrieval policy' = '(?m)^\s+retrieval_policy:\s*always\s*$'
  'DML strict provider preflight' = '(?m)^\s+preflight_strict:\s*true\s*$'
  'DML active-read DCN' = '(?m)^\s+mode:\s*active_read\s*$'
  'DML synchronized turns' = '(?m)^\s+sync_turns:\s*true\s*$'
  'DML project identity' = "(?m)^\s+project_id:\s*project:$([regex]::Escape($ProjectId))\s*$"
  'DML isolated store' = "(?m)^\s+storage_dir:\s*.*stores/$([regex]::Escape($DmlStoreName))\s*$"
  'DML isolated MCP launcher' = "(?m)^\s+-\s+.*$([regex]::Escape($DmlLauncherName))\s*$"
  'CMA isolated MCP launcher' = "(?m)^\s+-\s+.*$([regex]::Escape($CmaLauncherName))\s*$"
}
foreach ($entry in $policyChecks.GetEnumerator()) {
  $ok = $configText -match $entry.Value
  Add-Result $entry.Key $ok $(if ($ok) { 'configured' } else { 'required agentic-memory setting is absent' })
}

Add-Result 'Local chat model API' (Test-HttpEndpoint 'http://127.0.0.1:8000/v1/models') 'http://127.0.0.1:8000/v1/models'
Add-Result 'Local vision model API' (Test-HttpEndpoint 'http://127.0.0.1:8001/v1/models') 'http://127.0.0.1:8001/v1/models'

if (-not $SkipRhino) {
$rhinoRouter = Get-ChildItem (Join-Path $env:APPDATA 'McNeel\Rhinoceros\packages\8.0\Rhino-MCP-Platform') `
  -Filter rhino-mcp-router.exe -File -Recurse -ErrorAction SilentlyContinue |
  Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
$rhinoExe = 'C:\Program Files\Rhino 8\System\Rhino.exe'
Add-Result 'Rhino MCP router executable' ([bool]$rhinoRouter -and (Test-Path -LiteralPath $rhinoRouter -PathType Leaf)) $(if ($rhinoRouter) { $rhinoRouter } else { 'official McNeel Rhino MCP router was not found' })
Add-Result 'Rhino 8 executable' (Test-Path -LiteralPath $rhinoExe -PathType Leaf) $rhinoExe
if ($RhinoTemplatePath) {
  Add-Result 'Rhino starting template' (Test-Path -LiteralPath $RhinoTemplatePath -PathType Leaf) $RhinoTemplatePath
  $templateHashPath = $RhinoTemplatePath + '.sha256'
  $templateHashOk = $false
  $templateHashDetail = "missing integrity file: $templateHashPath"
  if ((Test-Path -LiteralPath $RhinoTemplatePath -PathType Leaf) -and (Test-Path -LiteralPath $templateHashPath -PathType Leaf)) {
    $expectedHash = ((Get-Content -LiteralPath $templateHashPath -Raw).Trim() -split '\s+')[0].ToLowerInvariant()
    $actualHash = (Get-FileHash -LiteralPath $RhinoTemplatePath -Algorithm SHA256).Hash.ToLowerInvariant()
    $templateHashOk = ($expectedHash -match '^[0-9a-f]{64}$') -and ($actualHash -eq $expectedHash)
    $templateHashDetail = if ($templateHashOk) { 'basic guide-only template matches repository SHA-256' } else { "template changed or polluted: expected $expectedHash, actual $actualHash" }
  }
  Add-Result 'Rhino template integrity' $templateHashOk $templateHashDetail
}
$rhinoConfigMatch = [regex]::Match($configText, '(?ms)^  rhino:\s*\r?\n(?<body>.*?)(?=^  \S|\z)')
$rhinoConfigBody = if ($rhinoConfigMatch.Success) { $rhinoConfigMatch.Groups['body'].Value } else { '' }
$directRhinoConfig = ($rhinoConfigBody -match '(?m)^    command:\s+.*rhino-mcp-router\.exe\s*$') -and
  ($rhinoConfigBody -match '(?m)^\s+-\s+--default-version\s*$') -and
  ($rhinoConfigBody -match '(?m)^\s+-\s+[\x27\x22]?8[\x27\x22]?\s*$')
Add-Result 'Rhino MCP direct-router config' $directRhinoConfig "$ProfileName launches the official McNeel router directly"
$rhinoMcpPort = 10500
if ($StartServices -and -not (Test-TcpPort $rhinoMcpPort) -and (Test-Path -LiteralPath $rhinoExe)) {
  $priorAutostartPort = $env:RHINO_MCP_AUTOSTART_PORT
  try {
    $env:RHINO_MCP_AUTOSTART_PORT = [string]$rhinoMcpPort
    $rhinoArgs = @('/nosplash')
    if ($RhinoTemplatePath) { $rhinoArgs += $RhinoTemplatePath }
    $rhinoArgs += '/runscript="_MCPSpawn"'
    Start-Process -FilePath $rhinoExe -ArgumentList $rhinoArgs
  } finally {
    $env:RHINO_MCP_AUTOSTART_PORT = $priorAutostartPort
  }
}
$rhinoBridge = if ($StartServices) { Wait-TcpPort $rhinoMcpPort } else { Test-TcpPort $rhinoMcpPort }
Add-Result 'Rhino MCP application bridge' $rhinoBridge $(if ($rhinoBridge) { "127.0.0.1:$rhinoMcpPort is accepting connections; the router can adopt this slot" } else { 'Rhino is not exposing an MCP listener; rerun preflight with -StartServices' })
}

$uvx = Get-Command uvx.exe -ErrorAction SilentlyContinue
if (-not $uvx) { $uvx = Get-Command uvx -ErrorAction SilentlyContinue }
Add-Result 'uvx for Blender MCP' ($null -ne $uvx) $(if ($uvx) { $uvx.Source } else { 'uvx is not on PATH' })
$blenderExe = Get-ChildItem 'C:\Program Files\Blender Foundation' -Filter blender.exe -Recurse -ErrorAction SilentlyContinue |
  Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
Add-Result 'Blender executable' ([bool]$blenderExe) $(if ($blenderExe) { $blenderExe } else { 'Blender was not found' })
if ($StartServices -and $blenderExe -and -not (Get-Process blender -ErrorAction SilentlyContinue)) {
  Start-Process -FilePath $blenderExe
}
$blenderBridge = if ($StartServices) { Wait-TcpPort 9876 } else { Test-TcpPort 9876 }
Add-Result 'Blender MCP application bridge' $blenderBridge $(if ($blenderBridge) { '127.0.0.1:9876 is accepting connections' } else { 'enable/start the Blender MCP add-on, then rerun preflight' })

$dmlRoot = Join-Path $hermesHome 'integrations\daystrom-dml'
$dmlPython = Join-Path $dmlRoot '.venv-dml\Scripts\python.exe'
$dmlServer = Join-Path $dmlRoot ("bin\" + $DmlLauncherName)
$cmaServer = Join-Path $dmlRoot ("bin\" + $CmaLauncherName)
$dmlConfig = Join-Path $dmlRoot 'config\aec-cptx-portable.yaml'
$dmlStore = Join-Path $dmlRoot ("stores\" + $DmlStoreName)
$cmaStore = Join-Path $dmlRoot ("stores\" + $CmaStoreName)
foreach ($item in @($dmlPython, $dmlServer, $cmaServer, $dmlConfig, $dmlStore, $cmaStore)) {
  Add-Result "DML asset: $(Split-Path -Leaf $item)" (Test-Path -LiteralPath $item) $item
}
$dmlLauncherText = if (Test-Path -LiteralPath $dmlServer -PathType Leaf) { Get-Content -LiteralPath $dmlServer -Raw } else { '' }
$cmaLauncherText = if (Test-Path -LiteralPath $cmaServer -PathType Leaf) { Get-Content -LiteralPath $cmaServer -Raw } else { '' }
$dmlLauncherModern = ($dmlLauncherText -match '[.]venv-dml[\\/]Scripts[\\/]python[.]exe') -and
  ($dmlLauncherText -match '-m\s+dml_mcp[.]dml_mcp_server\b')
$cmaLauncherModern = ($cmaLauncherText -match '[.]venv-dml[\\/]Scripts[\\/]python[.]exe') -and
  ($cmaLauncherText -match '-m\s+cma[.]mcp_server\b')
Add-Result 'DML launcher uses managed runtime' $dmlLauncherModern $(if ($dmlLauncherModern) { "$DmlLauncherName uses .venv-dml and dml_mcp.dml_mcp_server" } else { "$DmlLauncherName is stale or invokes the wrong Python/module" })
Add-Result 'CMA launcher uses managed runtime' $cmaLauncherModern $(if ($cmaLauncherModern) { "$CmaLauncherName uses .venv-dml and cma.mcp_server" } else { "$CmaLauncherName is stale or invokes the wrong Python/module" })
if (Test-Path -LiteralPath $dmlPython) {
  & $dmlPython -c "import dml_mcp.dml_mcp_server; import cma.mcp_server" 2>$null
  Add-Result 'DML/CMA Python imports' ($LASTEXITCODE -eq 0) 'dml_mcp and cma server modules import in the managed DML venv'
} else {
  Add-Result 'DML/CMA Python imports' $false 'managed DML Python is missing'
}

$hermesPython = Join-Path $hermesHome 'hermes-agent\venv\Scripts\python.exe'
$profilePlugin = Join-Path $profileRoot 'plugins\daystrom_dml\__init__.py'
Add-Result 'Daystrom profile memory plugin' (Test-Path -LiteralPath $profilePlugin -PathType Leaf) $profilePlugin
$profileConfig = Join-Path $profileRoot 'config.yaml'
$controllerEnabled = (Test-Path -LiteralPath $profileConfig -PathType Leaf) -and
  ((Get-Content -LiteralPath $profileConfig -Raw) -match '(?m)^\s*-\s*aec_demo_controller\s*$')
Add-Result 'Agent-led workflow (AEC controller disabled)' (-not $controllerEnabled) $profileConfig
if (Test-Path -LiteralPath $hermesPython -PathType Leaf) {
  $priorHermesHome = $env:HERMES_HOME
  try {
    $env:HERMES_HOME = $profileRoot
    & $hermesPython -c "from plugins.memory import load_memory_provider; p=load_memory_provider('daystrom_dml'); assert p and p.is_available(); d=p.decide_iteration_extension({'user_message':'stop: repeated same error and no progress','recent_text':'looping with the same error','recent_tool_calls':2,'recent_tool_results':2}); assert d.get('decision')=='deny' and d.get('source')=='daystrom_dml' and d.get('reason_codes'); print(p.store_dir, p.dcn_mode)" 2>$null
    Add-Result 'Daystrom/DCN runtime hook' ($LASTEXITCODE -eq 0) 'named profile loads daystrom_dml and returns an explicit DCN iteration decision'
  } finally {
    $env:HERMES_HOME = $priorHermesHome
  }
} else {
  Add-Result 'Daystrom/DCN runtime hook' $false "Hermes profile Python is missing: $hermesPython"
}
Add-Result 'DML Ollama dependency' (Test-HttpEndpoint 'http://127.0.0.1:11434/api/version') 'http://127.0.0.1:11434/api/version'

$comfyRoot = Join-Path $env:USERPROFILE 'ComfyUI'
$comfyPython = Join-Path $comfyRoot '.venv\Scripts\python.exe'
$comfyMain = Join-Path $comfyRoot 'main.py'
Add-Result 'ComfyUI installation' ((Test-Path $comfyPython) -and (Test-Path $comfyMain)) $comfyRoot (-not $SkipComfyUI)
$comfyModelSpecs = @(
  @{ RelativePath = 'models\checkpoints\sd_xl_base_1.0.safetensors'; Bytes = 6938078334L },
  @{ RelativePath = 'models\controlnet\controlnet-depth-sdxl-1.0\diffusion_pytorch_model.safetensors'; Bytes = 5004167860L },
  @{ RelativePath = 'models\diffusion_models\flux-2-klein-base-4b-fp8.safetensors'; Bytes = 4089498488L },
  @{ RelativePath = 'models\text_encoders\qwen_3_4b.safetensors'; Bytes = 8044982048L },
  @{ RelativePath = 'models\vae\flux2-vae.safetensors'; Bytes = 336213556L }
)
$badComfyModels = @()
foreach ($spec in $comfyModelSpecs) {
  $modelPath = Join-Path $comfyRoot $spec.RelativePath
  if (-not (Test-Path -LiteralPath $modelPath -PathType Leaf)) {
    $badComfyModels += "missing $($spec.RelativePath)"
  } elseif ((Get-Item -LiteralPath $modelPath).Length -ne $spec.Bytes) {
    $badComfyModels += "wrong-size $($spec.RelativePath)"
  }
}
$modelRepair = 'run scripts\install_comfy_flux2_models.ps1 for FLUX files and install the approved SDXL/depth files'
Add-Result 'ComfyUI SDXL + FLUX.2 model set' ($badComfyModels.Count -eq 0) $(if ($badComfyModels.Count -eq 0) { 'all five model components have the approved byte sizes' } else { ($badComfyModels -join '; ') + "; $modelRepair" }) (-not $SkipComfyUI)
if (-not $SkipComfyUI -and $StartServices -and -not (Test-TcpPort 8188) -and (Test-Path $comfyPython) -and (Test-Path $comfyMain)) {
  Start-Process -FilePath $comfyPython -ArgumentList @($comfyMain, '--listen', '127.0.0.1', '--port', '8188', '--enable-manager') -WorkingDirectory $comfyRoot -WindowStyle Hidden
}
if (-not $SkipComfyUI) {
  $comfyReady = if ($StartServices) { Wait-TcpPort 8188 } else { Test-TcpPort 8188 }
  Add-Result 'ComfyUI REST service' $comfyReady $(if ($comfyReady) { '127.0.0.1:8188 is accepting connections' } else { 'installed but not running; use -StartServices for the required SDXL -> FLUX phase' }) $true
}

Write-Host ''
Write-Host "$DisplayName preflight"
Write-Host ('=' * ($DisplayName.Length + 10))
foreach ($result in $results) {
  $marker = if ($result.Passed) { '[PASS]' } elseif ($result.Required) { '[FAIL]' } else { '[WARN]' }
  $color = if ($result.Passed) { 'Green' } elseif ($result.Required) { 'Red' } else { 'Yellow' }
  Write-Host ("{0} {1} - {2}" -f $marker, $result.Check, $result.Detail) -ForegroundColor $color
}

$failed = @($results | Where-Object { $_.Required -and -not $_.Passed })
if ($failed.Count -gt 0) {
  Write-Error ("Preflight failed: {0} required check(s) are not ready." -f $failed.Count)
  exit 1
}

Write-Host "Required $DisplayName MCP and DML checks passed." -ForegroundColor Green
exit 0
