# Blender PBR Materials at Architectural Scale — Pitfalls & Fixes

Discovered June 2026 during Empire State Building render (443m tall, 5,083 objects, 9 materials).

## The Scale Problem

Blender's procedural noise textures operate in object/world space. When the scene is hundreds of meters tall, default noise scales produce features that are either invisible or scene-spanning.

**Rule of thumb for noise Scale parameter:**
- `feature_size_meters ≈ scene_extent / noise_scale`
- A 443m building with Noise Scale 3.0 → features are ~150m wide → invisible variation
- A 443m building with Noise Scale 40.0 → features are ~11m wide → single window bay, still too coarse

### Limestone/Stone texture scales for skyscrapers (443m class)

| Noise Layer | Purpose | Scale | Detail | Notes |
|---|---|---|---|---|
| Large variation | Tier-level weathering | 15–25 | 8 | Features ~20–30m (visible per setback) |
| Panel detail | Panel-scale variation | 150–250 | 14 | Features ~2m (individual panels) |
| Bump height | Stone grain | 400–600 | 16 | Features <1m (tactile roughness) |

### Bump map strength must scale too

Default bump strength (0.25) and distance (0.02) are calibrated for small objects. At building scale:
- `Strength`: 0.6–1.0
- `Distance`: 0.05–0.15
- Without this, surfaces read as perfectly flat regardless of noise complexity

### Color ramp contrast

Procedural color ramps with positions at 0.25/0.75 produce very subtle variation. For visible material differentiation at distance:
- Tighten ramp: dark stop at 0.35, light stop at 0.65
- Increase color difference: e.g. weathered (0.45, 0.40, 0.33) vs clean (0.88, 0.85, 0.78)

## Metallic Materials Need Environment to Reflect

Materials with `Metallic=1.0` (gold, chrome, steel, aluminum) are 100% reflective — their color only appears when reflecting something. If the environment is uniform or low-contrast, metallics appear flat/muddy.

**Hosek-Wilkie sky problem:** At low turbidity (2–3), the sky is fairly uniform blue, giving metallics almost nothing to reflect. Result: gold crown renders as olive/dark-green instead of gold.

### Fixes for metallic materials in procedural environments

1. **Use a gradient sky instead of Hosek-Wilkie** for dramatic scenes:
   - Ground: warm dark (0.15, 0.08, 0.04)
   - Horizon: hot sunset (1.0, 0.6, 0.2)
   - Mid-sky: golden (0.9, 0.5, 0.25)
   - Upper: transition blue (0.4, 0.5, 0.8)
   - Zenith: deep blue (0.08, 0.12, 0.35)
   - Background Strength: 3.0–4.0

2. **Add emission as fallback** for critical metallic surfaces:
   - Crown gold: `Emission Color = (1.0, 0.85, 0.2)`, `Emission Strength = 0.3–0.5`
   - This ensures the material reads as gold even when reflections are weak
   - Keep emission subtle — it supplements reflections, not replaces them

3. **Increase Hosek-Wilkie turbidity to 5–8** if keeping procedural sky:
   - Higher turbidity = warmer, more varied sky = better metallic reflections
   - `sun_direction` Z component should be 0.05–0.10 (near horizon) for golden hour

## Volume Scatter Causes Black Renders at Scale

World-level Volume Scatter with even tiny density (0.0003) produces completely black frames when camera-to-subject distance is hundreds of meters.

**Math:** optical_depth = distance × density = 300m × 0.0003 = 0.09. This seems low, but Cycles traces many bounce paths through the volume. Combined with multiple scattering iterations, the scene goes black.

**Rule:** Do NOT use Volume Scatter on World for scenes larger than ~50m. For atmospheric haze at architectural scale, use:
- Mist pass in compositor (post-process depth fog)
- Or a very large transparent box with Volume Scatter at density < 0.00005
- Or just rely on the gradient sky color ramp fading to haze

## Glass Windows at Scale (Thousands of Instances)

### Linked mesh duplicates pattern

For 5,000+ windows, use a single template mesh shared across all instances:

