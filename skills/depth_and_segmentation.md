# SKILL: Depth Maps and Segmentation Masks from Blender

## When to use this skill
Any time you need to extract depth passes or semantic segmentation masks from
a Blender Cycles scene for AI training, compositing, depth-of-field, or
object isolation workflows.

---

## COMMON PITFALLS (read before writing any code)

1. **Depth range too wide → flat gray image with no differentiation.**
   If you set near=0, far=500 and the scene is 15–60m deep, everything maps
   to a narrow mid-gray band. Always use per-frame auto-normalization.

2. **Using Workbench "depth" shading → shadows and AO appear.**
   Workbench flat shading is NOT a depth map. It still shows cavity and shadow
   effects. Use Cycles emission + CameraData node instead.

3. **HDRI not fully zeroed → ambient light creates gradient/shadows.**
   Set `bg.inputs["Strength"].default_value = 0.0` AND
   `scene.render.film_transparent = True`. Both are required.

4. **Bounces not zeroed → inter-reflections contaminate flat emission.**
   Set ALL bounce types: max_bounces, diffuse, glossy, transmission, volume = 0.

5. **Accessing Render Result in memory → returns 0×0 array.**
   `bpy.data.images["Render Result"]` is unreliable for programmatic access.
   Render to a temp EXR file instead, then read with OpenEXR + numpy.

6. **PIL mode 'I;16' deprecated for PNG in Pillow 13.**
   Use `PILImage.fromarray(uint16_array.astype(np.int32), mode='I')` instead.
   Or use the uint16 array directly: `PILImage.fromarray(uint16_array)`.

7. **EXR bottom-up vs PNG top-down → image is flipped.**
   Always apply `np.flipud()` after reading EXR pixels before saving as PNG.

---

## DEPTH MAPS — Correct Approach

### What produces a correct depth map
- Pure Z-distance from camera to each surface point
- Background = black (0)
- Near objects = white (1.0)
- Far objects = dark gray → black
- No shadows, no AO, no lighting effects

### Step 1: Create raw depth emission material

```python
import bpy

def make_raw_depth_mat():
    """
    Uses ShaderNodeCameraData 'View Distance' (true spherical distance from
    camera, no perspective distortion artifacts) wired to an emission shader.
    No normalization — raw metre values so we can normalize per-frame.
    """
    m = bpy.data.materials.get("_DepthRaw")
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new("_DepthRaw")
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()

    cam  = nt.nodes.new("ShaderNodeCameraData")
    emit = nt.nodes.new("ShaderNodeEmission")
    out  = nt.nodes.new("ShaderNodeOutputMaterial")

    # 'View Distance' = true distance, not 'View Z Depth' which is orthographic Z
    nt.links.new(cam.outputs["View Distance"], emit.inputs["Color"])
    emit.inputs["Strength"].default_value = 1.0
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return m
```

### Step 2: Assign to ALL objects and configure scene

```python
import bpy

depth_mat = make_raw_depth_mat()

# Override ALL object materials — including glass (transmission = 0 bounces anyway)
orig_mats = {}
for obj in bpy.data.objects:
    if obj.type != 'MESH': continue
    orig_mats[obj.name] = list(obj.data.materials)
    obj.data.materials.clear()
    obj.data.materials.append(depth_mat)

scene = bpy.context.scene
bpy.ops.preferences.addon_enable(module='cycles')
scene.render.engine               = 'CYCLES'
scene.cycles.device               = 'GPU'
scene.cycles.samples              = 1           # 1 sample — emission only
scene.cycles.max_bounces          = 0           # CRITICAL — no bounces
scene.cycles.diffuse_bounces      = 0
scene.cycles.glossy_bounces       = 0
scene.cycles.transmission_bounces = 0
scene.cycles.volume_bounces       = 0
scene.cycles.use_denoising        = False

# Kill world completely
world = scene.world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs["Strength"].default_value = 0.0
bg.inputs["Color"].default_value    = (0, 0, 0, 1)

scene.render.film_transparent       = True      # CRITICAL — transparent background
scene.render.image_settings.file_format = 'OPEN_EXR'
scene.render.image_settings.exr_codec  = 'NONE'   # uncompressed = faster
scene.render.image_settings.color_depth = '32'
scene.render.image_settings.color_mode  = 'RGB'
scene.render.filepath = os.path.join(TEMP_DIR, "raw_")
bpy.ops.render.render(animation=True)   # renders all frames to temp EXR
```

### Step 3: Per-frame auto-normalization (run as subprocess)

```python
"""
Run via: subprocess.run([sys.executable, 'normalise_depth.py'])
Requires OpenEXR and Pillow installed in the same Python environment.
"""
import sys, os
sys.path.insert(0, r"PATH_TO_BLENDER\python\lib\site-packages")
import OpenEXR, numpy as np
from PIL import Image as PILImage

TEMP_DIR  = "path/to/temp/exr"
DEPTH_DIR = "path/to/output/depth"
os.makedirs(DEPTH_DIR, exist_ok=True)

for fname in sorted(f for f in os.listdir(TEMP_DIR) if f.endswith('.exr')):
    frame_num = fname.replace("raw_", "").replace(".exr", "")

    # Read EXR
    f  = OpenEXR.File(os.path.join(TEMP_DIR, fname))
    px = list(f.channels().values())[0].pixels   # shape (H, W, 3), float32
    raw = px[:, :, 0].astype(np.float32)   # OpenEXR via Python already top-down — do NOT flipud

    # Per-frame auto-normalization
    valid = raw[raw > 0.01]  # exclude transparent background
    if len(valid) == 0:
        norm = np.zeros_like(raw, dtype=np.uint16)
    else:
        d_min, d_max = float(valid.min()), float(valid.max())
        # near = WHITE (1.0), far = BLACK (0.0)
        n = np.clip(1.0 - (raw - d_min) / max(d_max - d_min, 0.001), 0.0, 1.0)
        n[raw <= 0.01] = 0.0                          # background = black
        norm = (n * 65535).astype(np.uint16)

    # Save 16-bit grayscale PNG
    img = PILImage.fromarray(norm.astype(np.int32), mode='I')
    img.save(os.path.join(DEPTH_DIR, f"depth_{frame_num}.png"))
```

