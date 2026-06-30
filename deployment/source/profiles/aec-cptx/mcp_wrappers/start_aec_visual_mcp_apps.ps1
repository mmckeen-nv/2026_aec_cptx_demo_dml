$ErrorActionPreference = 'Continue'
# Start GUI-bound MCP apps in the logged-in Console session. Must be run as user test.
# Blender: start app + addon server on 127.0.0.1:9876
Get-Process blender -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2
$blenderBat = Join-Path $env:TEMP 'aec_start_blender_mcp_it.bat'
@"
@echo off
start "" "C:\Program Files\Blender Foundation\Blender 5.1\blender.exe" --python-expr "import bpy; bpy.ops.blendermcp.start_server()"
"@ | Set-Content -Path $blenderBat -Encoding ASCII
schtasks /Delete /TN AEC_Blender_Interactive_MCP /F 2>$null | Out-Null
$st=(Get-Date).AddMinutes(1).ToString('HH:mm')
schtasks /Create /TN AEC_Blender_Interactive_MCP /SC ONCE /ST $st /TR "`"$blenderBat`"" /RU test /IT /F | Out-Null
schtasks /Run /TN AEC_Blender_Interactive_MCP | Out-Null

# Rhino: start hidden MCPSpawn listener on port 10500; router will adopt via listener announcement.
Get-Process Rhino -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 3
Remove-Item (Join-Path $env:LOCALAPPDATA 'McNeel\rhino-mcp\listeners\*.json') -ErrorAction SilentlyContinue
Remove-Item (Join-Path $env:LOCALAPPDATA 'McNeel\rhino-mcp\listeners\*.gone') -ErrorAction SilentlyContinue
$rhinoBat = Join-Path $env:TEMP 'aec_start_rhino_mcpspawn_10500_it.bat'
@"
@echo off
set RHINO_MCP_AUTOSTART_PORT=10500
"C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript="_MCPSpawn"
"@ | Set-Content -Path $rhinoBat -Encoding ASCII
schtasks /Delete /TN AEC_Rhino_MCPSpawn_Single /F 2>$null | Out-Null
$st=(Get-Date).AddMinutes(1).ToString('HH:mm')
schtasks /Create /TN AEC_Rhino_MCPSpawn_Single /SC ONCE /ST $st /TR "`"$rhinoBat`"" /RU test /IT /F | Out-Null
schtasks /Run /TN AEC_Rhino_MCPSpawn_Single | Out-Null

Start-Sleep 40
Write-Host '--- visual MCP app readiness ---'
tasklist /v /fi "imagename eq blender.exe"
tasklist /v /fi "imagename eq Rhino.exe"
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 9876,10500,4455 } | Sort-Object LocalPort | Format-Table -AutoSize
Get-ChildItem (Join-Path $env:LOCALAPPDATA 'McNeel\rhino-mcp\listeners') -ErrorAction SilentlyContinue | Select FullName,Length,LastWriteTime | Format-Table -AutoSize
