# rhino_mcp_wrapper.ps1
# Waits for Rhino MCP server (port 3001) to be ready, then launches mcp-remote.
# Prevents the ECONNREFUSED race condition when Claude Desktop starts before
# MCPServer.exe has finished initializing inside Rhino.

$target  = "127.0.0.1"
$port    = 3001
$timeout = 60   # seconds to wait for Rhino MCP to come up
$delay   = 1    # seconds between retries

[Console]::Error.WriteLine("[rhino_mcp_wrapper] Waiting for Rhino MCP on ${target}:${port}...")

$elapsed = 0
$ready   = $false

while ($elapsed -lt $timeout) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $tcp.Connect($target, $port)
        $tcp.Close()
        $ready = $true
        break
    } catch {
        Start-Sleep -Seconds $delay
        $elapsed += $delay
    }
}

if (-not $ready) {
    Write-Error "[rhino_mcp_wrapper] Timed out after ${timeout}s waiting for port ${port}. Is Rhino running with the MCP plugin loaded?"
    exit 1
}

[Console]::Error.WriteLine("[rhino_mcp_wrapper] Port ${port} is ready (after ${elapsed}s). Launching mcp-remote...")

# Launch mcp-remote — use 127.0.0.1 explicitly to avoid IPv6 lookup
& npx -y mcp-remote "http://127.0.0.1:3001/mcp" 2>$null
