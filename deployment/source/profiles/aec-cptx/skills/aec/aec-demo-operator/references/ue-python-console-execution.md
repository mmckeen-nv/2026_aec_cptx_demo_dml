# UE Python Console Execution (proven June 30 2026)

How to run Python scripts inside Unreal Engine from outside the editor, when you don't have direct Python API access (e.g., the MCP TCP server only handles actor management, not asset import).

## The Problem

The UnrealMCP TCP server (port 55557) handles actor management commands (spawn, transform, screenshot) but does NOT handle asset import (FBX, OBJ). To import an FBX file into UE, you need to run a Python script inside UE's editor. UE's Python scripting subsystem can do this, but you need to get the script into UE's console.

## Console Backtick Key

UE's output log / console command bar opens with the **backtick** key (`VK_OEM_3 = 0xC0`), NOT the tilde (`~`) key. This is a common confusion because many games use tilde for console.

## Script Path Resolution

`py script.py` resolves relative to the **engine binaries directory** (`C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\`), NOT the project directory or the current working directory.

**Options:**
1. Copy the script to the engine binaries directory:
   ```bash
   cp my_script.py "/c/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/"
   ```
   Then send: `py my_script.py`

2. Use full path in the console command:
   ```
   py "C:/Users/test/Documents/unreal-mcp/MCPGameProject/Content/Python/my_script.py"
   ```
   Note: Use forward slashes in the path.

## PowerShell SendKeys Pattern

To send a console command to UE from a Python script or terminal, use PowerShell with WScript.Shell:

```powershell
# Full PowerShell script to send a command to UE console:
Add-Type -AssemblyName System.Windows.Forms

$ue = Get-Process -Name 'UnrealEditor' -ErrorAction SilentlyContinue
if ($ue) {
    $hwnd = $ue[0].MainWindowHandle

    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public class Win {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
}
'@
    [Win]::ShowWindow($hwnd, 9)  # SW_RESTORE
    Start-Sleep -Milliseconds 500
    [Win]::SetForegroundWindow($hwnd)
    Start-Sleep -Milliseconds 1000

    # Open console with backtick key (VK_OEM_3 = 0xC0)
    $wsh = New-Object -ComObject WScript.Shell
    $wsh.SendKeys([char]0xC0)
    Start-Sleep -Milliseconds 500

    # Type the command
    $wsh.SendKeys('py my_script.py{ENTER}')
    Write-Host 'Command sent to UE console'
} else {
    Write-Host 'UE process not found'
}
```

Save this as a `.ps1` file and run via:
```bash
powershell.exe -ExecutionPolicy Bypass -File "C:\Users\test\Documents\send_ue_cmd.ps1"
```

## Verifying Script Execution

Check the UE project log for Python output:
```bash
tail -20 "/c/Users/test/Documents/unreal-mcp/MCPGameProject/Saved/Logs/MCPGameProject.log" | grep -i "python\|error\|complete"
```

Python errors appear as `LogPython: Error:` entries. Success messages appear as `LogPython:` entries with whatever you logged with `unreal.log()`.

## Working FBX Import Script for UE 5.8

```python
import unreal

fbx_path = r"C:\Users\test\Documents\utah_teapot.fbx"
import_path = "/Game/Teapot"
import_name = "utah_teapot_mesh"

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
import_task = unreal.AssetImportTask()
import_task.set_editor_property('filename', fbx_path)
import_task.set_editor_property('destination_path', import_path)
import_task.set_editor_property('destination_name', import_name)
import_task.set_editor_property('replace_existing', True)
import_task.set_editor_property('save', True)
# Do NOT set import_task.options — FbxImportOptions doesn't exist in UE 5.8
asset_tools.import_asset_tasks([import_task])
unreal.log("FBX import done")

# List imported assets
imported = unreal.EditorAssetLibrary.list_assets(import_path)
unreal.log(f"Imported assets: {imported}")

# Assign to actor
editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
all_actors = unreal.GameplayStatics.get_all_actors_of_class(
    editor_subsystem.get_editor_world(), unreal.StaticMeshActor
)
for actor in all_actors:
    if actor.get_name() == "Teapot":
        for mesh_path in imported:
            mesh_asset = unreal.EditorAssetLibrary.load_asset(mesh_path)
            if mesh_asset and isinstance(mesh_asset, unreal.StaticMesh):
                actor.static_mesh_component.set_static_mesh(mesh_asset)
                actor.set_actor_scale3d(unreal.Vector(0.5, 0.5, 0.5))
                unreal.log(f"Assigned mesh: {mesh_path}")
                break
        break

unreal.log("=== ASSIGNMENT COMPLETE ===")
```

## UE Interchange Import Pitfalls (proven June 30 2026)

### Mesh simplification on import

UE 5.8's Interchange framework simplifies meshes on import. A Rhino OBJ with 22,357 vertices and 29,329 faces was reduced to only 636 vertices after import. A Maya FBX export of the same model had only 412 vertices. For detailed models, this means the imported mesh may look low-poly compared to the source.

**Mitigation:** There is no straightforward way to disable simplification via the Python API (FbxImportOptions was removed in 5.8). If mesh fidelity matters, consider:
- Importing at a higher LOD setting via the Interchange import dialog (requires UI interaction)
- Using the UE editor's manual import workflow instead of the Python script
- Splitting the model into smaller parts so each has enough vertex density

### Import dialog may require user approval

The `import_asset_tasks()` Python call can trigger an Interchange import dialog in the UE editor that requires the user to click "Import" manually. The script blocks until the user approves. If running the script via console SendKeys, the user must switch to the UE window and click the dialog button.

### spawn_actor_from_object pattern (preferred over spawn + set_property)

Instead of spawning a generic StaticMeshActor and then trying to set its mesh via `set_actor_property` (which has parameter naming issues — see below), use `spawn_actor_from_object` to spawn the actor with the mesh already assigned:

```python
teapot_mesh = unreal.EditorAssetLibrary.load_asset("/Game/Teapot/teapot_obj")
teapot_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
    teapot_mesh,
    unreal.Vector(0, 0, 100),
    unreal.Rotator(0, 0, 0)
)
if teapot_actor:
    teapot_actor.set_actor_label("Teapot")
    teapot_actor.set_actor_scale3d(unreal.Vector(20, 20, 20))
