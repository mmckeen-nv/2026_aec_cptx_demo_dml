# Phase 8 — Cycles Materials
### Cycles Material Assignment Prompt
*Part of the Hermes AEC Demo prompt suite*
*Reads: `08_phase_lighting_camera.md` (Phase 7 complete)*
*`[project]/user_prompts/project_prompt.md` § Section 8*
*Version 2.0 — May 2026*

---

## Purpose

Assign Principled BSDF (Cycles-ready) materials to all objects in Blender,
driven by the material tags set in Phase 6 and the approved palette in Section 8
of the user prompt. This phase ends at a render-approved material state.
All changes are written back to Section 8 of `project_prompt.md`.

## Material System Overview

The material pipeline flows through three phases and one final step:

| Phase | Location | Role |
|---|---|---|
| 5 — Detailing | Rhino display materials | Visual approximation for design review |
| 6 — Export | Rhino User Text `material` tag | Data bridge: tags survive .3dm → Blender |
| 8 — Cycles Materials | Blender Principled BSDF | Physically-based render materials |
| 11 — ComfyUI | Text prompt ingredients | Stylistic enhancement in image diffusion |

Section 8 of `project_prompt.md` is the **single source of truth** for all
material decisions. Tags, colours, roughness values, and description notes
all live there. Every change approved at the Phase 8 gate is written to Section 8
before the phase closes.

---

## Inputs

- `[project]/blender_assets/base_model.blend` from Phase 7
- `[project]/user_prompts/project_prompt.md` § Section 8 — canonical tag list + parameters
- `aec_skills.md` Skill 09 — material assignment patterns

## Outputs

- `[project]/blender_assets/base_model.blend` — all Cycles materials assigned
- `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`
- `[project]/test_renders/` — eight progressive test stills
- Updated `project_prompt.md` § Section 8 — reflects any approved changes

---

## Pre-Phase Audit Checklist

- [ ] Phase 7 gate approved — lighting and camera confirmed
- [ ] Section 8 of `project_prompt.md` read this session
- [ ] All objects have `material` custom property (verified in Phase 6)
- [ ] `rotation_mode = 'XYZ'` confirmed on all objects (Phase 6)

---

## OBS Recording Protocol

→ **TRAY:** Update `current_stage.json` with current phase. Announce: "Starting phase — click Record in the tray when ready."
Confirm: "Recording started — `08-cycles_materials-hermes`."

Hermes presents the material palette from Section 8 on screen,
explains the tag → Cycles mapping strategy.

→ **TRAY:** Announce: "Switching to Blender — click Record Blender in the tray when ready."
Stay on BLENDER through all material assignment and test renders.
The progressive material appearance (per-category test renders) is key demo footage.

→ **TRAY:** Announce: "Switching back to Hermes."

---

## Execution Steps

### Step 1 — Read Section 8 and build material palette dict

Read `[project]/user_prompts/project_prompt.md` Section 8.
Extract the tag names, colour values, roughness, metallic, and any special
parameters (glass transmission, emission, etc.).

Build a Python dict mapping each canonical tag to its Cycles parameters.
Example for cliff_house_01 — adapt to the actual Section 8 content:

```python
MATERIAL_PALETTE = {
    # tag_name: (base_color_linear, roughness, metallic, special)
    "M_Concrete_WarmBone":   ((0.72, 0.64, 0.50), 0.80, 0.0, None),
    "M_Glass_TintedBronze":  ((0.20, 0.22, 0.22), 0.0,  0.0, {"transmission": 0.25}),
    "M_Aluminum_Bronze":     ((0.35, 0.25, 0.14), 0.45, 0.60, None),
    "M_Stone_Fieldstone":    ((0.28, 0.24, 0.18), 0.92, 0.0, None),
    "M_Wood_DarkCedar":      ((0.10, 0.05, 0.02), 0.72, 0.0, None),
    "M_Concrete_Pool":       ((0.08, 0.12, 0.16), 0.85, 0.0, None),
    "M_Steel_EdgeTrim":      ((0.10, 0.10, 0.10), 0.35, 0.85, None),
    "M_Terrain_DesertCoastal":((0.42, 0.36, 0.22), 0.95, 0.0, None),
    "M_Granite_DG":          ((0.38, 0.30, 0.20), 0.92, 0.0, None),
    # Add all tags from Section 8
}
```

### Step 2 — Create and assign Cycles materials

```python
import bpy

def make_mat(name, base_color, roughness, metallic=0.0, special=None):
    """Create a Principled BSDF material."""
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)     # always rebuild fresh
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b  = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    b.inputs["Base Color"].default_value  = (*base_color, 1.0)
    b.inputs["Roughness"].default_value   = roughness
    b.inputs["Metallic"].default_value    = metallic

    if special and "transmission" in special:
        # Blender 5.x: check available input names
        for input_name in ["Transmission Weight", "Transmission"]:
            if input_name in b.inputs:
                b.inputs[input_name].default_value = special["transmission"]
                break

    return m

def assign_mat(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)

# Build material library
materials = {}
for tag, (color, rough, metal, special) in MATERIAL_PALETTE.items():
    materials[tag] = make_mat(tag, color, rough, metal, special)

# Assign by custom property tag
assigned = 0; fallback = 0; skipped = 0
for obj in bpy.data.objects:
    if obj.type != 'MESH':
        skipped += 1; continue
    tag = obj.get("material", "")
    if tag and tag in materials:
        assign_mat(obj, materials[tag])
        assigned += 1
    else:
        # Fallback: infer from object name
        n = obj.name.lower()
        tag_fallback = None
        if   "glass" in n or "glazing" in n: tag_fallback = "M_Glass_TintedBronze"
        elif "mull" in n or "frame" in n:    tag_fallback = "M_Aluminum_Bronze"
        elif "terrain" in n:                 tag_fallback = "M_Terrain_DesertCoastal"
        elif "pool" in n:                    tag_fallback = "M_Concrete_Pool"
        else:                                tag_fallback = "M_Concrete_WarmBone"
        if tag_fallback in materials:
            assign_mat(obj, materials[tag_fallback])
        fallback += 1

print(f"Assigned={assigned} Fallback={fallback} Skipped={skipped}")
```

