[CmdletBinding()]
param(
  [switch]$StartServices,
  [switch]$SkipComfyUI,
  [int]$WaitSeconds = 30
)

$ErrorActionPreference = 'Stop'
$hermesHome = Join-Path $env:LOCALAPPDATA 'hermes'
$profileRoot = Join-Path $hermesHome 'profiles\rtx_pro'
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
Add-Result 'RTX Pro profile config' ($configText.Length -gt 0) $profileConfig

foreach ($name in @('rhino', 'blender', 'daystrom_dml', 'cma')) {
  $registered = $configText -match "(?m)^  $([regex]::Escape($name)):\s*$"
  Add-Result "MCP registration: $name" $registered $(if ($registered) { 'configured in rtx_pro' } else { 'missing from rtx_pro config.yaml' })
}

$policyChecks = @{
  'DML retrieval policy' = '(?m)^\s+retrieval_policy:\s*always\s*$'
  'DML active-read DCN' = '(?m)^\s+mode:\s*active_read\s*$'
  'DML synchronized turns' = '(?m)^\s+sync_turns:\s*true\s*$'
  'DML VP project identity' = '(?m)^\s+project_id:\s*project:vp-studio-01\s*$'
  'DML VP-isolated store' = '(?m)^\s+storage_dir:\s*.*stores/vp-studio-01-runtime-store\s*$'
  'DML VP-isolated MCP launcher' = '(?m)^\s+-\s+.*dml_mcp_server_vp_studio\.cmd\s*$'
  'CMA VP-isolated MCP launcher' = '(?m)^\s+-\s+.*cma_mcp_server_vp_studio\.cmd\s*$'
}
foreach ($entry in $policyChecks.GetEnumerator()) {
  $ok = $configText -match $entry.Value
  Add-Result $entry.Key $ok $(if ($ok) { 'configured' } else { 'required agentic-memory setting is absent' })
}

Add-Result 'Local chat model API' (Test-HttpEndpoint 'http://127.0.0.1:8000/v1/models') 'http://127.0.0.1:8000/v1/models'
Add-Result 'Local vision model API' (Test-HttpEndpoint 'http://127.0.0.1:8001/v1/models') 'http://127.0.0.1:8001/v1/models'

$rhinoRouter = 'C:\Users\test\AppData\Roaming\McNeel\Rhinoceros\packages\8.0\Rhino-MCP-Platform\0.1.5\router\win-x64\rhino-mcp-router.exe'
$rhinoExe = 'C:\Program Files\Rhino 8\System\Rhino.exe'
Add-Result 'Rhino MCP router executable' (Test-Path -LiteralPath $rhinoRouter -PathType Leaf) $rhinoRouter
Add-Result 'Rhino 8 executable' (Test-Path -LiteralPath $rhinoExe -PathType Leaf) $rhinoExe
Add-Result 'Rhino MCP direct-router config' ($configText -match '(?ms)^  rhino:\s+command:\s+.*rhino-mcp-router\.exe\s+args:\s+-\s+--default-version\s+-\s+[\x27\x22]?8') 'rtx_pro launches the official McNeel router directly'
$rhinoMcpPort = 10500
if ($StartServices -and -not (Test-TcpPort $rhinoMcpPort) -and (Test-Path -LiteralPath $rhinoExe)) {
  $priorAutostartPort = $env:RHINO_MCP_AUTOSTART_PORT
  try {
    $env:RHINO_MCP_AUTOSTART_PORT = [string]$rhinoMcpPort
    Start-Process -FilePath $rhinoExe -ArgumentList '/nosplash', '/runscript="_MCPSpawn"'
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
$dmlServer = Join-Path $dmlRoot 'bin\dml_mcp_server_vp_studio.cmd'
$cmaServer = Join-Path $dmlRoot 'bin\cma_mcp_server_vp_studio.cmd'
$dmlConfig = Join-Path $dmlRoot 'config\aec-cptx-portable.yaml'
$dmlStore = Join-Path $dmlRoot 'stores\vp-studio-01-runtime-store'
$cmaStore = Join-Path $dmlRoot 'stores\cma-vp-studio-01'
foreach ($item in @($dmlPython, $dmlServer, $cmaServer, $dmlConfig, $dmlStore, $cmaStore)) {
  Add-Result "DML asset: $(Split-Path -Leaf $item)" (Test-Path -LiteralPath $item) $item
}
if (Test-Path -LiteralPath $dmlPython) {
  & $dmlPython -c "import dml_mcp.dml_mcp_server; import cma.mcp_server" 2>$null
  Add-Result 'DML/CMA Python imports' ($LASTEXITCODE -eq 0) 'dml_mcp and cma server modules import in the managed DML venv'
} else {
  Add-Result 'DML/CMA Python imports' $false 'managed DML Python is missing'
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
Write-Host 'RTX Pro virtual-production preflight'
Write-Host '===================================='
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

Write-Host 'Required RTX Pro MCP and DML checks passed.' -ForegroundColor Green
exit 0