```

This creates a StaticMeshActor with the mesh already set, avoiding the need for a separate `set_actor_property` call.

### MCP set_actor_property parameter names

The UE MCP TCP plugin's `set_actor_property` command expects `property_name` and `property_value` as parameter keys (NOT `property` and `value`):

```python
# CORRECT:
ue_cmd('set_actor_property', {
    'name': 'Teapot',
    'property_name': 'StaticMesh',
    'property_value': '/Engine/BasicShapes/Sphere.Sphere'
})

# WRONG — returns "Missing 'property_name' parameter":
ue_cmd('set_actor_property', {
    'name': 'Teapot',
    'property': 'StaticMesh',
    'value': '/Engine/BasicShapes/Sphere.Sphere'
})
```

### Maya FBX export simplifies meshes

When exporting from Maya via Command Port (`file -f -exportAll -type "FBX export"`), the resulting FBX may have significantly fewer vertices than the source OBJ. The Utah Teapot OBJ (22K verts) exported as FBX from Maya produced only 412 vertices. For higher fidelity, import the OBJ directly into UE instead of going through Maya's FBX export.

## UE 5.8 Python API Pitfalls Summary

| API | UE 5.5 | UE 5.8 | Fix |
|-----|--------|--------|-----|
| FBX import options | `unreal.FbxImportOptions()` | Removed — use Interchange defaults | Omit `import_task.options` |
| AssetImportTask prop | `automated_import_should_handle` | Removed | Omit the property |
| Actor location | `set_actor_location(pos, False)` | Requires 3rd arg | `set_actor_location(pos, False, False)` |
| Editor world | `EditorLevelLibrary.get_editor_world()` | Deprecated | `unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()` |
| EditorLevelLibrary.destroy_actor | `EditorLevelLibrary.destroy_actor(actor)` | Deprecated (warning only, still works) | Works but produces deprecation warning |
| Actor spawn with mesh | spawn + set_actor_property | Prefer spawn_actor_from_object | `EditorLevelLibrary.spawn_actor_from_object(mesh, loc, rot)` |
