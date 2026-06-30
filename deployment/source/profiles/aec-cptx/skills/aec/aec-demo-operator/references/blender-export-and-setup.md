# Blender Export & Scene Setup — From Rhino Detailing

Procedure for transferring Rhino geometry to Blender and setting up Cycles rendering.

## Rhino Export: `-Export` works (June 30 2026), `_-Export` blocks

**`-Export`** (dash prefix only, no underscore) works correctly via `mcp_rhino_run_command` and does NOT block the MCP slot. It runs in command-line mode, suppresses dialogs, and completes the export. Proven June 30 2026 — exported 46 meshes to OBJ successfully:

```csharp
mcp_rhino_run_command(command: "-Export \"C:\\path\\to\\file.obj\" _Enter _Enter _Enter")
```

**`_-Export`** (underscore + dash) was previously reported as blocking. The underscore forces English command names but may behave differently with the MCP router. If `_-Export` blocks, use `-Export` instead.

**UNC path pitfall:** Rhino's `-Export` cannot write directly to WSL UNC paths (`\\wsl.localhost\Ubuntu\...`). It reports "Directory does not exist." Export to a local Windows path first (e.g. `C:\Users\test\Documents\`), then copy to the WSL project folder with `cp`.

**Export workflow (proven June 30 2026, 90 objects, VP studio fresh run):**
1. `mcp_rhino_run_command("SelAll")` — select all objects
2. `mcp_rhino_run_command("-Export \"C:\\Users\\test\\Documents\\export.obj\" _Enter _Enter _Enter")` — export locally
3. `terminal: cp "C:/Users/test/Documents/export.obj" "//wsl.localhost/Ubuntu/.../blender_assets/"` — copy to project

### Workaround: Recreate geometry in Blender programmatically

Since all building dimensions are known from the Rhino massing phase, recreate geometry directly in Blender via `mcp_blender_execute_blender_code`. This is actually cleaner because:
- Materials can be assigned inline during creation
- Collections can be organized during creation
- No coordinate-system conversion headaches (both use Z-up when working directly)
- Custom properties (`obj["material"]`) are set immediately

### Alternative: Write OBJ manually from Rhino Python (proven June 15 2026, 381 objects)

Export from Rhino by writing the OBJ file directly from `run_python`. This preserves material group assignments and avoids the blocking Export dialog.

**Key pattern:**
```python
import Rhino.Geometry as rg
import Rhino.DocObjects as rd

mp = rg.MeshingParameters.Default
mp.MinimumEdgeLength = 1.0
mp.MaximumEdgeLength = 500.0

# Group objects by material tag
objects_by_mat = {}
for obj in doc.Objects.GetObjectList(es):
    mat_tag = obj.Attributes.GetUserString("material") or "M_Concrete_WarmBone"
    meshes = []
    geo = obj.Geometry
    if geo.GetType().Name == "Brep":
        ms = rg.Mesh.CreateFromBrep(geo, mp)
        if ms:
            meshes.extend(ms)
    # Convert verts: mm -> meters (divide by 1000)
    for mesh in meshes:
        for i in range(mesh.Vertices.Count):
            v = mesh.Vertices[i]
            verts.append((v.X / 1000.0, v.Y / 1000.0, v.Z / 1000.0))
    # Write OBJ with usemtl groups and 1-indexed face indices

# Write companion .mtl with placeholder Kd values
```

**Results (June 15 2026, cliff_house):** 381 objects → 12MB OBJ, 202K vertices, 196K faces, 2276 mesh groups, 8 material groups. Coordinates written in meters. No coordinate swap needed — Blender OBJ import handles axis mapping via `forward_axis`/`up_axis` params.

**Large-scene mesh density pitfall (June 15 2026, airport — 922 exportable objects):** Default `MeshingParameters` on airport-scale models (1,570 Rhino objects, 3km site) produced a 529MB OBJ with 4.5M vertices — far too heavy for Blender. Re-export with coarser settings halved it:
```python
mp = rg.MeshingParameters.Default
mp.MinimumEdgeLength = 500    # 500mm min (was 100mm)
mp.MaximumEdgeLength = 20000  # 20m max (was 5m)
mp.SimplePlanes = True        # merge coplanar faces
```
Result: 217MB, 1.9M vertices — still large but workable in Blender 5.1. For scenes over ~500 objects or 1km site extent, always use coarse mesh params. The terrain mesh alone was 1.6M vertices at these settings. **Rule of thumb:** MinimumEdgeLength ≥ 0.5m and MaximumEdgeLength ≥ 10m for campus/airport scale.

**Important:** Do NOT apply Y/Z coordinate swap in the OBJ writer. Write raw Rhino coordinates and use `bpy.ops.wm.obj_import(forward_axis='Y', up_axis='Z')` for identity mapping. Both Rhino and Blender use X=right, Y=forward, Z=up.

**Unit conversion depends on Rhino document units:**
- cliff_house_02 (mm units): divide by 1000 → meters in OBJ
- vp_studio_01 (meter units): write raw coordinates, no conversion needed
- Always check `doc.ModelUnitSystem` before writing OBJ. If meters, skip the /1000 step.

