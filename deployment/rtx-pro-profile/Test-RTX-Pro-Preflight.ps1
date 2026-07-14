[CmdletBinding()]
param(
  [switch]$StartServices,
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

foreach ($name in @('rhino', 'blender', 'daystrom_dml', 'cma')) {
  $registered = $configText -match "(?m)^  $([regex]::Escape($name)):\s*$"
  Add-Result "MCP registration: $name" $registered $(if ($registered) { "configured in $ProfileName" } else { "missing from $ProfileName config.yaml" })
}

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

$rhinoRouter = Get-ChildItem (Join-Path $env:APPDATA 'McNeel\Rhinoceros\packages\8.0\Rhino-MCP-Platform') `
  -Filter rhino-mcp-router.exe -File -Recurse -ErrorAction SilentlyContinue |
  Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
$rhinoExe = 'C:\Program Files\Rhino 8\System\Rhino.exe'
Add-Result 'Rhino MCP router executable' ([bool]$rhinoRouter -and (Test-Path -LiteralPath $rhinoRouter -PathType Leaf)) $(if ($rhinoRouter) { $rhinoRouter } else { 'official McNeel Rhino MCP router was not found' })
Add-Result 'Rhino 8 executable' (Test-Path -LiteralPath $rhinoExe -PathType Leaf) $rhinoExe
if ($RhinoTemplatePath) {
  Add-Result 'Rhino starting template' (Test-Path -LiteralPath $RhinoTemplatePath -PathType Leaf) $RhinoTemplatePath
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
if (Test-Path -LiteralPath $dmlPython) {
  & $dmlPython -c "import dml_mcp.dml_mcp_server; import cma.mcp_server" 2>$null
  Add-Result 'DML/CMA Python imports' ($LASTEXITCODE -eq 0) 'dml_mcp and cma server modules import in the managed DML venv'
} else {
  Add-Result 'DML/CMA Python imports' $false 'managed DML Python is missing'
}

$hermesPython = Join-Path $hermesHome 'hermes-agent\venv\Scripts\python.exe'
$profilePlugin = Join-Path $profileRoot 'plugins\daystrom_dml\__init__.py'
Add-Result 'Daystrom profile memory plugin' (Test-Path -LiteralPath $profilePlugin -PathType Leaf) $profilePlugin
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
if (-not $SkipComfyUI -and $StartServices -and -not (Test-TcpPort 8188) -and (Test-Path $comfyPython) -and (Test-Path $comfyMain)) {
  Start-Process -FilePath $comfyPython -ArgumentList @($comfyMain, '--listen', '127.0.0.1', '--port', '8188', '--enable-manager') -WorkingDirectory $comfyRoot -WindowStyle Hidden
}
if (-not $SkipComfyUI) {
  $comfyReady = if ($StartServices) { Wait-TcpPort 8188 } else { Test-TcpPort 8188 }
  Add-Result 'ComfyUI REST service' $comfyReady $(if ($comfyReady) { '127.0.0.1:8188 is accepting connections' } else { 'installed but not running; use -StartServices when the stylization phase is needed' }) $false
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
