$ErrorActionPreference = "Stop"
$env:OBS_WEBSOCKET_PASSWORD = "bigfish"
$obsCmd = "C:\Users\test\AppData\Roaming\npm\obs-mcp.cmd"
& $obsCmd
