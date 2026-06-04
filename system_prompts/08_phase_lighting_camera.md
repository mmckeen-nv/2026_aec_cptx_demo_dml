# Phase 7 — Lighting and Camera Setup
### Lighting & Camera Execution Prompt
*Part of the Hermes AEC Demo prompt suite*
*Reads: `07_phase_export_blender.md` (Phase 6 complete)*
*`[project]/user_prompts/project_prompt.md` § Sections 10 + 11*
*Version 2.0 — May 2026*

---

## Purpose

Set up and approve the HDRI lighting and hero camera. The goal is an approved
composition and lighting mood before any Cycles materials are assigned.
Lighting and camera are locked here — subsequent phases work within this envelope.

---

## Inputs

- `[project]/blender_assets/base_model.blend` from Phase 6
- `[project]/hdr/` — project HDRI file(s)
- `[project]/user_prompts/project_prompt.md` § Section 10 (lighting mood, time of day)
- `[project]/user_prompts/project_prompt.md` § Section 11 (hero camera, animation notes)
- Delta notes in `[project]/prompts/` — check for: HDRI preference, camera angle overrides

## Outputs

- `[project]/blender_assets/base_model.blend` — HDRI tuned, cameras placed
- `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`
- `[project]/test_renders/camera_lighting_NW.png` etc. — four compass test stills

---

## Pre-Phase Audit Checklist

- [ ] Phase 6 gate approved — all objects present, metadata set
- [ ] `validate_blender_scene.py` confirmed clean last phase
- [ ] HDRI file confirmed in `[project]/hdr/`
- [ ] Section 10 + 11 of `project_prompt.md` read for mood and camera intent
- [ ] No sun lamp in scene (if one exists, see Step 2 — permanent removal)

---

## OBS Recording Protocol

→ **TRAY:** Update `current_stage.json` with current phase. Announce: "Starting phase — click Record in the tray when ready."
Confirm: "Recording started — `07-lighting_camera-hermes`."

Hermes explains HDRI strategy, camera composition intent, and lighting mood
from Section 10 + 11 on screen.

→ **TRAY:** Announce: "Switching to Blender — click Record Blender in the tray when ready."
Stay on BLENDER through all lighting iterations — each test render in the
Blender render window is key demo footage.

→ **TRAY:** Announce: "Switching back to Hermes."

---

## Execution Steps

### Part A — HDRI Lighting

#### Step A1 — Confirm world shader node chain

Verify the chain from Phase 6 is present and correctly connected:
```
Environment Texture → Mapping (Rotation Z = adjustable)
    → Gamma (Value = ~4.0) → Background (Strength = adjustable) → World Output
```

If the chain is missing or broken, rebuild it:
```python
import bpy, math

world = bpy.context.scene.world
world.use_nodes = True
nt = world.node_tree

# Clear existing nodes
nt.nodes.clear()

env   = nt.nodes.new("ShaderNodeTexEnvironment")
mapp  = nt.nodes.new("ShaderNodeMapping")
gamma = nt.nodes.new("ShaderNodeGamma")
bg    = nt.nodes.new("ShaderNodeBackground")
out   = nt.nodes.new("ShaderNodeOutputWorld")

nt.links.new(env.outputs["Color"],    mapp.inputs["Vector"])
nt.links.new(mapp.outputs["Vector"],  gamma.inputs["Color"])
nt.links.new(gamma.outputs["Color"],  bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

# Starting values — tune in Steps A3/A4
gamma.inputs["Value"].default_value = 4.0
bg.inputs["Strength"].default_value = 1.35
```

#### Step A2 — Load HDRI

```python
import bpy, os
hdr_dir = r"[project_path]\hdr"
hdrs = [f for f in os.listdir(hdr_dir)
        if f.lower().endswith(('.hdr', '.exr'))]
if not hdrs:
    raise RuntimeError("No HDRI file found in hdr/ folder")

hdr_path = os.path.join(hdr_dir, hdrs[0])
world = bpy.context.scene.world
env = next(n for n in world.node_tree.nodes if n.type == 'TEX_ENVIRONMENT')
env.image = bpy.data.images.load(hdr_path)
print("Loaded HDRI:", hdrs[0])
```

