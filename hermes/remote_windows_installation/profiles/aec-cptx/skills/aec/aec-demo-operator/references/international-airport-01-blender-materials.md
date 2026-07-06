# International Airport 01 — Blender PBR Material Palette

Cycles PBR materials for Summit International Airport scene. All use Principled BSDF unless noted.

## Material Table

| Material Tag | Base Color (RGBA) | Metallic | Roughness | Alpha | Emission Str | Notes |
|---|---|---|---|---|---|---|
| M_Solar_BIPV | (0.05, 0.05, 0.08, 1.0) | 0.6 | 0.25 | 1.0 | 0.0 | Dark blue-grey, semi-metallic. Hub roof + terminals + canopy |
| M_Glass_Clear | (0.7, 0.8, 0.9, 0.15) | 0.0 | 0.05 | 0.15 | 0.0 | Transparent structural glass. Use Glass BSDF or Transmission for Cycles |
| M_Concrete_DarkRib | (0.15, 0.14, 0.13, 1.0) | 0.0 | 0.7 | 1.0 | 0.0 | Dark charcoal structural ribs |
| M_Concrete_LightFloor | (0.55, 0.53, 0.50, 1.0) | 0.0 | 0.6 | 1.0 | 0.0 | Light grey polished floor slabs |
| M_Concrete_Apron | (0.45, 0.43, 0.40, 1.0) | 0.0 | 0.65 | 1.0 | 0.0 | Aircraft apron concrete |
| M_Aluminum_DarkBronze | (0.12, 0.09, 0.06, 1.0) | 0.9 | 0.35 | 1.0 | 0.0 | Dark bronze anodised mullions |
| M_Steel_Brushed | (0.5, 0.5, 0.5, 1.0) | 0.85 | 0.4 | 1.0 | 0.0 | Jetway bridges, fixtures |
| M_Tarmac | (0.08, 0.08, 0.08, 1.0) | 0.0 | 0.8 | 1.0 | 0.0 | Runway/taxiway asphalt |
| M_Terrain_Prairie | (0.18, 0.22, 0.08, 1.0) | 0.0 | 0.85 | 1.0 | 0.0 | Native grassland |
| M_Interior_Glow | (1.0, 0.95, 0.85, 1.0) | 0.0 | 0.5 | 1.0 | 8.0 | Warm amber emission behind glass |
| M_Aircraft_White | (0.9, 0.9, 0.92, 1.0) | 0.1 | 0.3 | 1.0 | 0.0 | White aircraft fuselage/wings |
| M_Marking_White | (0.95, 0.95, 0.95, 1.0) | 0.0 | 0.5 | 1.0 | 0.0 | Runway centerline/threshold markings |
| M_Mountain_Rock | (0.35, 0.30, 0.25, 1.0) | 0.0 | 0.8 | 1.0 | 0.0 | Brownish exposed rock, Front Range |
| M_Mountain_Snow | (0.85, 0.87, 0.92, 1.0) | 0.0 | 0.6 | 1.0 | 0.0 | Snow-capped distant peaks |
| M_Mountain_Forest | (0.12, 0.18, 0.08, 1.0) | 0.0 | 0.85 | 1.0 | 0.0 | Dark green forested foothills |

## Glass Material Pitfall (Cycles)

Do NOT use `blend_method='BLEND'` + alpha for glass in Cycles — renders opaque. Use:
- **Glass BSDF node** (simplest for clear glass): `ShaderNodeBsdfGlass`, IOR=1.52
- **Principled BSDF with Transmission Weight** (more control): `inputs['Transmission Weight'] = 0.7`

## Interior Glow Emission

Set `Emission Color` = base color + `Emission Strength` = 8.0 on Principled BSDF. Position glow planes 1-3m behind glass line to avoid reading as facade light bars.

## Object Count After Phase 4b Detail Pass

Phase 4 cleanup: removed 132 detached glass + added 9 transitions (922 exportable). Phase 4b detail: added 54 aircraft + 181 taxiway/runway objects + 4 mountains + 1 extended prairie = **2,156 total Rhino objects**. Blender objects after separation: **14** (one per material).

## Dual Mesh Resolution for OBJ Export (Critical for Large Scenes)

A single mesh resolution setting produces enormous files for scenes with both detailed buildings and large environment surfaces. The airport at uniform fine mesh was 993MB; at uniform coarse it lost building detail.

**Solution: two mesh parameter sets:**
- **Fine** (building objects): `MinimumEdgeLength=500, MaximumEdgeLength=20000, SimplePlanes=True`
- **Coarse** (environment: terrain, mountains): `MinimumEdgeLength=5000, MaximumEdgeLength=100000, SimplePlanes=True`

Select params per-material: `{"M_Terrain_Prairie", "M_Mountain_Rock", "M_Mountain_Snow", "M_Mountain_Forest"}` → coarse; everything else → fine. Result: **76MB** (vs 993MB single-resolution). 695K verts vs 8.3M.

## Hosek-Wilkie Sky Setup (Blender Cycles)

