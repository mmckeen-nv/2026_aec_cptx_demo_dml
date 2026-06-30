---
name: ue58-mcp-plugin-fixes
description: Fix chongdashu/unreal-mcp plugin (and similar UE 5.5 plugins) to compile and run against UE 5.8 — C++ source fixes, Python API changes, and console script execution
---

# UE 5.8 MCP Plugin Compatibility Fixes

## When to use
When building the chongdashu/unreal-mcp plugin (or any UE C++ plugin written for UE 5.5) against UE 5.8, OR when running UE 5.8 Python scripts that hit API changes from 5.5.

## Prerequisites
- UE 5.8 installed (requires .NET 10.0 Runtime — winget install Microsoft.DotNet.Runtime.10)
- VS 2022 Community with C++ Game Dev workload + Windows SDK
- .NET Framework 4.8.1 Developer Pack (winget install Microsoft.DotNet.Framework.DeveloperPack_4)

## Fix 1: Target.cs files (2 files)
In both MCPGameProjectEditor.Target.cs and MCPGameProject.Target.cs:
- DefaultBuildSettings = BuildSettingsVersion.V5 -> BuildSettingsVersion.V7
- IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_5 -> EngineIncludeOrderVersion.Unreal5_8
- Add bOverrideBuildEnvironment = true (NOT BuildEnvironment = TargetBuildEnvironment.Unique — fails with installed engine)
- Update .uproject: "EngineAssociation": "5.5" -> "5.8"

## Fix 2: ANY_PACKAGE removed in UE 5.8
In UnrealMCPBlueprintCommands.cpp and UnrealMCPBlueprintNodeCommands.cpp:
- FindObject<UClass>(ANY_PACKAGE, *Name) -> FindFirstObject<UClass>(*Name)
- 9 occurrences total across both files

## Fix 3: FImageUtils::CompressImageArray deprecated
In UnrealMCPEditorCommands.cpp:
- FImageUtils::CompressImageArray -> FImageUtils::PNGCompressImageArray
- TArray<uint8> CompressedBitmap -> TArray64<uint8> CompressedBitmap

## Fix 4: TCHAR_TO_UTF8 triggers C4459 in StringConv.h
In MCPServerRunnable.cpp (2 occurrences):
- Add #pragma warning(disable:4459) at top of file
- TCHAR_TO_UTF8(*Response) -> FTCHARToUTF8 UTF8Response(*Response) then use UTF8Response.Get() and UTF8Response.Length()

## Build
Do NOT use MSBuild directly — use UE Build.bat:
"/c/Program Files/Epic Games/UE_5.8/Engine/Build/BatchFiles/Build.bat" MCPGameProjectEditor Win64 Development -Project="path/to/MCPGameProject.uproject" -WaitMutex

## Verify
After build succeeds, launch the project in UE. Check port 55557:
netstat -an | grep 55557
Should show TCP 127.0.0.1:55557 LISTENING.

## Fix 5: UE 5.8 Python API changes (runtime — not compile-time)

After the plugin compiles, Python scripts running inside UE 5.8 hit additional API changes that break scripts written for UE 5.5.

### FbxImportOptions removed
`unreal.FbxImportOptions()` does not exist in UE 5.8. The Interchange framework handles FBX import with defaults. Just create an `AssetImportTask` without setting `import_task.options`.

### automated_import_should_handle removed
`import_task.set_editor_property('automated_import_should_handle', True)` fails — this property was removed from AssetImportTask in UE 5.8. Omit it entirely.

### set_actor_location requires teleport parameter
`actor.set_actor_location(unreal.Vector(0, 0, 3), False)` fails with `TypeError: set_actor_location() required argument 'teleport' (pos 3) not found`. In UE 5.8, `teleport` is a required named parameter:
```python
actor.set_actor_location(unreal.Vector(0, 0, 3), False, False)  # (location, sweep, teleport)
```

### EditorLevelLibrary.get_editor_world deprecated
`unreal.EditorLevelLibrary.get_editor_world()` is deprecated in UE 5.8. Use the UnrealEditorSubsystem instead:
```python
editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = editor_subsystem.get_editor_world()
```

### Working FBX import script for UE 5.8
```python
import unreal
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
import_task = unreal.AssetImportTask()
import_task.set_editor_property('filename', r"C:\path\to\teapot.fbx")
import_task.set_editor_property('destination_path', "/Game/Teapot")
import_task.set_editor_property('destination_name', "teapot_mesh")
import_task.set_editor_property('replace_existing', True)
import_task.set_editor_property('save', True)
# Do NOT set import_task.options — FbxImportOptions doesn't exist in 5.8
asset_tools.import_asset_tasks([import_task])
```

### Additional runtime pitfalls (mesh import + actor spawning)

- **Mesh simplification:** UE 5.8 Interchange framework simplifies imported meshes (22K verts → 636). No Python API to disable this.
- **Import dialog:** `import_asset_tasks()` can trigger a UI dialog requiring user to click "Import" — script blocks until approved.
- **spawn_actor_from_object preferred:** Use `EditorLevelLibrary.spawn_actor_from_object(mesh, loc, rot)` instead of `spawn_actor` + `set_actor_property` — avoids MCP `set_actor_property` parameter naming issues.
- **MCP set_actor_property params:** The TCP plugin expects `property_name` and `property_value` keys, NOT `property` and `value`.
- **Maya FBX simplifies:** Maya's FBX export reduces vertex count (22K → 412). Import OBJ directly into UE for higher fidelity.

Full details in `aec-demo-operator/references/ue-python-console-execution.md` § "UE Interchange Import Pitfalls".

## UE Console Script Execution (proven June 30 2026)

To run Python scripts inside UE from outside (no direct Python API access):

### Console backtick key
UE's console opens with the backtick key (VK_OEM_3 = 0xC0), NOT tilde (~). In SendKeys, use `[char]0xC0` not `~`.

### Script path resolution
`py script.py` resolves relative to the engine binaries directory (`C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\`), NOT the project directory. Either:
- Copy the script to that directory, OR
- Use full path: `py "C:/path/to/script.py"`

### PowerShell SendKeys pattern
```powershell
# Send a console command to UE from PowerShell:
$wsh = New-Object -ComObject WScript.Shell
$wsh.SendKeys([char]0xC0)  # Open console with backtick
Start-Sleep -Milliseconds 500
$wsh.SendKeys('py assign_teapot.py{ENTER}')  # Type command + Enter
```

Must bring UE to foreground first (SetForegroundWindow). See `aec-demo-operator/references/multi-tool-mcp-servers.md` for the full PowerShell script pattern.

## Detailed reference

For full error transcripts, build process details, VS Installer pitfalls,
MSBuild flag mangling in bash/MSYS, .NET 10 + .NET FW 4.8.1 Dev Pack requirements,
and the complete step-by-step build procedure, see:
`aec-demo-operator/references/multi-tool-mcp-servers.md` sections
"UE 5.8 build process" and "UE 5.8 C++ Plugin Source Fixes".

For runtime pitfalls (mesh simplification, import dialog, spawn_actor_from_object,
MCP set_actor_property parameter names, Maya FBX simplification), see:
`aec-demo-operator/references/ue-python-console-execution.md` § "UE Interchange Import Pitfalls".