**Proven VP studio export (June 29 2026, 451 objects):** 1.0MB OBJ, 21K verts, 15K faces, 451 groups, 18 material groups. MeshingParameters: MinEdge=0.05m, MaxEdge=5.0m, SimplePlanes=True. Compact because the geometry is all box-shaped (no curved terrain or complex organic forms).

## Material Tagging in Rhino (Step 1)

Before export/transfer, tag all Rhino objects with material User Text. Use a **list of tuples** (not dict) for priority ordering — first match wins.

```python
# Layer keyword -> material tag. Order matters: most specific first.
layer_material_map = [
    ("terrain",         "M_Terrain_DesertCoastal"),
    ("glazing",         "M_Glass_TintedBronze"),
    ("mullions",        "M_Aluminum_Bronze"),
    ("railings",        "M_Steel_EdgeTrim"),
    ("entry",           "M_Wood_DarkCedar"),
    ("garage_doors",    "M_Steel_EdgeTrim"),
    ("pool_coping",     "M_Aluminum_Bronze"),      # bronze coping
    ("pool",            "M_Concrete_Pool"),
    ("firepit",         "M_Stone_Fieldstone"),
    ("patio",           "M_Stone_Fieldstone"),      # stone deck slabs
    ("retaining",       "M_Stone_Fieldstone"),
    ("driveway",        "M_Terrain_DesertCoastal"), # decomposed granite
    ("building_pad",    "M_Concrete_WarmBone"),
    ("garage_pad",      "M_Concrete_WarmBone"),
    ("patio_pad",       "M_Concrete_WarmBone"),
    ("floor_slabs",     "M_Concrete_WarmBone"),
    ("partition_walls", "M_Concrete_WarmBone"),
    ("service_core",    "M_Concrete_WarmBone"),
    ("stairs",          "M_Concrete_WarmBone"),
    ("L1_solids",       "M_Concrete_WarmBone"),
    ("L2_solids",       "M_Concrete_WarmBone"),
    ("L2_balcony",      "M_Concrete_WarmBone"),
    ("L2_roof",         "M_Concrete_WarmBone"),
    ("L3_solids",       "M_Concrete_WarmBone"),
    ("L3_balcony",      "M_Concrete_WarmBone"),
    ("L3_roof",         "M_Concrete_WarmBone"),
]

# Also match by object name for edge cases (sidelights, jambs, etc.)
name_material_map = [
    ("glass",     "M_Glass_TintedBronze"),
    ("sidelight", "M_Glass_TintedBronze"),
    ("mull",      "M_Aluminum_Bronze"),
    ("frame",     "M_Aluminum_Bronze"),
    ("jamb",      "M_Aluminum_Bronze"),
    ("head",      "M_Aluminum_Bronze"),
    ("sill",      "M_Aluminum_Bronze"),
    ("transom",   "M_Aluminum_Bronze"),
    ("toprail",   "M_Steel_EdgeTrim"),
    ("post",      "M_Steel_EdgeTrim"),
    ("terrain",   "M_Terrain_DesertCoastal"),
    ("pool",      "M_Concrete_Pool"),
    ("water",     "M_Concrete_Pool"),
    ("entry_door","M_Wood_DarkCedar"),
    ("coping",    "M_Aluminum_Bronze"),
    ("firepit",   "M_Stone_Fieldstone"),
    ("patio",     "M_Stone_Fieldstone"),
]

# Priority: layer keyword → object name keyword → M_Concrete_WarmBone default
obj.Attributes.SetUserString("material", mat_tag)
obj.Attributes.SetUserString("layer", layer.FullPath)
obj.CommitChanges()
```

**Proven results (June 15 2026, 381 objects):**
- M_Aluminum_Bronze: 110 (mullions, frames, coping)
- M_Glass_TintedBronze: 130 (all glazing)
- M_Concrete_WarmBone: 72 (massing, slabs, walls, pads, stairs)
- M_Steel_EdgeTrim: 52 (railings, posts, garage doors)
- M_Concrete_Pool: 6, M_Stone_Fieldstone: 8, M_Terrain_DesertCoastal: 2, M_Wood_DarkCedar: 1

## BlenderMCP TCP Protocol (discovered June 2026)

BlenderMCP (Blender 5.1) listens on TCP port 9876. The protocol is:
- **Format**: JSON with `type` and `params` fields, newline-delimited (`\n` terminated)
- **Execute code**: `{"type": "execute_code", "params": {"code": "<python_code>"}}`
- **Response**: JSON with `status` ("success"/"error") and `result` dict containing `executed` (bool) and `result` (string)
- The `result` field in the response contains whatever is in the `result` variable at the end of the executed script

### Reusable helper script (C:\Users\test\Documents\blender_helper.py)

```python
import socket, json, sys

def blender_exec(code, timeout=30):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect(('127.0.0.1', 9876))
    msg = json.dumps({'type': 'execute_code', 'params': {'code': code}})
    s.sendall((msg + '\n').encode())
    data = b''
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk: break
            data += chunk
            # CRITICAL: break as soon as we have complete JSON
            try:
                json.loads(data.decode())
                break
            except:
                continue
    except socket.timeout:
        pass
    s.close()
    if data:
        return json.loads(data.decode())
    return {'status': 'error', 'message': 'no response'}
```