```python
# Create template once
win_mesh = bpy.data.meshes.new('Win_template')
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co.x *= 1.8   # window width
    v.co.y *= 0.15   # inset depth
    v.co.z *= 2.6    # window height
bm.to_mesh(win_mesh)
bm.free()

# Assign material to the MESH, not each object
win_mesh.materials.append(mat_glass)

# Create instances (all share the same mesh data)
for i in range(n_windows):
    obj = bpy.data.objects.new(f'win_{i}', win_mesh)
    obj.location = calculated_position
    collection.objects.link(obj)
```

**Memory benefit:** 5,000 window objects sharing 1 mesh = ~50x less mesh data than 5,000 unique meshes.

**Material assignment:** Assign material to the template mesh AFTER all objects are created. All linked duplicates inherit the material automatically.

### Glass shader for architectural windows (dark reflective)

Principled BSDF approach (more reliable than manual Mix Shader):
```python
bsdf.inputs['Base Color'] = (0.01, 0.015, 0.025, 1)  # near-black interior
bsdf.inputs['Metallic'] = 0.0
bsdf.inputs['Roughness'] = 0.02                        # near-mirror
bsdf.inputs['Specular IOR Level'] = 1.5                # high reflectivity
bsdf.inputs['Coat Weight'] = 1.0                       # clearcoat for extra reflection
bsdf.inputs['Coat Roughness'] = 0.01
# Optional: subtle cold interior emission
bsdf.inputs['Emission Color'] = (0.02, 0.03, 0.06, 1)
bsdf.inputs['Emission Strength'] = 0.3
```

## Aerial Distance Rendering (400m+ Camera)

At aerial/bird's-eye distances (camera 400m+ from subject), procedural noise textures are completely invisible regardless of scale settings. What matters at this distance:

1. **Color contrast between materials** — different zones must read as visually distinct colors
2. **Material reflectance** — solar panels, glass, and metallic surfaces need specular response to catch sky
3. **Atmospheric depth** — mountains must be lighter/hazier than foreground (atmospheric perspective)
4. **Interior glow emission strength** — **3.0 is correct for aerial views.** 15.0 causes completely blown-out white strips that dominate the image. At 400m+ camera distance, even 3.0 reads clearly through glass.
5. **Sky quality and sun warmth** — these dominate the mood more than any material detail

**Don't waste time on:** bump maps, fine noise detail, micro-texture, displacement. They are pixel-invisible at this camera distance. Focus budget on color, reflectance, lighting, atmosphere, and compositor post-processing.

### Camera rotation (avoid manual trig)

Manual trigonometry for camera rotation is error-prone and caused a black-render debug cycle. Use mathutils:

```python
from mathutils import Vector
cam_loc = Vector((450, -400, 220))
target = Vector((0, 0, 20))
direction = target - cam_loc
rot_quat = direction.to_track_quat('-Z', 'Y')
cam.rotation_euler = rot_quat.to_euler()
```

The `-Z` axis is the camera look direction in Blender; `Y` is the up reference.

### Volume scatter at aerial scale

World-level Volume Scatter kills renders at aerial distance:
- Density 0.001 → scene too dark (confirmed at 600m camera-to-subject)
- Density 0.0002 → borderline, still eats noticeable light
- **Recommendation:** Remove Volume Scatter entirely for aerial renders. Use Mist compositor pass for atmospheric fog instead — it's post-process so it doesn't darken the 3D lighting.

**For archviz quality at aerial scale, improve the Blender render directly — do not rely on AI img2img post-processing.** SDXL img2img and ControlNet fundamentally cannot understand 3D geometry and will hallucinate generic forms that look nothing like the actual model. At denoise levels low enough to preserve form (0.3–0.5), the enhancement is negligible. At denoise levels high enough to be photorealistic (0.75+), the building shape morphs into something generic. The honest path: better materials, HDRI/procedural sky, atmospheric compositing, and Cycles render quality.

## Blender 5.1 Sky Texture Types

