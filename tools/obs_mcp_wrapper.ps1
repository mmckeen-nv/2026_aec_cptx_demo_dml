# obs_mcp_wrapper.ps1
# Wraps obs-mcp with auto-restart so Claude Desktop never loses the MCP connection.
# Claude Desktop calls this script as the MCP server command.
# If obs-mcp exits for any reason, this wrapper restarts it after a short delay.

$env:OBS_WEBSOCKET_PASSWORD = "bigfish"
$obsCmd = "C:\Users\swags\AppData\Roaming\npm\obs-mcp.cmd"

while ($true) {
    try {
        & $obsCmd
    } catch {
        # process exited with error — fall through to restart
    }
    Start-Sleep -Seconds 2   # brief pause before restart
}
