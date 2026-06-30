$ErrorActionPreference = "Stop"
$target  = "127.0.0.1"
$port    = 3001
$timeout = 20
$delay   = 1
[Console]::Error.WriteLine("[rhino_mcp_wrapper] Waiting for Rhino MCP on ${target}:${port}...")
$elapsed = 0
while ($elapsed -lt $timeout) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect($target, $port)
        $tcp.Close()
        [Console]::Error.WriteLine("[rhino_mcp_wrapper] Port ${port} is ready (after ${elapsed}s). Launching mcp-remote...")
        & npx -y mcp-remote "http://127.0.0.1:3001/mcp"
        exit $LASTEXITCODE
    } catch {
        Start-Sleep -Seconds $delay
        $elapsed += $delay
    }
}
Write-Error "[rhino_mcp_wrapper] Timed out after ${timeout}s waiting for port ${port}. Is Rhino running with the MCP plugin loaded?"
exit 1