If multiple HDRIs are present, use the one specified in Section 10 delta notes.

#### Step A3 — Rotate HDRI to match lighting brief

Read Section 10 of `project_prompt.md` for the intended sun direction.
- Default for west-facing ocean view: warm zone coming from the south-west
- Target Mapping Z rotation: start at ~202.5° (SSW), adjust to match test renders

```python
import bpy, math
world = bpy.context.scene.world
mapp = next(n for n in world.node_tree.nodes if n.type == 'MAPPING')
mapp.inputs["Rotation"].default_value[2] = math.radians(202.5)
```

**Always verify by rendering a compass test still** — do not trust the code value
alone. Read shadows and highlight direction from the render to confirm.

#### Step A4 — Tune strength and gamma iteratively

Render test stills at NW, NE, SE, SW while adjusting:

```python
import bpy
world = bpy.context.scene.world
bg    = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
gamma = next(n for n in world.node_tree.nodes if n.type == 'GAMMA')

bg.inputs["Strength"].default_value = 1.35    # adjust: 1.0–2.5 typical
gamma.inputs["Value"].default_value = 4.0     # adjust: 3.5–5.0 typical
```

Target look from Section 10 lighting brief (golden hour / late afternoon dusk):
- Walls warm, not washed out and not too dark
- Roof catches directional light from the correct side
- Balcony/veranda underside has soft shadow — not completely black
- Glass reflects the sky with some depth and warmth
- Interior amber glow shows through the west glazing at dusk

#### Step A5 — Permanently remove any sun lamp

If any sun lamp exists in the scene:
```python
import bpy
for obj in bpy.data.objects:
    if obj.type == 'LIGHT' and obj.data.type == 'SUN':
        # Move to hidden collection and disable from renders
        hidden = bpy.data.collections.get("__hidden__")
        if not hidden:
            hidden = bpy.data.collections.new("__hidden__")
        bpy.context.scene.collection.objects.unlink(obj)
        hidden.objects.link(obj)
        obj.hide_render = True
        obj.hide_viewport = True
        for lc in bpy.context.scene.view_layers[0].layer_collection.children:
            if lc.name == "__hidden__":
                lc.exclude = True
```

Document in project delta notes: "Sun lamp permanently hidden — Phase 7."
This is a permanent project decision. Do not re-enable.

#### Step A6 — Render four compass lighting test stills

```python
import bpy, math, os

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 128
scene.cycles.use_denoising = True
scene.render.resolution_x = 1280
scene.render.resolution_y = 720

out_dir = r"[project_path]\test_renders"
os.makedirs(out_dir, exist_ok=True)

# Create or reuse compass test camera
cam_name = "compass_cam"
if cam_name not in bpy.data.objects:
    cam_data = bpy.data.cameras.new(cam_name)
    cam_obj  = bpy.data.objects.new(cam_name, cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
else:
    cam_obj = bpy.data.objects[cam_name]

cam_obj.rotation_mode = 'XYZ'
cam_obj.data.lens = 35.0
scene.camera = cam_obj

# Building centre — adapt to project
CENTER = (0.0, 0.0, 2.5)
RADIUS = 40.0
HEIGHT = 8.0

for label, az_deg in [("NW",315),("NE",45),("SE",135),("SW",225)]:
    az = math.radians(az_deg)
    cam_obj.location = (
        CENTER[0] + RADIUS * math.sin(az),
        CENTER[1] + RADIUS * math.cos(az),
        CENTER[2] + HEIGHT )
    # Look at building centre
    direction = (
        math.Vector(CENTER) - math.Vector(cam_obj.location)
    ).normalized()
    cam_obj.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()
    scene.render.filepath = os.path.join(out_dir, f"lighting_{label}.png")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: lighting_{label}.png")
```

---

### Part B — Camera Setup

#### Step B1 — Hero camera (ocean_view)