**Blender 5.1 does NOT have Nishita sky.** Available `ShaderNodeTexSky.sky_type` values:
- `PREETHAM`
- `HOSEK_WILKIE` (best for golden hour — use turbidity 4.0+, low sun_direction Z)
- `SINGLE_SCATTERING`
- `MULTIPLE_SCATTERING`

Attempting `sky.sky_type = 'NISHITA'` raises `enum not found` error.

## GPU Rendering Must Be Explicitly Enabled

Even when NVIDIA GPUs are present and `device.use = True`, rendering defaults to CPU unless BOTH conditions are met:

```python
# 1. Set compute device type (required even if devices show up)
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'  # or 'OPTIX'
prefs.get_devices()
for dev in prefs.devices:
    if 'NVIDIA' in dev.name:
        dev.use = True

# 2. Set scene device (separate from preferences)
bpy.context.scene.cycles.device = 'GPU'
```

Without step 1, `compute_device_type` stays `'NONE'` and Cycles silently falls back to CPU. This was confirmed on dual RTX PRO 5000 72GB Blackwell — GPUs showed `use=True` but `compute_device_type` was `'NONE'` until explicitly set.

## Glass Transparency in Blender 5.1

For glass in Cycles (Blender 5.1), use `Transmission Weight` on Principled BSDF — NOT `Alpha` alone:

```python
bsdf.inputs["Transmission Weight"].default_value = 0.85  # glass transparency
bsdf.inputs["Alpha"].default_value = 0.15                 # also set for render passes
bsdf.inputs["IOR"].default_value = 1.52                   # glass IOR
bsdf.inputs["Roughness"].default_value = 0.02             # near-mirror for reflections
bsdf.inputs["Specular IOR Level"].default_value = 1.0     # maximum reflectivity
```

`Alpha` alone without `Transmission Weight` renders opaque in Cycles. `blend_method='BLEND'` is an EEVEE-only property and does nothing in Cycles.

## Blender 5.1 Compositor API Changes

**`scene.node_tree` does NOT exist in Blender 5.1.** The compositor node tree is accessed via:

```python
scene.use_nodes = True
cng = scene.compositing_node_group  # may be None initially

if cng is None:
    cng = bpy.data.node_groups.new("Compositing", "CompositorNodeTree")
    scene.compositing_node_group = cng

tree = cng  # use this as you'd use scene.node_tree in older Blender
```

**Glare node properties are now INPUT SOCKETS in 5.1.** You cannot set `glare.glare_type` or `glare.quality` — they raise `AttributeError`. Enum values use **Display Names** not identifiers:

```python
glare = tree.nodes.new("CompositorNodeGlare")
for inp in glare.inputs:
    if inp.name == "Type":       inp.default_value = 'Fog Glow'    # NOT 'FOG_GLOW'
    elif inp.name == "Quality":  inp.default_value = 'High'         # NOT 'HIGH'
    elif inp.name == "Threshold": inp.default_value = 2.0
    elif inp.name == "Size":     inp.default_value = 6.0
    elif inp.name == "Strength": inp.default_value = 0.5
```

**Glare outputs changed too:** `['Image', 'Glare', 'Highlights']` — use `glare.outputs["Image"]` for the combined result.

### ⛔ MORE REMOVED/CHANGED NODES in Blender 5.1 (discovered June 15 2026)

**`CompositorNodeComposite` — REMOVED.** Use `CompositorNodeViewer` for preview and `CompositorNodeOutputFile` for file output. Note: `render(write_still=True)` still writes to `scene.render.filepath` but does NOT go through the compositor pipeline — compositor output requires FileOutput node or Viewer.

**`CompositorNodeMixRGB` — REMOVED.** Use `CompositorNodeAlphaOver` for compositing two images. For color mixing by factor (e.g. Mist pass → fog color blend), you need a workaround since no direct replacement exists. Best alternative: use the Alpha Over node's Factor input, or use ColorBalance gain to approximate warm fog tinting.

**`CompositorNodeColorBalance` — PROPERTIES REMOVED.** `correction_method`, `lift`, `gamma`, `gain` are no longer object attributes. They are now INPUT SOCKETS:

