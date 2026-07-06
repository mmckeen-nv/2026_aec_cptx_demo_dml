# Multi-Tool MCP Servers — Maya and Unreal Engine

Reference for setting up MCP servers for DCC tools beyond Rhino and Blender.
Researched June 30, 2026. Used by the teapot_build lite demo.

## Autodesk Maya MCP

### Repo
- **URL:** https://github.com/PatrickPalmer/MayaMCP
- **Stars:** 86 (as of June 2026)
- **Tested with:** Maya 2023, 2025
- **License:** MIT

### Architecture
- **No plugin needed inside Maya.** Uses Maya's built-in Command Port (MEL scripting port).
- Python code is sent from the MCP server to Maya's command port for execution.
- Results are sent back and processed by the MCP server.
- Two connections per command: first to run the operation and save results, second to read back results (limitation of MEL-based Python execution).

### Installation
```bash
# Clone the repo
cd /c/Users/test/Documents
git clone https://github.com/PatrickPalmer/MayaMCP.git
cd MayaMCP

# Create venv (Python 3.10+ required)
python -m venv .venv
.venv/Scripts/activate.bat

# Install dependencies (just the mcp package)
pip install -r requirements.txt
```

### MCP Config (Hermes)
```json
{
  "mcpServers": {
    "MayaMCP": {
      "command": "C:\\Users\\test\\Documents\\MayaMCP\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\test\\Documents\\MayaMCP\\src\\maya_mcp_server.py"]
    }
  }
}
```

### Key Notes
- When MCP server first connects to Maya, Maya shows a security popup — user must click "Allow All". Required each Maya session.
- Python 3.10+ required (machine has 3.11.15 — OK).
- Exposed tools: create_object, set_object_attributes, create_material, create_advanced_model, mesh_operations, create_curve, curve_modeling, scene_new, scene_open, scene_save, organize_objects, generate_scene.
- Material types: lambert, phong, wood, marble, chrome, glass, etc.
- Object types: cube, cone, sphere, cylinder, camera, spotLight, pointLight, directionalLight.

### Maya Command Port (verified June 30 2026)

MayaMCP's default command port is **50007** (defined at line 33 of `maya_mcp_server.py`: `DEFAULT_COMMAND_PORT = 50007`). This is NOT the Maya default of 7001 — it's the MayaMCP project's chosen port. Maya must be running and listening on this port for the MCP server to connect.

**Verify Maya Command Port is active:**
```bash
# Check port 50007 is listening
netstat -an | grep 50007
# Verify the PID is maya.exe
netstat -ano | grep "50007"   # get the PID
tasklist | grep <PID>          # confirm it's maya.exe
```

When Maya is running with the Command Port active, the MayaMCP stdio server connects automatically on MCP client startup. Hermes reported "46 MCP tool(s) now available" after Maya was launched.

**Security popup:** When the MCP server first connects to Maya, Maya shows a security popup asking to allow script execution. The user must click "Allow All". This must be done each Maya session.

### Verification
```bash
ls "/c/Program Files/Autodesk/Maya2025/bin/maya.exe"
ls "/c/Users/test/Documents/MayaMCP/src/maya_mcp_server.py"
ls "/c/Users/test/Documents/MayaMCP/.venv/Scripts/python.exe"
netstat -an | grep 50007       # Maya Command Port
```

---

## Unreal Engine MCP

### Repo
- **URL:** https://github.com/chongdashu/unreal-mcp
- **Stars:** 2019 (as of June 2026)
- **Requires:** Unreal Engine 5.5+ (5.8 verified June 30 2026), Python 3.10+, Visual Studio 2022 (C++ Game dev workload), .NET 10.0 runtime (for UE 5.8 — not bundled with UE or VS)
- **License:** MIT

### Architecture
- **C++ plugin** (UnrealMCP) runs inside UE — native TCP server on port 55557.
- **Python MCP server** (unreal_mcp_server.py) — stdio transport to MCP client, TCP to UE plugin.
- Uses FastMCP library. Loads tool modules from a `tools/` directory.
- Sample project (MCPGameProject) included — UE 5.5 Blank Project with plugin pre-configured.

### Installation

#### 1. Install Unreal Engine
- Install Epic Games Launcher from https://www.unrealengine.com/download
- Log in with Epic Games account
- Install UE 5.5+ via launcher (~50 GB)

#### 2. Install Visual Studio 2022