Report fallback count. Any fallbacks should be investigated — they indicate
missing or incorrect tags from Phase 6. Fix the tags and reassign.

### Step 3 — Progressive test renders (one per material category)

After assigning each major category, render a 64-sample test still and
display it in the Blender render window. This progressive reveal is good
demo footage and catches material errors early.

Render sequence:
1. After all concrete/wall materials → compass SW test still
2. After glass and mullions → compass SW test still
3. After terrain and ground → compass SW test still
4. After all remaining (pool, steel, cedar) → compass SW test still

```python
import bpy, os
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.render.resolution_x = 960
scene.render.resolution_y = 540
out = r"[project_path]\test_renders"
scene.camera = bpy.data.objects["compass_cam"]
# Position compass_cam SW before rendering
```

### Step 4 — Full eight-direction test render

After all materials assigned, render all eight test stills:
four diagonal compass views of the whole building + four close-up stills
of key material details.

```python
import bpy, os
scene.cycles.samples = 128
scene.render.resolution_x = 1280
scene.render.resolution_y = 720

for label, az_deg, radius, height in [
    ("NW_wide", 315, 40, 8), ("NE_wide", 45,  40, 8),
    ("SE_wide", 135, 40, 8), ("SW_wide", 225, 40, 8),
    ("NW_close",315, 20, 5), ("NE_close",45,  20, 5),
    ("SE_close",135, 20, 5), ("SW_close",225, 20, 5)]:
    # position compass_cam and render
    ...
```

Save all eight to `test_renders/materials_*.png`.

### Step 5 — Present and await approval

Present all eight test renders for review. Ask the user:
- Does the palette match the intention in Section 8?
- Any materials to adjust (colour, roughness, metallic, transmission)?
- Any objects that appear to have the wrong material assigned?

**Record all approved changes in `project_prompt.md` Section 8 immediately**
before proceeding. Do not close this phase without updating the source of truth.

The update format in Section 8:
```
[UPDATED Phase 8 — approved YYYYMMDD]
M_Concrete_WarmBone: (0.72, 0.64, 0.50) R=0.80 M=0.0 — approved
M_Glass_TintedBronze: (0.20, 0.22, 0.22) R=0.0 M=0.0 T=0.25 — adjusted
  ← User changed base colour from (0.18, 0.20, 0.20) — glass appeared too green
```

Iterate until the user approves the full palette in writing.

---

## Material Tag → ComfyUI Prompt Bridge

Section 8 material descriptions also feed Phase 11 (ComfyUI).
For each material tag, note a short phrase that can appear in a ComfyUI
text prompt to reinforce that material in the AI-generated output.

Add a `comfy_phrase` column to Section 8 at approval time:

| Tag | Cycles params | ComfyUI phrase |
|---|---|---|
| M_Concrete_WarmBone | (0.72, 0.64, 0.50) R=0.80 | warm travertine concrete, bone white, matte |
| M_Glass_TintedBronze | (0.20, 0.22, 0.22) R=0.0 T=0.25 | tinted glass, bronze frame, reflective |
| M_Stone_Fieldstone | (0.28, 0.24, 0.18) R=0.92 | dry-stack fieldstone, natural grey-tan, rough |

These phrases are assembled into the ComfyUI prompt in Phase 11.

---

## Post-Phase Cleanup Checklist

- [ ] All mesh objects have a material assigned — no objects with no-material (grey default)
- [ ] Fallback count is zero or all fallbacks investigated and resolved
- [ ] Glass objects are translucent/reflective in test renders — not opaque
- [ ] No surface is pure white or pure black in typical lighting
- [ ] Roughness variation visible across material categories
- [ ] Section 8 of `project_prompt.md` updated with approved final values + ComfyUI phrases
- [ ] Eight test stills saved to `test_renders/materials_*.png`

---

## ▶ REVIEW GATE 8 — Cycles Materials

Present:
1. Four wide compass stills (NW, NE, SE, SW) showing full building
2. Four close-up stills showing key material details

Confirm:
- Palette matches Section 8 intent
- Glass reads correctly (not opaque)
- Metals have appropriate sheen
- Concrete reads warm and matte
- No obvious misassigned surfaces

**All approved changes must be written back to Section 8 before gate closes.**
Wait for written approval.

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
Rename: `08-cycles_materials-hermes.mkv`, `08-cycles_materials-blender.mkv`. Confirm.

[Phase 9 — Animation is currently COMMENTED OUT]

Proceed to `13_test_render_prompt.md` (Phase 10 — Rendering).