```python
cb = tree.nodes.new("CompositorNodeColorBalance")
for inp in cb.inputs:
    if inp.name == "Type" and inp.type == "MENU":
        inp.default_value = 'Lift/Gamma/Gain'
    elif inp.name == "Lift" and inp.type == "RGBA":
        inp.default_value = (0.95, 0.95, 1.02, 1)   # cool shadows
    elif inp.name == "Gamma" and inp.type == "RGBA":
        inp.default_value = (1.02, 1.0, 0.95, 1)    # warm midtones
    elif inp.name == "Gain" and inp.type == "RGBA":
        inp.default_value = (1.10, 1.02, 0.88, 1)   # golden highlights
```

Note: ColorBalance has DUPLICATE input names (e.g. two "Lift" inputs — one VALUE, one RGBA). Filter by `inp.type == "RGBA"` for color grading.

**`CompositorNodeOutputFile` — `base_path` property REMOVED.** The file output path is configured differently in 5.1 (check available attributes).

### Available compositor nodes (confirmed working in Blender 5.1)

| Node | Status |
|---|---|
| `CompositorNodeRLayers` | ✅ Works |
| `CompositorNodeGlare` | ✅ Works (settings via inputs) |
| `CompositorNodeColorBalance` | ✅ Works (settings via inputs) |
| `CompositorNodeAlphaOver` | ✅ Works |
| `CompositorNodeViewer` | ✅ Works (replaces Composite) |
| `CompositorNodeOutputFile` | ✅ Works (no base_path) |
| `CompositorNodeCombineColor` | ✅ Works |
| `CompositorNodeZcombine` | ✅ Works |
| `CompositorNodeComposite` | ❌ REMOVED |
| `CompositorNodeMixRGB` | ❌ REMOVED |
| `CompositorNodeMix` | ❌ Does not exist |

### Compositor post-processing pipeline for aerial archviz (Blender 5.1)

Proven node chain: RenderLayers → Glare(Fog Glow, threshold=1.5) → ColorBalance(golden hour grade) → Viewer + FileOutput

For the mist fog pass:
```python
vl = scene.view_layers["ViewLayer"]
vl.use_pass_mist = True
scene.world.mist_settings.start = 200    # meters from camera
scene.world.mist_settings.depth = 4000   # full fog distance
scene.world.mist_settings.falloff = 'QUADRATIC'
```

Color balance golden hour grading (via RGBA input sockets):
- Lift (shadows): `(0.95, 0.95, 1.02, 1)` — slightly cool
- Gamma (midtones): `(1.02, 1.0, 0.95, 1)` — warm shift
- Gain (highlights): `(1.10, 1.02, 0.88, 1)` — golden highlights

**⛔ Mist pass fog blending:** Since MixRGB is gone, you cannot directly blend fog color by mist factor. Alternatives: (a) Use AlphaOver with mist driving the factor, (b) push the warm fog look entirely via ColorBalance gain, (c) Use a gradient sky that already has warm horizon tones (preferred for aerial archviz).

### Hosek-Wilkie vs HDRI for aerial golden hour

Hosek-Wilkie procedural sky at low sun angles (8-12° elevation) produces dim, neutral lighting. After 12 render iterations (v1-v12, June 15 2026), the scene stayed at 3-4.5/10 quality despite sun energy up to 20.0 and sky strength up to 5.0. **The single most impactful upgrade for aerial archviz is an HDRI environment map** — it simultaneously fixes:
1. Sky appearance (clouds, vivid gradients)
2. Environmental lighting (warm ambient bouncing onto all surfaces)
3. Reflections on glass and metallic surfaces (solar panels, steel)
4. Atmospheric mood and depth

Download a golden hour HDRI from Poly Haven (free, CC0) and use as world environment texture. This is more effective than any combination of procedural sky + sun energy + compositor grading.

## Blender API Enum Pitfalls