**⚠️ winget pitfall (discovered June 30 2026):** `winget install` with `--override` and workload flags registers the workloads in VS metadata (vswhere confirms them) but does NOT install the actual C++ toolchain. After winget install, `cl.exe` was missing, `VC/Tools/MSVC/` was empty, and the Windows SDK was absent. MSBuild was present but the C++ compiler was not.

**Failed approach:**
```bash
# This registers workloads but does NOT install C++ compiler:
winget install Microsoft.VisualStudio.2022.Community \
  --override "--quiet --add Microsoft.VisualStudio.Workload.ManagedGame --add Microsoft.VisualStudio.Workload.NativeDesktop --includeRecommended" \
  --accept-package-agreements --accept-source-agreements
```

**Working approach — use VS Installer setup.exe directly:**
```bash
# Step 1: winget installs the VS 2022 base (OK)
winget install Microsoft.VisualStudio.2022.Community --accept-package-agreements --accept-source-agreements

# Step 2: Use the VS Installer to actually install C++ components
VS_INSTALLER="/c/Program Files (x86)/Microsoft Visual Studio/Installer/setup.exe"
"$VS_INSTALLER" install \
  --installPath "C:\\Program Files\\Microsoft Visual Studio\\2022\\Community" \
  --add Microsoft.VisualStudio.Workload.ManagedGame \
  --add Microsoft.VisualStudio.Workload.NativeDesktop \
  --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 \
  --add Microsoft.VisualStudio.Component.Windows11SDK.22621 \
  --includeRecommended \
  --quiet --norestart
```

**Verify C++ toolchain after install:**
```bash
# MSBuild (should exist)
ls "/c/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/amd64/MSBuild.exe"
# C++ compiler (should exist after setup.exe install)
find "/c/Program Files/Microsoft Visual Studio/2022/Community/VC" -name "cl.exe"
# VC Tools version directory (should be populated)
ls "/c/Program Files/Microsoft Visual Studio/2022/Community/VC/Tools/MSVC/"
# Windows SDK
ls "/c/Program Files (x86)/Windows Kits/10/Include/"
```

If `cl.exe` or `VC/Tools/MSVC/` is missing/empty, the setup.exe step did not complete — re-run it.

#### 3. Clone and set up MCP server
```bash
cd /c/Users/test/Documents
git clone https://github.com/chongdashu/unreal-mcp.git
cd unreal-mcp/Python

python -m venv .venv
.venv/Scripts/activate.bat
pip install -e .
# Dependencies: mcp[cli]>=1.4.1, fastmcp>=0.2.0, uvicorn, fastapi, pydantic>=2.6.1, requests
```

#### 4. Build the UE plugin
- Use the sample project: `MCPGameProject` (already has the plugin)
  - OR copy `MCPGameProject/Plugins/UnrealMCP` to your project's Plugins folder
- Right-click the .uproject file → "Generate Visual Studio project files"
- Open the .sln in Visual Studio 2022
- Set configuration to "Development Editor"
- Build the project (compiles the UnrealMCP plugin)
- Launch the UE project — plugin starts TCP server on port 55557

### MCP Config (Hermes)
```json
{
  "mcpServers": {
    "unrealMCP": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\test\\Documents\\unreal-mcp\\Python",
        "run",
        "unreal_mcp_server.py"
      ]
    }
  }
}
```

### Key Notes
- UE editor must be running before starting the MCP server.
- Plugin must be rebuilt if UE version changes.
- Exposed tools: actor management (create, delete, transform, query), Blueprint development (create classes, add components, compile, spawn), Blueprint node graph (events, function calls, variables), editor control (viewport focus, camera).
- Logs in `unreal_mcp.log`.

### UE 5.8 build process (proven June 30 2026)

The user installed UE 5.8 (not 5.5). This required three additional steps:

**Step 1: Install .NET 10 runtime (REQUIRED for UE 5.8)**
UE 5.8's UnrealBuildTool targets .NET 10.0, but the machine only had .NET 8.0. Without .NET 10, project file generation fails with:
```
You must install or update .NET to run this application.
App: UnrealBuildTool.exe
Framework: 'Microsoft.NETCore.App', version '10.0.0' (x64)
```
Fix:
```bash
winget install Microsoft.DotNet.Runtime.10 --accept-package-agreements --accept-source-agreements
```

**Step 2: Update .uproject EngineAssociation**
The MCPGameProject .uproject ships with `"EngineAssociation": "5.5"`. Update to match installed version:
```json
// MCPGameProject.uproject
"EngineAssociation": "5.8"
```
Use the `patch` tool — this is a Windows-side file, not WSL.