**Socket recv pitfall (June 2026):** Without the JSON-completeness check in the recv loop, the socket hangs indefinitely after receiving the response — the server doesn't close the connection, so `recv` blocks waiting for more data. The `try: json.loads(data); break` pattern is mandatory.

Usage from terminal: `python C:\Users\test\Documents\blender_helper.py <code_file.py>` or `python C:\Users\test\Documents\blender_helper.py --info` for scene info.

The helper supports two modes:
- `blender_helper.py <script.py>` — execute a Python file via BlenderMCP (timeout=120s)
- `blender_helper.py --info` — send `get_scene_info` and print JSON response (object_count, materials_count, object list)

### `result` variable capture is unreliable

Setting `result = "some value"` at the end of execute_code scripts often returns an empty string in the response. This appears to be a BlenderMCP addon issue — the variable is set but not reliably captured by the JSON response serializer.

**Workaround:** Don't rely on `result` for verification. Instead:
- Use `get_scene_info` command to check object/material counts: `{"type": "get_scene_info"}`
- For detailed checks, write to a temp file from bpy and read it back from the terminal
- The `status: success` field is reliable — if it says success, the code executed

### Critical Pitfall: read_factory_settings kills MCP

**NEVER** call `bpy.ops.wm.read_factory_settings()` via MCP — it unregisters all addons including BlenderMCP, killing the TCP server. The socket connection dies and cannot be restored without restarting Blender entirely.

**Instead**, to clear a scene while preserving MCP:
```python
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
```

### Recovery if MCP dies
```bash
taskkill /IM blender.exe /F
sleep 3
powershell.exe -Command "Start-Process 'C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe'"
sleep 10
# Verify: netstat -an | grep "9876.*LISTEN"
```

### Auto-start MCP server on Blender launch (proven June 30 2026)

Launch Blender with `--python` flag pointing to a script that auto-starts the MCP server, avoiding manual interaction:

```python
# C:\Users\test\Documents\start_blender_mcp.py
import bpy, time
time.sleep(3)  # wait for Blender to fully load
try:
    bpy.ops.blendermcp.start_server()
    print("BLENDER_MCP_SERVER_STARTED")
except Exception as e:
    print(f"FAILED: {e}")
```

Launch from Hermes terminal (background mode):
```bash
# Write the start script, then launch
terminal(background=true, notify_on_complete=true):
  "C:/Program Files/Blender Foundation/Blender 5.1/blender.exe" --python "C:/Users/test/Documents/start_blender_mcp.py"
```

Wait ~10 seconds, verify with `netstat -an | grep 9876 | grep LISTEN` and `python blender_helper.py --info`.

**Note:** The `--background` flag does NOT work with `bpy.ops.blendermcp.start_server()` — it requires a GUI session. Use `terminal(background=true)` (Hermes background mode) instead of Blender's `--background` flag.

**Dual-process pitfall (June 2026):** If you relaunch Blender without killing the old process first, both bind port 9876, creating stale connections that hang new requests. Always `taskkill /IM blender.exe /F` before relaunch. After launch, verify only one blender.exe is in the process list and the port shows LISTENING with no leftover ESTABLISHED connections from the old session.

The `schtasks /Run /TN "LaunchBlenderForHermes"` path also works but `powershell.exe Start-Process` is more reliable from MSYS/git-bash.

## Blender Scene Build Strategy (proven end-to-end June 2026, 301 objects + render)

**Three proven approaches, choose by complexity:**

**Approach 1: Recreate from known dimensions (fastest for <50 objects)**
Build geometry directly in Blender via bmesh/bpy.ops using meter-scale coordinates from the geometry reference. Best when massing is simple and detailing is minimal. Proven June 2026 session 2 (24 objects).

**Approach 2: OBJ manual export + import (proven June 15 2026, 381 objects)**
Write OBJ from Rhino Python (see "Write OBJ manually" above), import into Blender. Preserves exact geometry from Rhino including all detailing. Requires post-import cleanup (duplicate materials, separate by material, rotation_mode fix). Best for complex scenes with hundreds of detailed objects.

**Approach 3: Parametric batch generation (proven June 2026 session 1, 301 objects)**
Recreate geometry parametrically in Blender, generating glazing/mullion grids from dimensions. Most control over materials and collections but takes many script steps.

Building a full 300+ object scene via BlenderMCP requires batching into multiple execute_code calls. Each call runs one logical step. This exact sequence was executed successfully on 2026-06-11:

