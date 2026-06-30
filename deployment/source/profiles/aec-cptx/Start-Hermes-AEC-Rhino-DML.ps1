$ErrorActionPreference='Continue'
$env:Path = 'C:\Users\test\AppData\Local\hermes\hermes-agent\venv\Scripts;C:\Users\test\AppData\Local\hermes\bin;C:\Users\test\.local\bin;' + [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User')
# Launch only the Rhino side of the AEC demo. Blender/OBS are deliberately omitted for DML-efficient phase scoping.
Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(hermes|Rhino|rhino-mcp-router)\.exe$' -or $_.CommandLine -match 'aec-cptx|rhino-mcp-router|_MCPSpawn' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2
$rhino='C:\Program Files\Rhino 8\System\Rhino.exe'
if(Test-Path $rhino){ Start-Process -FilePath $rhino -ArgumentList '/nosplash','/runscript="_MCPSpawn"' }
Start-Sleep -Seconds 18
Set-Location '\\wsl.localhost\Ubuntu\home\test\2026_aec_cptx_demo'
Write-Host 'Starting fresh aec-cptx Hermes session: Opus executor + Daystrom DML continuity + Rhino-only MCP.'
hermes -p aec-cptx chat