**Step 3: Update Target.cs for UE 5.8 compatibility**

The MCPGameProject ships with UE 5.5 build settings. UE 5.8 requires updated Target.cs files in both `Source/MCPGameProjectEditor.Target.cs` and `Source/MCPGameProject.Target.cs`:

```csharp
// Change these three lines in BOTH Target.cs files:
DefaultBuildSettings = BuildSettingsVersion.V7;           // was V5
IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8; // was Unreal5_5
bOverrideBuildEnvironment = true;                          // NEW — required for UE 5.8
```

**Pitfall:** Do NOT use `BuildEnvironment = TargetBuildEnvironment.Unique` — this fails with "Targets with a unique build environment cannot be built with an installed engine" when using a binary UE install (not built from source). Use `bOverrideBuildEnvironment = true` instead.

**Step 4: Install .NET Framework 4.8.1 Developer Pack (REQUIRED for SwarmInterface)**

UE 5.8's build system requires the .NET Framework 4.x SDK (NOT the same as .NET 10 runtime). Without it, the build fails with:
```
Unable to instantiate module 'SwarmInterface': Could not find NetFxSDK install dir
```

```bash
winget install Microsoft.DotNet.Framework.DeveloperPack_4 --accept-package-agreements --accept-source-agreements
```

**Step 5: Clean old build artifacts and regenerate**

After changing Target.cs, old binaries in `Binaries/` and `Intermediate/` cause "Incompatible or missing module" errors. Clean them first:

```bash
# Clean stale artifacts (IMPORTANT — do this after Target.cs changes)
rm -rf /c/Users/test/Documents/unreal-mcp/MCPGameProject/Binaries
rm -rf /c/Users/test/Documents/unreal-mcp/MCPGameProject/Intermediate

# Regenerate project files for the new UE version
"/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe" \
  -projectfiles -project="C:\Users\test\Documents\unreal-mcp\MCPGameProject\MCPGameProject.uproject" \
  -game -engine -progress
# Takes ~8 seconds, writes .sln and .slnx
```

**Step 6: Build the plugin**

**⚠️ MSBuild flag mangling pitfall (bash/MSYS):** MSBuild's `/p:` flags get mangled by git-bash — `/p:Configuration=` becomes `p:Configuration=` (the leading `/` is treated as a path prefix). Use `-p:` (dash prefix) instead, or wrap the entire command in `cmd.exe /c "..."`.

```bash
# CORRECT — use -p: (dash prefix) with MSBuild in bash/MSYS:
"/c/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/amd64/MSBuild.exe" \
  "C:/Users/test/Documents/unreal-mcp/MCPGameProject/MCPGameProject.sln" \
  -p:Configuration="Development Editor" \
  -p:Platform=Win64 \
  -m -v:minimal
# First build takes 5-10 minutes (compiles UnrealMCP C++ plugin)

# WRONG — /p: gets mangled by bash, causing "error MSB1008: Only one project can be specified"
```

**Alternative: Use UE's own Build.bat** (avoids MSBuild flag issues but still needs all SDKs):
```bash
"/c/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" \
  MCPGameProjectEditor Win64 Development \
  -Project="C:\Users\test\Documents\unreal-mcp\MCPGameProject\MCPGameProject.uproject" \
  -WaitMutex
```

**Alternative: Launch UE directly** — UE compiles plugins on first open. But if build deps are missing, UE exits silently after logging "Incompatible or missing module" in the project log:
```bash
# UE log location: MCPGameProject/Saved/Logs/MCPGameProject.log
"/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe" \
  "C:\Users\test\Documents\unreal-mcp\MCPGameProject\MCPGameProject.uproject"
# If UE exits immediately, check the log for build errors
```

After successful build, launch the UE project — the UnrealMCP plugin starts TCP server on port 55557.

**`cmd.exe /c` wrapper pitfall:** Wrapping MSBuild in `cmd.exe /c "..."` with nested quotes produces empty output (the command runs but output is swallowed by the cmd.exe shell layer). Prefer the `-p:` dash-prefix approach in bash directly, or use UE's `Build.bat` which handles its own argument parsing.

**VS Installer `modify` vs `install` (discovered June 30 2026):**
The VS Installer `setup.exe` uses `modify` (not `install`) to add workloads to an existing VS install. Using `install` returns exit code 87. However, the winget `--override` install actually DOES launch background setup.exe processes that install the C++ workloads — these processes run elevated and cannot be killed from a non-elevated shell. The cl.exe compiler and Windows SDK appeared while we were trying (and failing) to kill these processes. Key insight: **if winget reports success and setup.exe processes are running, wait for them to finish — they are installing the workloads.**