1. **Clear scene + configure Cycles** — select all, delete, remove collections, set engine/samples/resolution
2. **Create materials** — all 8 Cycles materials in one call
3. **Create collections** — flat collection list (Blender links them to scene root)
4. **Site geometry** — terrain ground plane, pad, curtain wall, driveway (4 boxes)
5. **Massing geometry** — all 11 massing volumes (one call)
6. **Curtain wall glazing + mullions** — parametric generation (one large call per face type, ~120s timeout)
7. **Punched windows** — secondary face windows (one call)
8. **Railings + doors** — balcony railings, entry door, garage doors (one call)
9. **Lighting + camera** — sun, sky world, fill light, hero camera (one call)
10. **Save** — `bpy.ops.wm.save_as_mainfile(filepath=...)`
11. **Render** — `bpy.ops.render.render(write_still=True)` with 128 samples, 75% resolution

**Write scripts to disk, execute via helper.** For complex steps, write the Python code to `C:\Users\test\Documents\bstep_N.py` and run via `python blender_helper.py bstep_N.py`. This avoids quoting hell and makes debugging easier.

**File-based script pattern (proven June 2026):** When NOT using the reusable helper, write a self-contained Python file with `write_file` (to e.g. `C:\Users\test\Documents\blender_render.py`) then run via `terminal: python C:/Users/test/Documents/blender_render.py`. This avoids:
- Backslash escaping hell with inline `-c` strings (especially Windows paths with `\U` triggering unicode escape errors)
- The `exit 124` timeout from the Python process wrapper even when Blender commands succeed
- Quote nesting issues when embedding multi-line bpy code in Python `-c` strings

**Terminal timeout for renders:** Always set `timeout=300` or higher on `terminal()` calls that wrap Blender renders. The render blocks synchronously — even GPU renders at 128 samples take 30-60s. A 60s terminal timeout will show `exit 124` even though the render completes and saves the file.

**Verify via get_scene_info between steps.** Don't rely on `result` variable — use `{"type": "get_scene_info"}` which reliably returns object_count and materials_count.

**All coordinates in meters.** Blender works natively in meters. The Rhino model is in mm. When recreating geometry in Blender, divide all Rhino coordinates by 1000 (or use the meter values from DEMO_RULES / geometry reference directly).

**CRITICAL: OBJ import axis mapping.** When writing OBJ from Rhino Python with raw `v x y z` coordinates (Rhino: X=right, Y=forward, Z=up), use `bpy.ops.wm.obj_import(forward_axis='Y', up_axis='Z')` for identity mapping. Do NOT use the Blender default `forward_axis='NEGATIVE_Z', up_axis='Y'` — that's for 3ds Max convention and will swap Y/Z axes, making the building lie on its side. Always verify scene bounding box immediately after import.

## OBJ Import Pitfalls (discovered June 15 2026)

### Duplicate `.001` materials when PBR materials pre-exist

If you create PBR materials first (recommended for cliff_house workflow) and then import an OBJ with a `.mtl` that has the same material names, Blender creates duplicate materials with `.001` suffix. The imported mesh gets the `.001` versions, not your PBR materials.

**Alternative workflow (proven June 15 2026, airport — avoids the problem entirely):**
Import OBJ first, then overwrite the placeholder materials from the .mtl in-place:
1. Import OBJ → Blender creates materials from .mtl with correct names (no .001)
2. Separate by material (`mesh.separate(type='MATERIAL')`)
3. Rename objects by their material name
4. Overwrite each material's node tree with PBR nodes (clear nodes, add Principled BSDF + output, set values)
This avoids the .001 duplication entirely because you're modifying existing materials, not creating competing ones.

**Fix if you already have duplicates — replace and clean up after import:**
```python
obj = bpy.data.objects.get("cliff_house_02_export")
for slot in obj.material_slots:
    if slot.material and slot.material.name.endswith(".001"):
        base_name = slot.material.name[:-4]
        pbr_mat = bpy.data.materials.get(base_name)
        if pbr_mat:
            slot.material = pbr_mat
# Remove orphan .001 materials
for mat in list(bpy.data.materials):
    if mat.name.endswith(".001") and mat.users == 0:
        bpy.data.materials.remove(mat)
```

### Single merged mesh — must separate by material

`bpy.ops.wm.obj_import()` imports the entire OBJ as one mesh object, even with `usemtl` groups. To get per-material objects for collection organization:

```python
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.mesh.separate(type='MATERIAL')
```

This creates one object per material slot. Each object inherits the material from its faces. Then organize into collections by reading `obj.material_slots[0].material.name`.

### OBJ import axis settings — CRITICAL

For OBJ files written with raw Rhino coordinates (no Y/Z swap in the writer), import with **identity mapping**:
```python
bpy.ops.wm.obj_import(
    filepath=obj_path,
    forward_axis='Y',
    up_axis='Z'
)
```

**Do NOT use `forward_axis='NEGATIVE_Z', up_axis='Y'`** — that's the 3ds Max convention and will swap Y/Z axes, making the building lie on its side. Symptom: the scene's Z range equals the Rhino Y range (north-south span) instead of the Rhino Z range (vertical). Discovered June 15 2026 — the first import attempt produced a scene with Z: -20 to 16.5 (should have been Y range), while Y: -5 to 13.4 (should have been Z range).

### Post-import checklist

