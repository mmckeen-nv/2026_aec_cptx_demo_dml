$ErrorActionPreference='Stop'
$hermesHome = Join-Path $env:LOCALAPPDATA 'hermes'
$dmlSource = Join-Path $hermesHome 'integrations\daystrom-dml\source'
if (Test-Path (Join-Path $dmlSource 'pyproject.toml')) { $env:DML_SOURCE_DIR = $dmlSource }
$hermesScripts = Join-Path $hermesHome 'hermes-agent\venv\Scripts'
$env:Path = $hermesScripts + ';' + (Join-Path $hermesHome 'bin') + ';' + $env:Path
# Launch only the Rhino side of the AEC demo. Blender/OBS are deliberately omitted for DML-efficient phase scoping.
Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(hermes|Rhino|rhino-mcp-router)\.exe$' -or $_.CommandLine -match 'aec-cptx|rhino-mcp-router|_MCPSpawn' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2
$rhino='C:\Program Files\Rhino 8\System\Rhino.exe'
if(Test-Path $rhino){ Start-Process -FilePath $rhino -ArgumentList '/nosplash','/runscript="_MCPSpawn"' }
Start-Sleep -Seconds 18
if (-not $env:AEC_DEMO_ROOT) { throw 'Set AEC_DEMO_ROOT to the local repository path.' }
Set-Location $env:AEC_DEMO_ROOT
Write-Host 'Starting fresh aec-cptx Hermes session: Opus executor + Daystrom DML continuity + Rhino-only MCP.'
$hermesExe = Join-Path $hermesScripts 'hermes.exe'
if (-not (Test-Path $hermesExe)) { throw "Hermes not found at $hermesExe" }
& $hermesExe -p aec-cptx chat