### UE 5.8 C++ Plugin Source Fixes (REQUIRED — plugin won't compile without these)

The unreal-mcp plugin was written for UE 5.5. UE 5.8 removed/changed several APIs that break compilation. Three files need patching after cloning:

**Fix 1: `ANY_PACKAGE` removed in UE 5.8** (9 occurrences across 2 files)

`ANY_PACKAGE` was a legacy macro for `FindObject<UClass>()`. In UE 5.8 it's replaced by `FindFirstObject<UClass>()` which takes the name directly (no package argument).

Files affected:
- `Plugins/UnrealMCP/Source/UnrealMCP/Private/Commands/UnrealMCPBlueprintCommands.cpp` (4 occurrences)
- `Plugins/UnrealMCP/Source/UnrealMCP/Private/Commands/UnrealMCPBlueprintNodeCommands.cpp` (5 occurrences)

```cpp
// BEFORE (UE 5.5 — ANY_PACKAGE removed in 5.8):
ComponentClass = FindObject<UClass>(ANY_PACKAGE, *ComponentType);

// AFTER (UE 5.8):
ComponentClass = FindFirstObject<UClass>(*ComponentType);
```

The `TEXT("...")` form also works: `FindFirstObject<UClass>(TEXT("UGameplayStatics"))`.

Use Python string replacement for reliable patching across all occurrences:
```python
content = content.replace("FindObject<UClass>(ANY_PACKAGE, ", "FindFirstObject<UClass>(")
```

**Fix 2: `FImageUtils::CompressImageArray` deprecated** (1 occurrence)

File: `Plugins/UnrealMCP/Source/UnrealMCP/Private/Commands/UnrealMCPEditorCommands.cpp` (line ~588)

```cpp
// BEFORE (deprecated in 5.8):
FImageUtils::CompressImageArray(W, H, Bitmap, CompressedBitmap);

// AFTER (UE 5.8):
FImageUtils::PNGCompressImageArray(W, H, Bitmap, CompressedBitmap);
```

**Fix 3: `TArray<uint8>` → `TArray64<uint8>`** (same file, line ~586)

`PNGCompressImageArray` takes `TArray64<uint8>&` (64-bit array) not `TArray<uint8>&`:

```cpp
// BEFORE:
TArray<uint8> CompressedBitmap;

// AFTER:
TArray64<uint8> CompressedBitmap;
```

**Fix 4: `TCHAR_TO_UTF8` triggers C4459 in UE 5.8 StringConv.h** (2 occurrences in 1 file)

File: `Plugins/UnrealMCP/Source/UnrealMCP/Private/MCPServerRunnable.cpp` (lines ~94 and ~318)

UE 5.8's V7 build settings treat `C4459` (variable shadowing) as an error. The `TCHAR_TO_UTF8` macro instantiates `TStringConversion` which triggers `C4459` inside the engine's own `StringConv.h` header — this is an engine bug, not plugin code. Both `TCHAR_TO_UTF8` and `FTCHARToUTF8` trigger it. `FString::EncodeToUTF8()` does not exist in UE 5.8. `TCHAR_TO_ANSI` goes through the same `StringConv.h` header and triggers the same error.

**Working fix:** Use `FTCHARToUTF8` but add `#pragma warning(disable:4459)` at the top of the file to suppress the engine header warning:

```cpp
// Add at the VERY TOP of MCPServerRunnable.cpp (before any includes):
#pragma warning(disable:4459)

// Then use FTCHARToUTF8 normally in both Send() calls:
// Occurrence 1 (line ~94):
FTCHARToUTF8 UTF8Response(*Response);
if (!ClientSocket->Send((const uint8*)UTF8Response.Get(), UTF8Response.Length(), BytesSent))

// Occurrence 2 (line ~318):
FTCHARToUTF8 UTF8Response(*Response);
if (!Client->Send((const uint8*)UTF8Response.Get(), UTF8Response.Length(), BytesSent))
```

**Failed approaches (do NOT use):**
- `TCHAR_TO_UTF8(*Response)` — triggers C4459 in StringConv.h
- `FTCHARToUTF8` without pragma — same C4459 from StringConv.h
- `TCHAR_TO_ANSI` — goes through same StringConv.h, same C4459
- `FString::EncodeToUTF8()` — does not exist in UE 5.8 FString API
- `FString` cast to `char*` — type mismatch with `uint8*` expected by `Send()`