1. Replace `.001` materials with PBR versions
2. Separate by material (`mesh.separate(type='MATERIAL')`)
3. Set `rotation_mode = 'XYZ'` on ALL mesh objects (critical — Rhino imports arrive as QUATERNION)
4. Set custom properties: `obj["material"] = mat_name` for downstream pipeline use
5. Organize into collections by material name mapping

### Post-import axis fix when import params were wrong (proven June 30 2026)

If OBJ was imported without explicit `forward_axis='Y', up_axis='Z'` (i.e., Blender defaults applied), the Y/Z axes are swapped — the building lies on its side with Z containing the Y range and vice versa. Fix AFTER import:

```python
import math

obj = bpy.data.objects.get("vp_studio_01_export")
# Step 1: rotate -90 around X (puts Y into Z but flips Z negative)
obj.rotation_euler = (math.radians(-90), 0, 0)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

# Step 2: Z is now negative — rotate 180 around X to flip Z positive
obj.rotation_euler = (math.radians(180), 0, 0)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

# Verify: Z range should match Rhino's vertical extent (0 to 19 for VP studio)
mesh = obj.data
zs = [v.co.z for v in mesh.vertices]
print(f"Z: {min(zs):.2f} to {max(zs):.2f}")  # should be 0 to ~19
```

**Why two rotations:** A single +90 rotation around X is the correct fix, but applying it as a single transform can confuse the apply operator depending on initial rotation mode. The two-step (-90 then 180 = net +90) is more reliable because each step's transform_apply succeeds cleanly. Alternatively, use `forward_axis='Y', up_axis='Z'` on import to avoid the problem entirely.

### Face-center material assignment for single-mesh OBJ (proven June 30 2026)

When OBJ imports as a single mesh with no material groups (or all geometry under one material), assign materials by checking polygon center coordinates. This is the fallback when per-object material tagging wasn't done on the Rhino side:

```python
import math

obj = bpy.data.objects.get("vp_studio_01_export")
mesh = obj.data

# Create material slots
mesh.materials.clear()
mesh.materials.append(mat_cladding)   # slot 0
mesh.materials.append(mat_concrete)    # slot 1
mesh.materials.append(mat_asphalt)    # slot 2
mesh.materials.append(mat_glass)      # slot 3
mesh.materials.append(mat_led)        # slot 4
mesh.materials.append(mat_steel)      # slot 5
mesh.materials.append(mat_roof)       # slot 6

for poly in mesh.polygons:
    cx, cy, cz = poly.center
    mat = 0  # default cladding

    # Assign by Z ranges (site at Z~0, slab at Z~1.2, roof at Z~18, etc.)
    if abs(cz) < 0.01:
        mat = 2 if (abs(cx) > 35 or abs(cy) > 35) else 1  # asphalt vs concrete
    elif 1.0 <= cz <= 1.25:
        mat = 1  # stage slab = concrete
    elif 17.9 <= cz <= 18.5 or 8.4 <= cz <= 8.9:
        mat = 6  # roof membrane
    elif 14.9 <= cz <= 15.6:
        mat = 5  # rigging grid = steel
    elif 1.3 <= cz <= 8.4:
        dist = math.sqrt(cx*cx + (cy+8)*(cy+8))
        mat = 4 if dist < 12 else 0  # LED wall vs cladding
    # ... add Y-based checks for glazing, etc.

    poly.material_index = mat
```

**Key insight:** The polygon center (`poly.center`) is in object-local coordinates AFTER transform_apply. Always verify the bounding box first (`min/max of vertex coordinates`) to calibrate the Z thresholds before writing the assignment logic.

## Blender Scene Setup

### Collection hierarchy

**Full hierarchy (for detailed 300+ object scenes):**
```
Scene Collection
├── building_site/
│   ├── terrain/
│   ├── pad/
│   └── curtain_wall/
├── massing/
│   ├── L1_solids/
│   ├── L2_solids/
│   ├── L2_balconies/
│   └── L3_pool/
└── detailing/
    ├── glazing/
    ├── mullions/
    ├── railings/
    ├── entry/
    └── garage/
```

**Rapid-build flat hierarchy (proven June 2026 session 2, 24 objects):**
```
Scene Collection
├── Site/       (terrain, pads, retaining walls, driveway)
├── Building/   (L1/L2 walls, slabs, roof, garage)
├── Glazing/    (glass curtain wall panels)
└── Details/    (entry door, garage doors, railings)
```
Use the flat structure when building quickly from known dimensions. Each collection gets objects with materials assigned inline. Faster to create and easier to manage for scenes under ~50 objects.

### Reusable create_box helpers

**Approach A: bpy.ops (for small batches, straightforward)**

Uses `bpy.ops.mesh.primitive_cube_add` — easy to understand but relies on `bpy.context.active_object` which can break in batch loops.