| Correct | Wrong | Context |
|---|---|---|
| `HOSEK_WILKIE` | `HOSEKWILKIE`, `NISHITA` | `ShaderNodeTexSky.sky_type` (Nishita removed in 5.1) |
| `SINGLE_SCATTERING` | `SINGLE` | `ShaderNodeTexSky.sky_type` |
| `OPENIMAGEDENOISE` | `OIDN` | `scene.cycles.denoiser` |
| `AgX - Medium High Contrast` | `Medium High Contrast` | `scene.view_settings.look` |
| `CUDA` | `NONE` (default!) | `preferences.compute_device_type` — must be set explicitly |
| `'Fog Glow'` | `'FOG_GLOW'` | Glare node Type input (display name, not identifier) |
| `'High'` | `'HIGH'` | Glare node Quality input (display name) |
| `'Lift/Gamma/Gain'` | `'LIFT_GAMMA_GAIN'` | ColorBalance Type input (display name) |

## Render Settings for Quality (Proven June 2026)

### Test render (fast feedback)
- Samples: 128
- Resolution: 75% of target (1440×810 for 1920×1080 target)
- Denoiser: OPENIMAGEDENOISE
- Max bounces: 8

### Final render (quality)
- Samples: 256+
- Resolution: 100% (1920×1080)
- Denoiser: OPENIMAGEDENOISE
- Max bounces: 12
- Diffuse/Glossy bounces: 4
- Transmission bounces: 8
- Color depth: 16-bit PNG
- View transform: AgX with Medium High Contrast look
- Film exposure: 1.2–1.4 (slightly bright for architectural)
- Film transparent: False (ensure sky renders)

### GPU acceleration
```python
prefs = bpy.context.preferences.addons.get('cycles')
if prefs:
    cprefs = prefs.preferences
    for dtype in ['OPTIX', 'CUDA', 'HIP', 'ONEAPI']:
        try:
            cprefs.compute_device_type = dtype
            cprefs.get_devices()
            if any(d.type != 'CPU' for d in cprefs.devices):
                for d in cprefs.devices:
                    d.use = True
                scene.cycles.device = 'GPU'
                break
        except:
            continue
```
Note: Try OPTIX before CUDA — it's faster on RTX cards. Fall through to CPU if nothing works.

## Diagnostic: Why Is My Render Black/Flat?

Checklist when render looks wrong:
1. **All black?** → Check for Volume Scatter on World, or camera inside geometry, or film_transparent=True with no background
2. **Materials all same color?** → Noise texture scales are wrong for scene size (see scale table above)
3. **Metallics look olive/gray?** → Environment too uniform for reflections (use gradient sky or HDRI)
4. **No shadows?** → Sun light energy too low, or sun rotation pointing away from scene
5. **Crown/gold looks green?** → Metallic surface reflecting uniform blue sky = desaturated olive. Add emission fallback.
6. **Windows don't reflect?** → Need Specular IOR Level > 1.0, or Coat Weight for extra layer
7. **Ground plane invisible?** → Check Z position (should be at 0 or -0.5, not buried)
8. **Compositor `AttributeError: node_tree`?** → Blender 5.1 uses `scene.compositing_node_group`, not `scene.node_tree`. See Blender 5.1 Compositor API Changes section above.
9. **Glare node `AttributeError: glare_type`?** → Blender 5.1 moved Glare settings to input sockets. Use `glare.inputs["Type"].default_value = 'Fog Glow'` (Display Name, not 'FOG_GLOW').
10. **Interior glow blown out (white strips)?** → Emission Strength too high. Use 3.0 for aerial views, not 15.0.
11. **`CompositorNodeMixRGB` or `CompositorNodeComposite` error?** → Both REMOVED in Blender 5.1. Use AlphaOver for mixing, Viewer+OutputFile for output. See "MORE REMOVED/CHANGED NODES" section.
12. **ColorBalance `correction_method` AttributeError?** → Properties moved to input sockets in 5.1. Use `inp.name == "Type"` menu input and RGBA socket inputs for Lift/Gamma/Gain.
13. **Scene still dark despite high sun energy (15-20)?** → Hosek-Wilkie sky produces dim ambient light at low sun angles. Use an HDRI environment map instead. Volume Scatter at any density also kills light at aerial scale — remove it entirely.