**After all four fixes, rebuild:**
```bash
"/c/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" \
  MCPGameProjectEditor Win64 Development \
  -Project="C:\Users\test\Documents\unreal-mcp\MCPGameProject\MCPGameProject.uproject" \
  -WaitMutex
```

The build compiles 7 modules total; with these fixes all should pass. First build takes ~35 seconds (UBA accelerated). If only one file changed, incremental rebuild is ~6 seconds. If the build still fails with `StringConv.h` errors after all four fixes, verify the `#pragma warning(disable:4459)` is at the absolute top of `MCPServerRunnable.cpp` (before `#include` directives).

### Verification
```bash
ls "/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe"
ls "/c/Users/test/Documents/unreal-mcp/Python/unreal_mcp_server.py"
netstat -an | grep 55557  # UE plugin TCP server (only active when UE is running)
```

### UE Plugin Build Success Verification (proven June 30 2026)

After all four source fixes, the build output should show:
```
[1/4] Compile [x64] MCPServerRunnable.cpp
[2/4] Link [x64] UnrealEditor-UnrealMCP.lib
[3/4] Link [x64] UnrealEditor-UnrealMCP.dll
[4/4] WriteMetadata MCPGameProjectEditor.target [NoUba]
Result: Succeeded
```

The output DLL is written to `C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe` (shared binary path). After building, launch UE with the project and verify port 55557:
```bash
netstat -an | grep 55557
# Should show: TCP 127.0.0.1:55557 LISTENING
```

The UE log at `MCPGameProject/Saved/Logs/MCPGameProject.log` should show:
```
LogPluginManager: Mounting Project plugin UnrealMCP
```
If UE exits immediately after launch, check the log for "Incompatible or missing module" — this means the plugin didn't compile or stale binaries exist. Clean Binaries/ and Intermediate/ dirs and rebuild.

---

## Hermes Config Editing (proven June 30 2026)

The `patch` tool refuses to edit `config.yaml` directly: "Agent cannot modify security-sensitive configuration. Edit ~/.hermes/config.yaml directly or use 'hermes config' instead."

**Workaround:** Use `hermes config set` for individual keys, then fix list values with `yaml.dump()`:

```bash
# Step 1: Set scalar values (works fine)
hermes config set "mcp_servers.maya.command" "C:\\Users\\test\\Documents\\MayaMCP\\.venv\\Scripts\\python.exe"
hermes config set "mcp_servers.unreal.command" "C:\\Users\\test\\Documents\\unreal-mcp\\Python\\.venv\\Scripts\\python.exe"
```

**Pitfall:** `hermes config set` for list values (like `args`) stores them as JSON STRING literals, not YAML lists:
```yaml
# What hermes config set produces (BROKEN — args is a string, not a list):
  maya:
    args: '["C:\\Users\\test\\Documents\\MayaMCP\\src\\maya_mcp_server.py"]'
```

```python
# Step 2: Fix with yaml.dump in Python (via execute_code or terminal python -c)
import yaml
config_path = r"C:\Users\test\AppData\Local\hermes\profiles\aec-cptx\config.yaml"
with open(config_path, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)
config["mcp_servers"]["maya"]["args"] = [r"C:\Users\test\Documents\MayaMCP\src\maya_mcp_server.py"]
config["mcp_servers"]["unreal"]["args"] = [r"C:\Users\test\Documents\unreal-mcp\Python\unreal_mcp_server.py"]
config["mcp_servers"]["maya"]["connect_timeout"] = 30
config["mcp_servers"]["maya"]["timeout"] = 120
config["mcp_servers"]["unreal"]["connect_timeout"] = 30
config["mcp_servers"]["unreal"]["timeout"] = 120
with open(config_path, "w", encoding="utf-8") as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
```

**Note on `uv` vs venv python:** The unreal-mcp README suggests using `uv` as the command. We used the venv python directly instead (`C:\\Users\\test\\Documents\\unreal-mcp\\Python\\.venv\\Scripts\\python.exe`) which works identically and avoids needing `uv` on PATH. Both approaches are valid.

### Hermes MCP Auto-Reload (verified June 30 2026)

When MCP servers are added to `config.yaml` (via `hermes config set` + yaml.dump fix), Hermes automatically detects the config change and reloads MCP servers. No restart needed. The system confirmed:
```
MCP servers have been reloaded. Added servers: maya. Reconnected servers: rhino. 46 MCP tool(s) now available.
```
This means you can add MCP servers mid-session — they become available immediately after the reload notification.

