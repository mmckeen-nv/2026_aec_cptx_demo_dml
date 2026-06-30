# Demo Reset Procedure — cliff_house_02

How to reset the full demo pipeline back to starting state so it can be run again.
Proven end-to-end on 2026-06-11.

## Three components to reset

1. **project_prompt.md** — restore all [FILL IN] placeholders
2. **Rhino** — clear built geometry, reimport base_model.3dm
3. **Blender** — clear all objects, materials, collections, lights, cameras

## 1. Reset project_prompt.md

The design brief has ~38 answer lines that get filled during the config/interview phase.
To restore them all to `[FILL IN]`:

```bash
# Find all filled answer lines (skip template instruction lines 7, 14, 19)
# Build line-targeted sed to avoid the bulk-replace pitfall

grep -n 'Your answer:' //wsl.localhost/Ubuntu/home/test/2026_aec_cptx_demo/aa_demo_versions/cliff_house_02/user_prompts/project_prompt.md

# Then for each line N that is filled (not [FILL IN] and not a template instruction):
sed -i 'Ns|Your answer:.*|Your answer:  [FILL IN]|' <path>
```

**Best approach:** Use execute_code to compute all line numbers, build a single multi-expression
sed command, and verify the count after:

```python
# Get all "Your answer:" lines
result = terminal("grep -n 'Your answer:' <path>")
lines = result['output'].strip().split('\n')
skip_lines = {7, 14, 19}  # template instruction lines
reset_lines = []
for line in lines:
    num = int(line.split(':')[0])
    if num in skip_lines or '[FILL IN]' in line:
        continue
    reset_lines.append(num)

# Build single sed command
sed_parts = [f"-e '{ln}s|Your answer:.*|Your answer:  [FILL IN]|'" for ln in reset_lines]
terminal(f"sed -i {' '.join(sed_parts)} <path>")

# Verify: should be 39 (38 answer fields + 1 template example on line 28)
terminal("grep -c 'FILL IN' <path>")
```

**Pitfall:** Never use a bare `sed 's/Your answer:.*/Your answer:  [FILL IN]/'` without
line numbers — it would also clobber the template instruction lines (7, 14, 19) which
describe the format, not actual answer fields.

## 2. Reset Rhino

Clear all built geometry and reimport the base_model.3dm source file.

```python
import Rhino

doc = __rhino_doc__

# Delete ALL objects
all_ids = [obj.Id for obj in doc.Objects]
for oid in all_ids:
    doc.Objects.Delete(oid, True)

# CRITICAL: Purge deleted objects from memory
# Without Purge, layers that had objects on them can't be deleted
doc.Objects.Purge(0)

# Reimport base model (16 source curves + labels)
path = r"\\wsl.localhost\Ubuntu\home\test\2026_aec_cptx_demo\aa_demo_versions\cliff_house_02\rhino_assets\base_model.3dm"
doc.Import(path)
doc.Views.Redraw()

# Verify: should be 16 objects, 11 layers
```

**Pitfall — double objects:** If you don't Purge before reimporting, the old objects
may still be logically present (deleted but not purged), and the import adds new copies
on the same layers, resulting in doubled objects (32 instead of 16).

**Pitfall — layer cleanup not needed:** The base_model layers (Source_Curves, Labels)
survive the clear because they have geometry on them. After reimport, these are correct
and don't need cleanup. Any layers you created (building_site_v3, massing_v3, detailing_v3)
will have been deleted when their objects were removed + purged.

**Pitfall — open_doc clearFirst:** `mcp_rhino_open_doc(clearFirst=True, path=...)` with
UNC WSL paths can throw NullReferenceException. Use `run_python` with the manual
delete + purge + import sequence instead.

## 3. Reset Blender

Clear all objects, materials, collections, orphan data via BlenderMCP:

```python
import bpy

# Delete all objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Remove all materials
for m in list(bpy.data.materials):
    bpy.data.materials.remove(m)

# Remove all non-default collections
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)

# Remove all worlds
for w in list(bpy.data.worlds):
    bpy.data.worlds.remove(w)

# Remove lights + cameras data blocks
for l in list(bpy.data.lights):
    bpy.data.lights.remove(l)
for c in list(bpy.data.cameras):
    bpy.data.cameras.remove(c)

# Purge all orphan data
bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
```

**NEVER** use `bpy.ops.wm.read_factory_settings()` — it kills the BlenderMCP addon.

Verify via `get_scene_info`: should return `object_count: 0, materials_count: 0`.

## Verification checklist

After reset, confirm:
- [ ] `grep -c 'FILL IN' project_prompt.md` → 39
- [ ] Rhino: 16 objects, 11 layers (Source_Curves + Labels + Default)
- [ ] Blender: 0 objects, 0 materials

## Artifacts on disk

Previous run artifacts in `C:\Users\test\Documents\` are NOT deleted by reset:
- `cliff_house_02_site_prep.3dm`
- `cliff_house_02_massing.3dm`
- `cliff_house_02_detailing.3dm`
- `cliff_house_02_scene.blend`
- `cliff_house_02_test_render.png`

These are kept for reference. Delete manually if disk space is a concern.