### Step 4: Restore beauty materials after depth render

```python
for obj in bpy.data.objects:
    if obj.type != 'MESH': continue
    obj.data.materials.clear()
    for mat in orig_mats.get(obj.name, []):
        if mat: obj.data.materials.append(mat)

# Restore render settings
scene.cycles.samples              = 384
scene.cycles.max_bounces          = 12
scene.cycles.use_denoising        = True
scene.render.film_transparent     = False
bg.inputs["Strength"].default_value = ORIGINAL_HDRI_STRENGTH
```

---

## SEGMENTATION MASKS — Correct Approach

### What a correct segmentation mask looks like
- Each object category = flat solid colour, no gradients
- Absolutely no shadows, AO, or lighting effects
- Background = black
- Colours must be IDENTICAL between frames (same RGB per category)

### Category palette (for AEC demos)

| Category | RGB | Hex |
|----------|-----|-----|
| Walls / balconies / posts | (204, 30, 30) | #CC1E1E |
| Glass / windows / doors | (25, 204, 229) | #19CCE5 |
| Roof / entry canopy | (25, 25, 217) | #1919D9 |
| Floor slabs | (229, 140, 25) | #E58C19 |
| Mullions / frames | (153, 153, 153) | #999999 |
| Terrain / grass | (20, 115, 20) | #147314 |
| Steps / landing | (89, 51, 20) | #593314 |
| Driveway / street | (51, 51, 51) | #333333 |
| Building pad | (102, 102, 102) | #666666 |

### Code

```python
import bpy

def make_seg_mat(name, r, g, b):
    """Flat emission material — zero lighting interaction."""
    m = bpy.data.materials.get(f"_Seg_{name}")
    if m: bpy.data.materials.remove(m)
    m = bpy.data.materials.new(f"_Seg_{name}")
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    emit = nt.nodes.new("ShaderNodeEmission")
    out  = nt.nodes.new("ShaderNodeOutputMaterial")
    emit.inputs["Color"].default_value    = (r, g, b, 1.0)
    emit.inputs["Strength"].default_value = 1.0
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return m

# Assign by object name
palette = {
    "wall":     make_seg_mat("wall",  0.80, 0.12, 0.12),
    "glass":    make_seg_mat("glass", 0.10, 0.80, 0.90),
    "roof":     make_seg_mat("roof",  0.10, 0.10, 0.85),
    "floor":    make_seg_mat("floor", 0.90, 0.55, 0.10),
    "mull":     make_seg_mat("mull",  0.60, 0.60, 0.60),
    "terrain":  make_seg_mat("terr",  0.08, 0.45, 0.08),
    "driveway": make_seg_mat("driv",  0.20, 0.20, 0.20),
    "building_pad": make_seg_mat("pad", 0.40, 0.40, 0.40),
}
fallback = palette["building_pad"]

for obj in bpy.data.objects:
    if obj.type != 'MESH': continue
    n = obj.name.lower()
    obj.data.materials.clear()
    matched = False
    for key, mat in palette.items():
        if key in n:
            obj.data.materials.append(mat); matched = True; break
    if not matched:
        obj.data.materials.append(fallback)

# CRITICAL: same render settings as depth pass
scene.cycles.samples              = 1
scene.cycles.max_bounces          = 0   # ALL bounce types must be 0
scene.cycles.diffuse_bounces      = 0
scene.cycles.glossy_bounces       = 0
scene.cycles.transmission_bounces = 0
scene.cycles.volume_bounces       = 0
scene.cycles.use_denoising        = False
bg.inputs["Strength"].default_value = 0.0   # world = black
scene.render.film_transparent     = True    # transparent BG = black in PNG
scene.render.image_settings.color_mode  = 'RGB'
scene.render.image_settings.color_depth = '8'
```

---

## LIBRARY REQUIREMENTS

- **OpenEXR 3.x**: `pip install openexr` in Blender's Python
  - Import path on Windows: `C:\Program Files\Blender Foundation\Blender X.X\X.X\python\lib\site-packages`
  - In subprocess scripts, insert this path via `sys.path.insert(0, ...)` before importing
  - Installed but not importable directly in `bpy` context — always use subprocess

- **Pillow**: `pip install Pillow`
  - Use `fromarray(uint16.astype(np.int32), mode='I')` for 16-bit PNG

- **numpy**: Pre-installed in Blender Python — available directly in `bpy` context

---

## OUTPUT FILE NAMING CONVENTION

```
renders/
  ocean_view/
    v_YYYYMMDD_HHMM/
      png/         beauty_0000.png  ...  (8-bit RGB)
      exr/         frame_0000.exr   ...  (32-bit float beauty)
      depth/       depth_0000.png   ...  (16-bit BW, near=white, far=black)
      depth_raw_temp/  raw_0000.exr ...  (temp: raw uncompressed float EXR)
      segmentation/ seg_0000.png    ...  (8-bit RGB, per-category colour)
```