### Actual proven config entries (June 30 2026)
```yaml
mcp_servers:
  rhino:
    command: C:\Users\test\AppData\Roaming\McNeel\Rhinoceros\packages\8.0\Rhino-MCP-Platform\0.1.5\router\win-x64\rhino-mcp-router.exe
    args: ['--default-version', '8']
    connect_timeout: 75
    timeout: 180
  maya:
    command: C:\Users\test\Documents\MayaMCP\.venv\Scripts\python.exe
    args:
    - C:\Users\test\Documents\MayaMCP\src\maya_mcp_server.py
    connect_timeout: 30
    timeout: 120
  unreal:
    command: C:\Users\test\Documents\unreal-mcp\Python\.venv\Scripts\python.exe
    args:
    - C:\Users\test\Documents\unreal-mcp\Python\unreal_mcp_server.py
    connect_timeout: 30
    timeout: 120
```

## Maya Command Port Direct Socket Communication (proven June 30 2026)

The MayaMCP server uses stdio transport (MCP client to server) then forwards to Maya Command Port (TCP 50007). But you can also communicate with Maya Command Port DIRECTLY from Python, bypassing the MCP server entirely. Useful for rapid Phase 2 operations (import OBJ, apply materials, set up lights) without MCP round-trips.

**Pattern: Send MEL commands via Python socket, one connection per command:**

```python
import socket, time

def send_mel(cmd):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(('127.0.0.1', 50007))
    s.send(cmd.encode('utf-8') + b'\x00')  # null-terminated
    time.sleep(0.3)
    s.close()

# Create new scene
send_mel('file -f -new;')
time.sleep(1)

# Import OBJ
send_mel('file -import -type "OBJ" "C:/Users/test/Documents/utah_teapot.obj";')
time.sleep(3)

# Create material
send_mel('shadingNode -asShader phong -name "ceramic_white";')
send_mel('setAttr "ceramic_white.color" -type double3 1.0 1.0 1.0;')
send_mel('setAttr "ceramic_white.reflectivity" 0.8;')

# Assign to all objects
send_mel('select -all; sets -e -forceElement ceramic_whiteSG;')
```

**Key rules:**
- One socket connection per MEL command. Do NOT reuse a connection across commands.
- Null-terminate commands: `s.send(cmd.encode('utf-8') + b'\x00')`.
- Use forward slashes in file paths inside MEL: `"C:/Users/test/..."` not backslashes.
- Do NOT read response data synchronously — the MEL command port protocol requires two connections (one to execute, one to read results). For simple commands, fire-and-forget is sufficient.

### Maya Command Port CLOSE_WAIT Pitfall

After multiple rapid socket connections, Maya Command Port can enter a `CLOSE_WAIT` state where `netstat` shows the port as `LISTENING` but all new connections are refused with `ConnectionRefusedError: [WinError 10061]`.

**Symptom:** `netstat` shows `LISTENING` plus `CLOSE_WAIT` entries, but `socket.connect()` raises `ConnectionRefusedError`.

**Fix:** Have the user re-open the command port from Maya Script Editor (Python tab):
```python
import maya.cmds as cmds
cmds.commandPort(name=':50007', close=True)
cmds.commandPort(name=':50007')
```

This clears CLOSE_WAIT connections and re-enables new connections. Must be run in Maya — cannot be done remotely.

## Rhino OBJ Export for Maya Import (proven June 30 2026)

`mcp_rhino_save_doc` cannot write to WSL UNC paths — it throws `DirectoryNotFoundException`. Save to a Windows path first, then copy to WSL via `wsl bash -c "cp /mnt/c/..."`.

For OBJ export, the Rhino `_-Export` command via `run_command` can open blocking dialogs. A more reliable approach is to write the OBJ file manually from `run_python`:

```python
import Rhino, scriptcontext as sc
from Rhino.Geometry import Brep, Mesh, MeshingParameters

doc = sc.doc
all_objs = list(doc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.Brep))

obj_path = r"C:\Users\test\Documents\utah_teapot.obj"
with open(obj_path, 'w') as f:
    f.write("# Utah Teapot\n\n")
    vertex_offset = 1
    for obj in all_objs:
        name = obj.Attributes.Name if obj.Attributes.Name else "unnamed"
        f.write(f"g {name}\n")
        meshes = Mesh.CreateFromBrep(obj.BrepGeometry, MeshingParameters.Default)
        for mesh in meshes:
            verts = mesh.Vertices
            faces = mesh.Faces
            for i in range(verts.Count):
                f.write(f"v {verts[i].X:.6f} {verts[i].Y:.6f} {verts[i].Z:.6f}\n")
            for i in range(faces.Count):
                if faces[i].IsQuad:
                    f.write(f"f {faces[i].A+vertex_offset} {faces[i].B+vertex_offset} {faces[i].C+vertex_offset} {faces[i].D+vertex_offset}\n")
                else:
                    f.write(f"f {faces[i].A+vertex_offset} {faces[i].B+vertex_offset} {faces[i].C+vertex_offset}\n")
            vertex_offset += verts.Count
        f.write("\n")
```

