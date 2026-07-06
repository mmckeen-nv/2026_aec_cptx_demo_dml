# UE 5.8 Python API Pitfalls (Runtime)

Complete reference of UE 5.8 Python API changes that break scripts written for UE 5.5.
Discovered June 30 2026 during teapot_build lite demo (cannon/starfield scene).

## Actor transform API

### set_actor_location — required params changed
```python
# UE 5.5 (works):
actor.set_actor_location(unreal.Vector(0, 0, 3), False)

# UE 5.8 (fails — "required argument 'teleport' (pos 3) not found"):
actor.set_actor_location(unreal.Vector(0, 0, 3), False)

# UE 5.8 (correct):
actor.set_actor_location(unreal.Vector(0, 0, 3), sweep=False, teleport=False)
```

### set_actor_rotation — required params changed
```python
# UE 5.5 (works):
actor.set_actor_rotation(unreal.Rotator(0, 180, 0))

# UE 5.8 (fails — "required argument 'teleport_physics' (pos 2) not found"):
actor.set_actor_rotation(unreal.Rotator(0, 180, 0))

# UE 5.8 (correct):
actor.set_actor_rotation(unreal.Rotator(0, 180, 0), teleport_physics=False)
```

## Material editing API

### connect_material_property — signature changed
```python
# UE 5.5 (works — 4 args):
ml.connect_material_property(node, "RGB", material, "EmissiveColor")

# UE 5.8 (fails — "takes at most 3 arguments (4 given)"):
ml.connect_material_property(node, "RGB", material, "EmissiveColor")

# UE 5.8 (correct — 3 args, property is an enum):
ml.connect_material_property(node, "RGB", unreal.MaterialProperty.MP_EmissiveColor)
# BUT: unreal.MaterialProperty.MP_EmissiveColor does NOT exist in UE 5.8!
# The correct enum name was not found. Material creation via Python
# connect_material_property is currently BLOCKED in UE 5.8.
```

**Workaround:** Create materials in the UE editor manually, or use Dynamic Material
Instances on existing materials instead of creating new ones from scratch:
```python
mid = mesh_comp.create_dynamic_material_instance(0)
mid.set_scalar_parameter_editor_property("Metallic", 1.0)
mid.set_vector_parameter_editor_property("BaseColor", unreal.LinearColor(0.8, 0.8, 0.85))
```

### MaterialExpressionConstant3Vector — constant type changed
```python
# UE 5.5 (works):
node.set_editor_property("constant", unreal.Color(255, 250, 220, 255))

# UE 5.8 (fails — "Cannot nativize 'Color' as 'LinearColor'"):
node.set_editor_property("constant", unreal.Color(255, 250, 220, 255))

# UE 5.8 (correct):
node.set_editor_property("constant", unreal.LinearColor(1.0, 0.98, 0.85, 1.0))
```

## Light component API

### PointLightComponent.light_color — needs Color, NOT LinearColor
```python
# UE 5.8 (fails — "Cannot nativize 'LinearColor' as 'Color'"):
lc.set_editor_property("light_color", unreal.LinearColor(1.0, 0.95, 0.85))

# Note: light_color on light components expects unreal.Color, the OPPOSITE
# of MaterialExpressionConstant3Vector which expects LinearColor.
# If Color fails too, omit light_color entirely — default white is fine.
```

## Properties that don't exist in UE 5.8 editor context

| Property | Object | Error | Workaround |
|----------|--------|-------|------------|
| `simulate_physics` | StaticMeshComponent | "Failed to find property" | Only available at runtime (PIE), not in editor |
| `static_material` | StaticMesh | "Failed to find property" | Use `static_mesh_component.get_material(0)` instead |
| `fog_component` | ExponentialHeightFog | "Failed to find property" | Property may be named differently; omit and use defaults |
| `auto_activate_for_player` | CameraComponent | "Failed to find property" | Try `bAutoActivate` or just place camera — it auto-activates |
| `automated_import_should_handle` | AssetImportTask | "Failed to find property" | Removed in 5.8 — omit entirely |
| `light_color` (with LinearColor) | DirectionalLightComponent | "Cannot nativize" | Use unreal.Color or omit |

## Asset import API

### FbxImportOptions removed
```python
# UE 5.5 (works):
fbx_options = unreal.FbxImportOptions()
fbx_options.set_editor_property('mesh_type_to_import', unreal.FBXImportType.FBXIT_STATIC_MESH)
import_task.options = [fbx_options]

# UE 5.8 (fails — "module 'unreal' has no attribute 'FbxImportOptions'"):
# The Interchange framework handles FBX import with defaults.
# Just create AssetImportTask WITHOUT setting options:
import_task = unreal.AssetImportTask()
import_task.set_editor_property('filename', r"C:\path\to\file.fbx")
import_task.set_editor_property('destination_path', "/Game/Teapot")
import_task.set_editor_property('destination_name', "teapot_mesh")
import_task.set_editor_property('replace_existing', True)
import_task.set_editor_property('save', True)
asset_tools.import_asset_tasks([import_task])
```

### Import dialog may block
`import_asset_tasks()` can trigger a UI dialog requiring user to click "Import".
The Python script blocks until the user approves. This is expected behavior —
tell the user to approve the import in the UE window.

### Mesh simplification
UE 5.8 Interchange framework simplifies imported meshes. A 22K-vertex OBJ was
reduced to 636 vertices on import. No Python API to disable this was found.
OBJ import generally produces better fidelity than Maya FBX export (412 verts).

## Star spawning pattern (proven June 30 2026)

Creating a starfield via material expressions hit the `connect_material_property`
API issue. The reliable workaround is spawning PointLight actors at random
spherical positions:

```python
import random, math
point_class = unreal.load_class(None, "/Script/Engine.PointLight")
random.seed(42)
for i in range(80):
    theta = random.uniform(0, 2 * math.pi)
    phi = random.uniform(0.1, math.pi - 0.1)
    radius = 20000
    x = radius * math.sin(phi) * math.cos(theta)
    y = radius * math.sin(phi) * math.sin(theta)
    z = abs(radius * math.cos(phi)) + 3000
    star = unreal.EditorLevelLibrary.spawn_actor_from_class(
        point_class, unreal.Vector(x, y, z), unreal.Rotator(0, 0, 0))
    if star:
        star.set_actor_label("Star_" + str(i))
        lc = star.get_editor_property("light_component")
        lc.set_editor_property("intensity", random.uniform(5000, 20000))
        lc.set_editor_property("attenuation_radius", random.uniform(200, 800))
```

## EditorLevelLibrary deprecation

All EditorLevelLibrary functions are deprecated in UE 5.8 (they show
DeprecationWarning but still work). The replacement is:
```python
editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = editor_subsystem.get_editor_world()
```

But `spawn_actor_from_class`, `spawn_actor_from_object`, and `destroy_actor`
on EditorLevelLibrary still function despite the warnings.
