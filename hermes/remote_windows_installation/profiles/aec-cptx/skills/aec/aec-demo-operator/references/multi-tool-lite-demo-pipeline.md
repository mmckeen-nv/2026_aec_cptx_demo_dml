# Multi-Tool Lite Demo Pipeline (Rhino + Maya + Unreal Engine)

## Overview

Lite demos use a shorter 4-phase pipeline with multiple DCC tools connected via MCP.
The first lite demo is `teapot_build`: Rhino (model) → Maya (texture) → Unreal Engine (render).

## MCP Server Configuration

All three MCP servers are configured in Hermes config.yaml under `mcp_servers`:

### Rhino MCP (existing)
- Router process, TCP port 3001 (or 10500 via autostart)
- Spawn via schtasks/PowerShell with `RHINO_MCP_AUTOSTART_PORT=10500` and `/runscript="_MCPSpawn"`
- Slot appears as adopted (e.g. "aardvark") after ~30s

### Maya MCP (PatrickPalmer/MayaMCP)
- Uses Maya's built-in Command Port — NO plugin needed inside Maya
- stdio transport (MCP client → server) → TCP socket (server → Maya Command Port :50007)
- Repo: C:\Users\test\Documents\MayaMCP, venv with `pip install mcp`
- Config: `maya: command: ...\.venv\Scripts\python.exe, args: [...\src\maya_mcp_server.py]`

**Maya Command Port usage from Python:**
```python
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
s.connect(('127.0.0.1', 50007))
s.send(mel_command.encode('utf-8') + b'\x00')  # null-terminated
s.close()
```

**Maya security popup:** First MCP connection triggers a security dialog in Maya.
User must click "Allow All". If port refuses connections after that, re-enable:
```python
import maya.cmds as cmds
cmds.commandPort(name=':50007', close=True)
cmds.commandPort(name=':50007')
```

### Unreal Engine MCP (chongdashu/unreal-mcp)
- C++ plugin (UnrealMCP) inside UE, TCP port 55557
- Python MCP server bridges stdio → TCP :55557
- Repo: C:\Users\test\Documents\unreal-mcp, venv with `pip install -e .`
- Config: `unreal: command: ...\.venv\Scripts\python.exe, args: [...\unreal_mcp_server.py]`

**UE TCP protocol (JSON over TCP):**
```python
import socket, json
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
s.connect(('127.0.0.1', 55557))
s.sendall(json.dumps({"type": "command_name", "params": {...}}).encode('utf-8'))
data = b""
try:
    while True:
        chunk = s.recv(4096)
        if not chunk: break
        data += chunk
        if len(data) > 5000: break
except: pass
s.close()
response = json.loads(data.decode('utf-8','replace'))
```

**Supported actor types:** StaticMeshActor, PointLight, SpotLight, DirectionalLight, CameraActor
(spawn_actor, delete_actor, set_actor_transform, get_actor_properties, take_screenshot)

## UE Python Script Execution (no direct MCP tool)

When the MCP plugin doesn't expose a needed operation (FBX import, mesh assignment, lighting setup),
execute Python scripts inside UE via the console:

1. Write Python script to `MCPGameProject/Content/Python/scriptname.py`
2. Copy to `Engine/Binaries/Win64/scriptname.py` (so `py scriptname.py` resolves)
3. Use PowerShell WScript.Shell to focus UE and send console commands:

```powershell
# Focus UE window
$wsh = New-Object -ComObject WScript.Shell
$wsh.SendKeys([char]0xC0)        # backtick key opens console (NOT tilde)
Start-Sleep -Milliseconds 500
$wsh.SendKeys('py scriptname.py{ENTER}')
```

**Key UE 5.8 Python API notes:**
- `unreal.FbxImportOptions()` does NOT exist — omit it, let UE use defaults
- `unreal.EditorLevelLibrary.get_editor_world()` is deprecated — use `unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()`
- `set_actor_location()` requires 3 args: `(location, sweep, teleport)` — use `actor.set_actor_location(loc, False, False)`
- `light_color` property expects `unreal.Color` not `unreal.LinearColor`
- `fog_component` property name is `component` on ExponentialHeightFog

## Project Registration Checklist

When creating a new demo project, register it in ALL of these locations:

1. **`tools/active_project.json`** — add entry to `available_projects` with title, description, audience, status
2. **`README.md`** — add row to project table, update "To start a demo" and "Or just say" lines
3. **`system_prompts/00_session_startup.md`** — update project reference list
4. **`skills/aec/aec-demo-operator/SKILL.md`** — add row to multi-project selector table

## Pipeline Flow (Lite Demo)

```
Phase 0: Pre-flight — install/verify tools, configure MCP servers
Phase 1: Rhino — model geometry, export OBJ
Phase 2: Maya — import OBJ, apply materials, set up lighting, export FBX
Phase 3: Unreal — import mesh (FBX or OBJ), set up scene, lighting, render
Endgame: User-directed (open-ended)
```

## Cross-Tool File Transfer

- Rhino → Maya: OBJ export (write mesh manually from run_python for reliability)
- Maya → UE: FBX export (Maya `file -f -exportAll -type "FBX export"`)
- Rhino → UE (direct): OBJ import via UE Python script (skip Maya entirely if needed)

**Note:** UE's Interchange framework imports OBJ/FBX but may require user approval
for the import dialog. The agent should tell the user "approve the import dialog"
and wait for confirmation.