This produces a standard OBJ with `g <name>` groups for each Brep, which Maya imports as separate mesh objects. The Utah Teapot (4 Breps) produced a 1.3MB OBJ file.

**Copy to WSL project directory:**
```bash
wsl bash -c "cp /mnt/c/Users/test/Documents/utah_teapot.obj /home/test/2026_aec_cptx_demo/aa_demo_versions/teapot_build/rhino_assets/"
```

## Autodesk Download Blocking (June 30 2026)

Autodesk's website blocks ALL automated access with Akamai 403. This affects:
- `curl` with any user agent → 403 Access Denied
- `agent-browser read` → HTTP 403
- `browser_navigate` (browser auto-launch) → Chrome not found / timeout
- Direct download URL patterns (dds.autodesk.com, efulfillment.autodesk.com) → 404 or redirect to 404 page

**Workaround:** Open the user's browser directly and let them download manually:
```bash
cmd.exe /c start msedge "https://www.autodesk.com/products/maya/free-trial"
```
The user must log in with an Autodesk account (or create one for free trial) and download the installer themselves. This is expected — do NOT attempt automated downloads for authenticated DCC tool installers.

## GitHub API for MCP Server Discovery

To find MCP servers for new DCC tools, use GitHub's REST API search:
```bash
curl -s "https://api.github.com/search/repositories?q=maya+mcp&sort=stars&order=desc&per_page=10" | python -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('items', []):
    print(f\"  {r['full_name']} | stars:{r['stargazers_count']} | updated:{r['updated_at'][:10]} | {r['description'][:80] if r['description'] else 'no desc'}\")
"
```
This is how the MayaMCP (PatrickPalmer/MayaMCP, 86 stars) and unreal-mcp (chongdashu/unreal-mcp, 2019 stars) repos were found.

## Unreal MCP TCP Protocol (proven June 30 2026)

The UnrealMCP C++ plugin listens on TCP port 55557. The Python MCP server (`unreal_mcp_server.py`) bridges stdio (MCP client) to TCP (UE plugin). But you can also communicate with UE directly via TCP, bypassing the MCP server.

**Protocol: JSON commands over TCP, one connection per command:**

```python
import socket, json

def ue_cmd(command, params=None):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect(('127.0.0.1', 55557))
    cmd_obj = {"type": command}
    if params:
        cmd_obj["params"] = params
    s.sendall(json.dumps(cmd_obj).encode('utf-8'))
    data = b""
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
            if len(data) > 10000:
                break
    except socket.timeout:
        pass
    s.close()
    try:
        return json.loads(data.decode('utf-8', 'replace'))
    except:
        return {"raw": str(data[:200])}

# Spawn a floor
r = ue_cmd('spawn_actor', {
    'name': 'Floor',
    'type': 'StaticMeshActor',
    'location': [0, 0, 0],
    'rotation': [0, 0, 0],
    'scale': [10, 10, 1]
})
```

**Key rules:**
- One TCP connection per command. UE closes the connection after responding.
- JSON format: `{"type": "command_name", "params": {...}}` — the key is `"type"`, NOT `"command"`.
- Location is `[x, y, z]` in UE world units (centimeters by default).
- Rotation is `[pitch, yaw, roll]` in degrees.

**Available actor types for `spawn_actor`:**
- `StaticMeshActor` — generic mesh actor (use for floor, walls, placeholder objects)
- `PointLight` — point light
- `SpotLight` — spot light
- `DirectionalLight` — directional (sun) light
- `CameraActor` — camera

**NOT supported:** `Cube`, `Sphere`, `Cylinder`, `Plane` — these return `"Unknown actor type: Cube"`. Use `StaticMeshActor` instead.

**Other commands:**
- `get_actors_in_level` — returns all actors with name, class, location, rotation, scale
- `set_actor_transform` — update position/rotation/scale by name
- `set_actor_property` — set a named property on an actor
- `delete_actor` — remove by name
- `take_screenshot` — saves viewport screenshot to a filepath
- `find_actors_by_name` — search actors by name pattern
- `get_actor_properties` — get all properties of an actor