```python
def create_box(name, min_pt, max_pt, collection_name, material_name):
    x0, y0, z0 = min_pt
    x1, y1, z1 = max_pt
    # CRITICAL: sort coordinates
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    cx, cy, cz = (x0+x1)/2, (y0+y1)/2, (z0+z1)/2
    sx = max(x1-x0, 0.001)
    sy = max(y1-y0, 0.001)
    sz = max(z1-z0, 0.001)
    if sx < 0.005 or sy < 0.005 or sz < 0.005:
        return None
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cx, cy, cz), scale=(sx, sy, sz))
    obj = bpy.context.active_object
    obj.name = name
    bpy.ops.object.transform_apply(scale=True)
    mat = bpy.data.materials.get(material_name)
    if mat: obj.data.materials.append(mat)
    col = bpy.data.collections.get(collection_name)
    if col:
        for c in obj.users_collection: c.objects.unlink(obj)
        col.objects.link(obj)
    return obj
```

**Approach B: bmesh (for batch creation, proven June 2026 session 2, 24 objects)**

Uses `bmesh.ops.create_cube` + direct object creation — no `bpy.ops` context dependency, more reliable in loops. Takes `location` (center) and `size` (full dimensions as tuple):

```python
import bmesh
from mathutils import Vector

def add_box(name, loc, size, collection_name, material_name):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = loc
    obj.scale = size
    col = get_or_create_collection(collection_name)
    col.objects.link(obj)
    if material_name in bpy.data.materials:
        obj.data.materials.append(bpy.data.materials[material_name])
    return obj
```

Both approaches work. Approach B is preferred for rapid scene builds because it avoids operator context issues.

### Cycles Materials (cliff_house_02 palette)

| Material Tag | Base Color (R,G,B) | Roughness | Metallic | Notes |
|---|---|---|---|---|
| M_Concrete_WarmBone | 0.88, 0.85, 0.80 | 0.65 | 0.0 | Walls, slabs |
| M_Glass_TintedBronze | 0.5, 0.55, 0.6 | 0.02 | 0.0 | Transmission Weight=0.7, IOR=1.52 |
| M_Aluminum_Bronze | 0.65, 0.50, 0.35 | 0.2 | 1.0 | Warm bronze, fully metallic |
| M_Stone_Fieldstone | 0.5, 0.47, 0.42 | 0.8 | 0.0 | Retaining wall |
| M_Terrain_DesertCoastal | 0.5, 0.45, 0.32 | 0.9 | 0.0 | Ground plane |
| M_Concrete_Pool | 0.4, 0.6, 0.7 | 0.3 | 0.0 | Pool basin |
| M_Wood_DarkCedar | 0.4, 0.25, 0.14 | 0.55 | 0.0 | Entry door |
| M_Steel_EdgeTrim | 0.15, 0.15, 0.17 | 0.15 | 1.0 | Railings, garage |

### Cycles Materials (vp_studio_01 palette — industrial/VP, proven June 29 2026)

18 materials for dark-clad industrial VP stage. Key difference from residential: heavy use of metallic darks, emissive materials for LED/screens, and matte acoustics.

| Material Tag | Base Color (R,G,B) | Roughness | Metallic | Notes |
|---|---|---|---|---|
| M_Metal_CharcoalStandingSeam | 0.06, 0.06, 0.065 | 0.18 | 1.0 | Dominant cladding — needs high Specular IOR Level (0.8) to catch sunlight |
| M_Aluminum_DarkAnodized | 0.06, 0.06, 0.07 | 0.15 | 1.0 | Window mullions |
| M_Steel_DarkMatte | 0.05, 0.05, 0.055 | 0.30 | 1.0 | Production equipment, trusses, cable trays |
| M_Steel_Yellow | 0.75, 0.65, 0.05 | 0.50 | 0.0 | Safety bollards |
| M_Acoustic_DarkGrey | 0.10, 0.10, 0.10 | 0.90 | 0.0 | Acoustic shell interior |
| M_Concrete_SealedGrey | 0.35, 0.34, 0.32 | 0.65 | 0.0 | Slabs, drives, loading dock |
| M_Asphalt_Dark | 0.06, 0.055, 0.05 | 0.80 | 0.0 | Parking lot — slight reflectivity for wet look |
| M_CementBoard_LightGrey | 0.55, 0.53, 0.50 | 0.75 | 0.0 | South facade accent |
| M_Drywall_White | 0.88, 0.87, 0.85 | 0.80 | 0.0 | Interior partition walls |
| M_Glass_DarkBronze | Glass BSDF | 0.03 | — | IOR 1.52, color (0.15, 0.18, 0.20) |
| M_Wood_WarmOak | 0.40, 0.28, 0.12 | 0.50 | 0.0 | Furniture, reception desk |
| M_Fabric_DarkGrey | 0.12, 0.12, 0.14 | 0.90 | 0.0 | Chairs, seating |
| M_Paint_White | 0.85, 0.85, 0.85 | 0.30 | 0.0 | Production trucks, trailers |
| M_Paint_Red | 0.55, 0.04, 0.02 | 0.35 | 0.0 | Hero vehicle |
| M_Foliage_Green | 0.08, 0.25, 0.05 | 0.85 | 0.0 | Trees, landscaping |
| M_LED_Panel_Emissive | 0.02, 0.01, 0.08 | 0.10 | 0.0 | Emission: (0.20, 0.12, 0.70), Strength: 25.0 |
| M_Screen_Emissive | 0.05, 0.08, 0.12 | 0.10 | 0.0 | Emission: (0.50, 0.65, 0.85), Strength: 15.0 |
| M_Emissive_White | 0.90, 0.90, 0.90 | 0.20 | 0.0 | Emission: (1.0, 0.95, 0.85), Strength: 12.0 — signage |

