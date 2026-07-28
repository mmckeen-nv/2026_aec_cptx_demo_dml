# Cliff House Control Plane

Local AEC operations UI for the Cliff House workflow. It intentionally binds to
`127.0.0.1`: its controls can start Hermes and its image routes read local Rhino,
Blender, and ComfyUI artifacts, so it must not be exposed directly to a public
network.

## What is live now

- Service health for Hermes, Rhino MCP, Blender MCP, ComfyUI, and DML/Ollama.
- Phase completion derived from the real `cliff_house_single_frame_01` artifact
  contract.
- One-second live viewport capture from Rhino and Blender, with current-run
  depth/FLUX artifacts replacing their live source proxies as they complete.
- Filtered Hermes model/tool activity from the active profile log.
- One-click manual and automatic launches.
- A resident Hermes worker that pays preflight once, preserves the latest
  Hermes session ID, and accepts later automatic/manual/chat requests through a
  local queue. Each turn still uses the full `aec-cptx` profile, 120 turns, DML,
  MCP tools, and existing safety rules.

## Native-video upgrade path

The current wall is a low-latency still stream, not encoded desktop video. True
15–30 FPS viewport streaming should use one local capture bridge with Windows
Graphics Capture and WebRTC:

1. Capture only the Rhino and Blender viewport child windows by native handle.
2. Hardware-encode both streams with NVENC.
3. Publish WebRTC tracks to the local dashboard.
4. Keep artifact image routes as a reliable fallback and for full-resolution
   inspection.
5. Connect the right-side console to Hermes `serve` on loopback using its PTY
   WebSocket, so prompts, tool approvals, and streamed responses share one
   persistent Hermes session.

Do not expose the native capture bridge or Hermes control endpoint beyond
loopback without authentication and origin checks.