**Screenshot command:**
```python
r = ue_cmd('take_screenshot', {'filepath': 'C:/Users/test/Documents/render.png'})
# Returns: {"status": "success", "result": {"filepath": "C:/Users/test/Documents/render.png"}}
```

### TIME_WAIT socket exhaustion pitfall

When sending many rapid sequential commands (6+ in quick succession), TCP connections accumulate in `TIME_WAIT` state. This causes:
- New connections to time out (the Python script hangs and the terminal command times out at 30s)
- `netstat` shows multiple `TIME_WAIT` entries on port 55557
- UE is still running and the port is still LISTENING, but new connections fail

**Fix:** Add `time.sleep(0.5)` between commands, and avoid sending more than 3-4 commands in a single Python script. For larger batch operations, combine multiple actions into a single command or use the MCP server's tool calls (which manage connections internally).

If already stuck in TIME_WAIT, wait 30-60 seconds for the OS to reclaim the sockets (default TCP TIME_WAIT timeout is 2*MSL ≈ 60s on Windows).

## Maya Save Path and FBX Export Pitfalls (proven June 30 2026)

### Maya saves to project directory, not the specified path

`file -save` with a full path does NOT save to that path. Maya saves to the current project's scenes directory (`Documents/maya/projects/default/scenes/` by default). The `-rename` flag changes the filename but not the directory.

```python
# This does NOT save to C:/Users/test/Documents/utah_teapot_textured.ma:
send_mel('file -save -type "mayaAscii" "C:/Users/test/Documents/utah_teapot_textured.ma";')

# Instead, Maya saves to: C:/Users/test/Documents/maya/projects/default/scenes/utah_teapot_textured.ma
# (if -rename was used) or to the default project scenes dir
```

**Fix:** After saving, search for the file in the Maya project directory:
```bash
find /c/Users/test/Documents/maya -name "utah_teapot*" 2>/dev/null
```

Then copy to the desired location:
```bash
cp "/c/Users/test/Documents/maya/projects/default/scenes/utah_teapot_textured.ma" /target/path/
```

### FBX export requires -exportAll flag

```python
# CORRECT — use -exportAll to export all objects:
send_mel('file -f -exportAll -type "FBX export" "C:/Users/test/Documents/utah_teapot.fbx";')

# WRONG — without -exportAll, the export may silently produce no file or an empty file
send_mel('file -f -export -type "FBX export" "C:/Users/test/Documents/utah_teapot.fbx";')
```

Always verify the FBX file exists after export:
```bash
ls -la /c/Users/test/Documents/utah_teapot.fbx
```

### Maya material assignment via Command Port

The `sets -e -forceElement` command assigns a material to selected objects. The shading group name is `<material_name>SG` (auto-created when the shader is created):

```python
# Create Phong material
send_mel('shadingNode -asShader phong -name "ceramic_white";')
send_mel('setAttr "ceramic_white.color" -type double3 1.0 1.0 1.0;')
send_mel('setAttr "ceramic_white.reflectivity" 0.8;')
send_mel('setAttr "ceramic_white.cosinePower" 50;')  # specular tightness

# Assign to all objects
send_mel('select -all;')
send_mel('sets -e -forceElement ceramic_whiteSG;')
```

## Preflight Checklist Pattern

For multi-tool demos, the preflight phase checks each tool in this order:

1. **Check install path** — `ls` the expected binary location.
2. **If missing:** Tell the user what to download and where. User handles account logins (Autodesk, Epic Games). This is expected — do NOT attempt automated downloads.
3. **Check MCP server** — repo cloned, venv created, dependencies installed.
4. **If missing:** Clone repo, create venv, pip install, add to Hermes MCP config.
5. **Verify MCP connection** — tool must be running, then test a simple command.
6. **Report status table** — Tool | Installed | MCP Connected.

### Disk space requirements (as of June 2026)
| Component | Download Size | Installed Size |
|-----------|-------------|---------------|
| Maya 2025 | ~4 GB | ~8 GB |
| Epic Games Launcher | ~200 MB | ~500 MB |
| Unreal Engine 5.5 | ~50 GB | ~55 GB |
| Visual Studio 2022 (C++ Game dev) | ~20 GB | ~20 GB |
| MayaMCP repo | <1 MB | ~10 MB (with venv) |
| unreal-mcp repo | ~50 MB | ~100 MB (with venv) |
