# obs_mcp_wrapper.ps1
# Wraps obs-mcp with auto-restart so the agent never loses the MCP connection.
# Configure OBS_WEBSOCKET_PASSWORD in the user environment.
# If obs-mcp exits for any reason, this wrapper restarts it after a short delay.

$obsCmd = Get-Command obs-mcp -ErrorAction SilentlyContinue
if (-not $obsCmd) {
    throw "obs-mcp is not on PATH. Install it, then rerun this wrapper."
}

while ($true) {
    try {
        & $obsCmd.Source
    } catch {
        # process exited with error — fall through to restart
    }
    Start-Sleep -Seconds 2   # brief pause before restart
}