**VP material tagging map (layer keyword → material, Rhino-side):**
```python
layer_material_map = [
    ("Landscaping", "M_Foliage_Green"), ("LED_Volume", "M_LED_Panel_Emissive"),
    ("Cable_Trays", "M_Steel_DarkMatte"), ("Trusses", "M_Steel_DarkMatte"),
    ("Steel_Frame", "M_Steel_DarkMatte"), ("Studio_Lights", "M_Steel_DarkMatte"),
    ("Cameras", "M_Steel_DarkMatte"), ("Grip_Equipment", "M_Steel_DarkMatte"),
    ("Set_Pieces", "M_Paint_Red"), ("Video_Village", "M_Steel_DarkMatte"),
    ("Acoustic_Shell", "M_Acoustic_DarkGrey"),
    ("Mullions", "M_Aluminum_DarkAnodized"), ("Glazing", "M_Glass_DarkBronze"),
    ("Metal_Panels_Vertical", "M_Metal_CharcoalStandingSeam"),
    ("Cement_Board", "M_CementBoard_LightGrey"),
    ("Signage", "M_Emissive_White"), ("Furniture_GF", "M_Wood_WarmOak"),
    ("Furniture_Upper", "M_Wood_WarmOak"), ("Interior_Walls", "M_Drywall_White"),
    ("Loading_Dock", "M_Concrete_SealedGrey"), ("Bollards", "M_Steel_Yellow"),
    ("Production_Trucks", "M_Paint_White"), ("Base_Camp_Trailers", "M_Paint_White"),
    ("Rooftop_HVAC", "M_Metal_CharcoalStandingSeam"),
    ("Electrical", "M_Steel_DarkMatte"), ("Asphalt_Lot", "M_Asphalt_Dark"),
    ("Concrete_Apron", "M_Concrete_SealedGrey"),
    ("Stage_House", "M_Metal_CharcoalStandingSeam"),
    ("Support_Wing", "M_Metal_CharcoalStandingSeam"),
    ("Site", "M_Asphalt_Dark"),
]
# Also use name_material_map for object-name overrides (Monitor→M_Screen_Emissive, etc.)
```

Glass material — TWO APPROACHES, choose by render engine:

**Approach A: Glass BSDF node (simpler, proven June 2026 session 2)**
Use a dedicated `ShaderNodeBsdfGlass` instead of Principled BSDF. This is more reliable for Cycles glass rendering than Principled BSDF with transmission, especially at low sample counts:
```python
nodes = mat.node_tree.nodes
links = mat.node_tree.links
for node in nodes: nodes.remove(node)  # clear defaults
output = nodes.new('ShaderNodeOutputMaterial')
glass = nodes.new('ShaderNodeBsdfGlass')
glass.inputs['Color'].default_value = (0.75, 0.82, 0.85, 1.0)  # slight blue-grey
glass.inputs['Roughness'].default_value = 0.02
glass.inputs['IOR'].default_value = 1.52
links.new(glass.outputs['BSDF'], output.inputs['Surface'])
```

**Approach B: Principled BSDF with Transmission Weight (more control)**
```python
bsdf.inputs["Transmission Weight"].default_value = 0.7  # NOT "Transmission"
bsdf.inputs["IOR"].default_value = 1.52
bsdf.inputs["Specular IOR Level"].default_value = 0.8
```

**PITFALL (June 2026):** Do NOT use `mat.blend_method = 'BLEND'` with `Alpha < 1.0` on Principled BSDF for Cycles glass. This is an EEVEE-only approach — in Cycles it renders the glass panels as opaque flat-colored surfaces with no refraction or transparency. Use Glass BSDF (Approach A) or Transmission Weight (Approach B) instead.

### Blender API Gotchas

- **Sky texture type**: Use `'HOSEK_WILKIE'` (with underscore) — NOT `'HOSEKWILKIE'`, NOT `'NISHITA'`. Valid types: `SINGLE_SCATTERING`, `MULTIPLE_SCATTERING`, `PREETHAM`, `HOSEK_WILKIE`. This enum is case-sensitive.
- **AgX look names**: Must include the `AgX -` prefix. E.g. `'AgX - Medium High Contrast'`, not `'Medium High Contrast'`.
- **Scene compositor**: Access via `bpy.context.scene.use_nodes = True` then the compositor node tree is separate from the scene object. Don't access `scene.node_tree` — that doesn't exist; use the compositor nodes differently.
- **Render timeout**: `bpy.ops.render.render(write_still=True)` blocks synchronously. With GPU (CUDA/OPTIX), 256 samples at 1920×1080 completes in <60s for scenes up to ~5,000 objects. On CPU at 512 samples it may exceed 180s MCP timeout. Use **128 samples at 75% resolution** for test renders, **256 samples at full resolution** for quality renders. Even if MCP times out, the render may still complete and save the file. Always set timeout=600 on the terminal call wrapping a render.
- **Film exposure**: `bpy.context.scene.cycles.film_exposure = 1.2` to brighten.