For Colorado golden hour, use `ShaderNodeTexSky`:
```python
sky = nodes.new('ShaderNodeTexSky')
sky.sky_type = 'HOSEK_WILKIE'
sky.sun_direction = (-0.85, -0.45, 0.14)  # WSW low sun (~8 deg elevation)
sky.turbidity = 4.0   # hazy golden hour (higher = warmer, more varied reflections)
sky.ground_albedo = 0.3
```
Connect through a Background node with Strength=1.2. Add Volume Scatter on World output at density=0.0008 for atmospheric haze (but see blender-pbr-at-scale-pitfalls.md — volume scatter can black out very large scenes).

**⚠ Blender 5.1 sky types:** `PREETHAM`, `HOSEK_WILKIE`, `SINGLE_SCATTERING`, `MULTIPLE_SCATTERING`. Nishita does NOT exist (raises enum error).

## Procedural Noise Texture Scales for Airport (9000m span)

Scene coordinates are in meters, terrain is 9000x8000m. Noise Scale parameter = 1/feature_size.

| Material | Noise Purpose | Scale | Feature Size |
|---|---|---|---|
| M_Terrain_Prairie (color) | Large prairie variation | 0.005 | 200m patches |
| M_Terrain_Prairie (bump) | Grass texture | 0.05 | 20m |
| M_Mountain_Rock (color) | Rock band variation | 0.003 | 333m |
| M_Mountain_Rock (bump) | Rock detail | 0.015 | 67m |
| M_Mountain_Forest (color) | Forest patches | 0.005 | 200m |
| M_Mountain_Forest (bump) | Canopy texture | 0.03 | 33m |
| M_Mountain_Snow (color) | Snow variation | 0.004 | 250m |
| M_Concrete_Apron (color) | Slab variation | 0.05 | 20m |
| M_Concrete_DarkRib (bump) | Rib texture | 0.5 | 2m |
| M_Tarmac (color) | Asphalt patches | 0.02 | 50m |

**⚠ At aerial camera distance (400m+), ALL procedural noise textures are invisible.** What matters at this distance: material color contrast, specular reflectance, atmospheric depth, interior glow strength. See `references/blender-pbr-at-scale-pitfalls.md` § "Aerial Distance Rendering" for details.

## Upgraded Material Properties (June 15, 2026 session)

Key updates from aerial rendering session:
- **M_Solar_BIPV:** Base Color (0.01, 0.015, 0.05), Metallic=0.4, Roughness=0.12, Coat Weight=1.0, Coat Roughness=0.02 — highly reflective dark panels with glass clearcoat
- **M_Glass_Clear:** Transmission Weight=0.85, Alpha=0.15, IOR=1.52, Roughness=0.02, Specular IOR Level=1.0 — proper glass transparency in Cycles
- **M_Interior_Glow:** Emission Strength=15.0 (was 8.0) — needs to be visible through glass at 400m distance
- **M_Terrain_Prairie:** dual-noise mix (dark 0.12/0.18/0.04, light 0.25/0.35/0.08) with warm golden-hour grass tones
- **M_Mountain_Rock:** atmospheric blue-grey tones (0.25/0.24/0.28 to 0.40/0.38/0.42) for distance haze effect
- **M_Aircraft_White:** Coat Weight=0.5, Coat Roughness=0.1 — glossy paint finish

## GPU Rendering Setup

**Must explicitly enable GPU — defaults to CPU even with GPUs present:**
```python
prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'CUDA'
prefs.get_devices()
for dev in prefs.devices:
    if 'NVIDIA' in dev.name:
        dev.use = True
bpy.context.scene.cycles.device = 'GPU'
```
On this machine: 2× RTX PRO 5000 72GB Blackwell. Renders 960x540 @ 128 samples in 1.5s on GPU (vs 3.5s on 24-core Threadripper CPU).

## Aircraft Mesh Template Pattern

Create once, instance many. The template mesh (57 verts, 52 faces) covers fuselage + wings + tail. For each gate, `DuplicateMesh()` + `Transform(translation * rotation)`. 54 aircraft at 57 verts each = 3,078 verts total — negligible overhead.

## ComfyUI Post-Processing Pipeline

After Blender Cycles render, enhance with ComfyUI SDXL img2img for photorealistic detail:
1. Resize render to 1024x576 (SDXL-friendly) and copy to `C:\Users\test\ComfyUI\input\`
2. Use `sdxl_img2img.json` workflow with **denoise=0.65-0.80** (NOT 0.40-0.50 which is too subtle)
3. Architecture-specific prompts: explicitly describe building shape, materials, environment, lighting. Add anti-drift negatives for complex forms
4. First run after server start: submit ONE job first to prime model (60-120s load), then batch. Multi-submit during load hangs server
5. Remove `_comment` key from workflow JSON before submitting
6. At denoise ≥0.75, SDXL may reinterpret building shapes — generate 4-6 seeds and pick best

See `references/comfyui-render-enhancement-pipeline.md` for full details including tested denoise table.

## Taxiway Geometry Pattern

Centerline `Polyline.ToNurbsCurve()` → `Curve.Offset(plane, ±halfWidth, tolerance, Sharp)` → `Brep.CreateFromLoft([left, right], Straight)`. Works reliably for straight and curved taxiways. Width parameter controls taxiway (20m) vs runway (45m).