This is the primary still and animation camera.
Position based on Section 11 of `project_prompt.md`:
- Default: south-west of building, looking north-east
- Framing: full west facade, pool in foreground, ocean horizon behind

```python
import bpy, math
from mathutils import Vector

# Remove existing ocean_view if present
if "ocean_view" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["ocean_view"])

cam_data = bpy.data.cameras.new("ocean_view")
cam_data.lens = 28.0    # moderate wide-angle [adjustable per Section 11]
cam_obj  = bpy.data.objects.new("ocean_view", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
cam_obj.rotation_mode = 'XYZ'

# Position — adapt to project geometry (SW of building)
cam_obj.location = (-18.0, -22.0, 7.0)   # [adjustable]

# Look target — between pool and building west face
look_at = Vector((2.0, 0.0, 2.5))        # [adjustable]
direction = (look_at - Vector(cam_obj.location)).normalized()
cam_obj.rotation_euler = direction.to_track_quat('-Z','Y').to_euler()

bpy.context.scene.camera = cam_obj
print("Hero camera placed at:", tuple(cam_obj.location))
```

Render one test still:
```python
import bpy, os
scene = bpy.context.scene
scene.camera = bpy.data.objects["ocean_view"]
scene.render.filepath = r"[project_path]\test_renders\hero_camera_test.png"
bpy.ops.render.render(write_still=True)
```

Evaluate the composition: building fills the frame comfortably, pool visible
in foreground, ocean horizon present. Adjust location and look_at until correct,
then record the final values in the project delta notes.

#### Step B2 — Compass test camera (compass_cam)

Already created in Step A6. Confirm it exists and is correctly named.
This camera is repositioned programmatically for test renders — never keyframed.

#### Step B3 — Animation sweep camera (patio_sweep_cam)

Create the animation camera object now. Leave unpositioned — keyframes set
in Phase 9 (currently commented out) or when animation is re-enabled.

```python
import bpy
if "patio_sweep_cam" not in bpy.data.objects:
    cam_data = bpy.data.cameras.new("patio_sweep_cam")
    cam_data.lens = 24.0
    cam_obj = bpy.data.objects.new("patio_sweep_cam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    cam_obj.rotation_mode = 'XYZ'
    print("patio_sweep_cam created — unpositioned, awaiting Phase 9")
```

---

## Post-Phase Cleanup Checklist

- [ ] No sun lamp in scene (verify: no LIGHT objects with type SUN in render)
- [ ] HDRI warm zone matches Section 10 brief (confirmed via test render shadows)
- [ ] Gamma and strength values locked and documented in delta notes
- [ ] `ocean_view` camera renders correct composition per Section 11
- [ ] `compass_cam` exists and renders correctly
- [ ] `patio_sweep_cam` object created (unpositioned)
- [ ] Four compass lighting test stills saved to `test_renders/`
- [ ] Hero camera test still saved to `test_renders/hero_camera_test.png`

---

## ▶ REVIEW GATE 7 — Lighting & Camera

Present:
1. Four compass lighting test stills (NW, NE, SE, SW)
2. Hero camera test still

Confirm:
- Lighting mood matches Section 10 brief (time of day, warmth, shadow quality)
- Hero camera framing correct per Section 11 brief
- No blown highlights on walls
- No completely black shadows under balconies/overhangs

Wait for written approval. Any lighting or camera changes requested by the user
must be recorded in `[project]/user_prompts/project_prompt.md` Section 10/11
before proceeding.

---

## Checkpoint Save

```python
import bpy, datetime
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
bpy.ops.wm.save_as_mainfile(
    filepath=fr"[project_path]\blender_assets\base_model_checkpoint_{stamp}.blend",
    copy=True)
bpy.ops.wm.save_as_mainfile(
    filepath=fr"[project_path]\blender_assets\base_model.blend")
```

→ **TRAY:** Announce: "Phase complete — stop recording in the tray."
Rename: `07-lighting_camera-hermes.mkv`, `07-lighting_camera-blender.mkv`. Confirm.

Proceed to `09_phase_materials.md`.