### Golden Hour Lighting Setup

```python
# Sun light — deep amber, very low angle
sun.data.energy = 8.0
sun.data.color = (1.0, 0.65, 0.3)  # Deep warm amber
sun.rotation_euler = (math.radians(85), 0, math.radians(-50))  # Nearly horizon
sun.data.angle = math.radians(2.0)  # Soft edge

# Hosek/Wilkie sky
sky.turbidity = 8.0  # Dusty golden atmosphere
sky.sun_direction = (-0.9, -0.3, 0.08)  # Nearly setting, W-SW

# Area fill light (sky bounce)
fill.data.energy = 80
fill.data.color = (0.55, 0.6, 0.85)  # Cool blue
fill.data.size = 40  # Very soft
```

**⛔ Interior emissive light escape pitfall (discovered June 29 2026, VP studio):**
Area lights placed INSIDE an enclosed building (behind opaque walls) will NOT illuminate exterior surfaces or be visible in exterior renders. The walls block all light — even emissive materials on interior objects won't create visible glow from outside.

**Fix:** For scenes where interior glow should be visible (e.g. LED stage glow spilling from dock doors, brain bar monitor glow through windows), place area lights JUST OUTSIDE the wall openings, facing outward:
```python
# LED glow spilling from open loading dock (north side)
dock_glow.location = (0, 27, 5)       # just outside dock opening
dock_glow.rotation_euler = (math.radians(-90), 0, 0)  # faces outward
dock_glow.data.energy = 5000           # needs to be high to read in exterior view

# Brain bar glow through window (east side of support wing)
bb_glow.location = (18.6, -2, 6)      # just outside the window surface
bb_glow.rotation_euler = (0, math.radians(-90), 0)  # faces toward camera
bb_glow.data.energy = 1200
```
Combine with emissive materials on the actual LED/screen geometry for close-up views, but for exterior hero shots, the exterior-facing area lights are what creates the visible glow effect.

**Lighting energy scale for industrial buildings (June 29 2026):**
Dark metal cladding (metallic, roughness 0.18-0.25) absorbs far more light than light-colored concrete. For dark-clad industrial buildings, multiply all light energies ~2-3x vs residential settings:
- Sun: 12.0 (not 8.0)
- Fill: 500 (not 80)
- Accent area lights: 1000-5000 (not 200-800)
- Film exposure: 1.3-1.4 (not 1.1-1.2)

### Hero Camera (cliff_house_02)

- Location: (-15, -35, 10) — elevated SW angle, full building in frame
- Target: (5, -5, 4) — center of building mass
- Lens: 28mm (wide, dramatic)
- Use `direction.to_track_quat('-Z', 'Y').to_euler()` for aim
- Previous attempt (-2, -20, 4) was too close — clipped base and right edge

### Camera look-at pattern (proven June 30 2026)

Full code pattern for pointing a camera at a target using mathutils:

```python
import math
import mathutils

cam = bpy.data.objects.get("Camera")
cam.location = (-55, -50, 30)  # camera position
target = mathutils.Vector((7, 0, 9))  # look-at point (building center)
cam_pos = mathutils.Vector(cam.location)
direction = target - cam_pos
rot_quat = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot_quat.to_euler()
```

This is more reliable than manually setting `rotation_euler` with guessed angles. The `to_track_quat('-Z', 'Y')` aligns the camera's -Z axis (view direction) toward the target while keeping Y as the up vector.

### Hero Camera (vp_studio_01 — proven June 30 2026)

- Location: (-55, -50, 30) — elevated SW angle
- Target: (7, 0, 9) — center of building mass
- Lens: 50mm (standard, less distortion for large building)
- Uses the mathutils look-at pattern above

## Saved Artifacts

After Blender setup, save:
- `cliff_house_02_scene.blend` — main Blender working file (301 objects, proven June 2026)
- `cliff_house_02_checkpoint_YYYYMMDD_HHMM.blend` — timestamped backup via `bpy.ops.wm.save_as_mainfile(filepath=..., copy=True)`
- `cliff_house_02_test_render.png` — test render at 128 samples / 75% resolution (~780KB)

VP Studio artifacts (proven June 29 2026):
- `vp_studio_01_scene.blend` — 18 objects (separated by material), 7 collections, 18 PBR materials
- `vp_studio_01_export.obj` + `.mtl` — 1.0MB OBJ source with material groups
- `vp_studio_01_final_render.png` — 1920x1080, 256 samples, golden hour with LED glow (2.3MB)
- Test renders in `test_renders/` for iteration history

Rhino checkpoints (saved before Blender stage):
- `cliff_house_02_site_prep.3dm` — Phase 1 (20 objects)
- `cliff_house_02_massing.3dm` — Phase 2 (31 objects)
- `cliff_house_02_detailing.3dm` — Phase 3 (318 objects)
