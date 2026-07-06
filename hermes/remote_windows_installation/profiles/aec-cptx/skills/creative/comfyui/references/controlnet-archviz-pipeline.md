# ControlNet for Architectural Visualization — Normal Map Pipeline

## Problem

When using SDXL img2img on 3D renders of architecture, the model either:
- Barely changes the image (low denoise) → still looks CG
- Invents a completely different building (high denoise) → doesn't match the designed form

Users who designed a specific building care about form fidelity above all else.
"They all look wrong" = the AI is hallucinating generic buildings.

## Solution: Normal Map + ControlNet Depth (txt2img)

Render a **surface normal map** from the 3D scene and use it as the ControlNet
conditioning image for a **txt2img** (NOT img2img) generation.

### Why Normal Maps Beat Depth Maps for Architecture

At aerial camera distances (>300m), depth maps have almost no contrast because:
- Building height (20-50m) vs camera distance (600m) = <10% depth variation
- Ground, building, and nearby structures all compress into the same depth value
- Only mountains/sky show meaningful depth separation

Normal maps encode **surface orientation** (which way each face points), so they
reveal:
- Roof curvature and structural ribs
- Wall vs floor vs ceiling transitions
- Aircraft silhouettes (tiny but present)
- Mountain ridge detail
- All architectural detail invisible in depth

### Rendering the Normal Map from Blender

```python
# In Blender Python
scene.view_layers["ViewLayer"].use_pass_normal = True
# Compositor: RenderLayers.Normal → Viewer Node
# Save via: bpy.data.images["Viewer Node"].save_render(path)
```

Resolution: Match SDXL input (1024x576 for 16:9 aerial).
Samples: 1 is fine — normals don't need path tracing.

### Also Render a Depth Map (useful for combined approaches)

Use inverse depth (1/d) for better near-range contrast:
```python
# After getting raw depth values from Viewer Node:
inv = 1.0 / depth_value
normalized = (inv - min_inv) / (max_inv - min_inv)  # 0-1 range
```

### Ground-Truth Depth from Blender ShaderNodeCameraData (proven June 2026)

For interior/close-range scenes (VP studios, building interiors, street-level
views), ground-truth depth maps from Blender produce far better ControlNet
conditioning than MiDaS-estimated depth. The technique:

1. Create a depth material using `ShaderNodeCameraData` "View Distance" →
   `ShaderNodeMapRange` (near=5m→1.0 white, far=150m→0.0 black) →
   `ShaderNodeEmission` (strength=1.0) → Material Output.
2. Assign this material to ALL mesh objects (save originals first).
3. Configure scene: Cycles, 1 sample, ALL bounces=0, world strength=0,
   film_transparent=True, no denoising.
4. Render to 16-bit PNG at the same resolution and camera position as the
   beauty render.
5. Upload BOTH the beauty render AND the depth map to ComfyUI. Feed beauty
   to VAEEncode (img2img latent) and depth to ControlNetApplyAdvanced.

**Key Blender 5.1 pitfall:** `ShaderNodeMapRange` does NOT have a `use_clamp`
property in Blender 5.1 — clamping is on by default. Do not set it
explicitly or you'll get a compile error.

**When to use ground-truth depth vs normal maps:**
- **Aerial/exterior at >300m distance:** Use normal maps (depth has almost no
  building-vs-ground contrast at that range). See normal map section above.
- **Interior/close-range <150m:** Use ground-truth depth maps (depth variation
  is meaningful and ControlNet can interpret it well).
- **Hybrid:** For exterior hero shots at 50-100m distance, ground-truth depth
  works well with denoise 0.65-0.70 and CN strength 0.72-0.78 (see V4 approach
  below).

### ComfyUI Workflow (API format)

```
LoadImage(normal_map) → ControlNetApplyAdvanced → KSampler → VAEDecode → SaveImage
                              ↑
CheckpointLoader(SDXL) → CLIPTextEncode(prompt)
                       → CLIPTextEncode(neg)
ControlNetLoader(depth-sdxl) ↗
EmptyLatentImage(1024x576) → KSampler.latent_image
```

Key: Use **EmptyLatentImage** (txt2img), NOT VAEEncode of the render (img2img).
The ControlNet provides ALL the structural guidance; img2img just fights it.

### Optimal Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| ControlNet strength | 0.75-0.80 | Sweet spot. 0.90 = illustration look. 0.65 = form drift |
| ControlNet end_percent | 0.9 | Let final steps refine freely |
| CFG | 7.0-8.0 | Standard SDXL range |
| Steps | 35 | Good quality/speed balance |
| Sampler | dpmpp_2m + karras | Reliable for architecture |
| Denoise | 1.0 | Full txt2img — NOT img2img denoise |

### Prompt Strategy for Architecture

Include in positive prompt:
- Building material description (solar panels, glass, steel, concrete)
- Specific aircraft types (Boeing 737, Airbus A320) for scale
- Geographic context (Rocky Mountains, Colorado, prairie)
- Camera/lens spec (Canon EOS R5, 24mm, f/8) for photographic look
- "aerial photograph" not "aerial render"

Include in negative prompt:
- "CG render, 3D render" to push away from synthetic look
- Wrong building shapes: "four arms, X-shape" if Y-shape is intended
- "night, dark, underexposed" if golden hour is wanted

### Results Observed

| Approach | Photorealism | Form Fidelity | Best Score |
|----------|-------------|---------------|------------|
| Pure img2img (d=0.80) | 8/10 | 3/10 | 8/10 but wrong building |
| ControlNet depth (RGB as input) | 5/10 | 5/10 | Inconsistent |
| ControlNet depth (real depth map) | 5/10 | 6/10 | Depth too flat |
| ControlNet depth (inverse depth) | 5/10 | 6.5/10 | Better but still flat |
| **ControlNet depth (normal map)** | **8/10** | **8.5/10** | **Best overall** |
| Hybrid (CN+img2img, same image, low d) | 3.5/10 | 7/10 | Double conditioning, flat output |
| **Hybrid (CN+img2img, separate images, high d)** | **8/10** | **8/10** | **Best for interiors — V4 approach** |

### Seed Sensitivity

Results vary significantly by seed. Always run 6-10 seeds at the optimal
strength and pick the best. File size correlates loosely with detail (larger
PNG = more visual information = usually better).

### Dual-Image High-Denoise Approach (V4 — proven June 2026)

**Problem:** At denoise 0.42-0.50 with ControlNet depth, all seeds produce
visually identical images. The diffusion barely touches the input — the
ControlNet locks geometry so firmly that there's nothing left to transform.
Users see "flat" outputs that "all look the same."

**Solution:** Push denoise to 0.65-0.70. The depth map still constrains the
3D form (CN strength 0.72-0.78), but the high denoise gives SDXL room to
actually paint atmosphere, texture, and lighting. This is the key
breakthrough for interior/VP studio scenes.

**Essential: per-seed prompt variation.** Same prompt + different seeds at
high denoise still produces similar images. Each seed MUST get a distinctly
different prompt emphasis:
- Exterior: golden hour / blue hour dusk / overcast moody
- Interior LED volume: sci-fi alien landscape / golden desert / stormy ocean
- Control room: monitor glow / red alert / night shoot mode
- Dock: warm shafts / morning mist / night work lights

**Parameters that work:**

| Parameter | Value | Notes |
|-----------|-------|-------|
| Denoise | 0.65-0.70 | CRITICAL — 0.42-0.50 = identical images |
| CN strength | 0.72-0.78 | Slightly lower than txt2img approach |
| CN end_percent | 0.80-0.85 | Release ControlNet before final steps |
| Steps | 30 | dpmpp_2m + karras |
| CFG | 7.5 | |
| Seeds | 3+ per view | Each with unique prompt emphasis |

**Workflow (API format):**

```
LoadImage(beauty) → VAEEncode → latent ──────────────────────┐
LoadImage(depth) → ControlNetApplyAdvanced ────┐              │
CheckpointLoader(SDXL) → CLIPTextEncode(pos) ───┤              │
                      → CLIPTextEncode(neg) ────┘              │
ControlNetLoader(depth-sdxl) ↗                                │
                                                              ↓
KSampler(model, cn_pos, cn_neg, latent, denoise=0.68) → VAEDecode → SaveImage
```

**Why this beats plain img2img:** Plain img2img at any denoise has no
geometric constraint — high denoise invents a different building. The
ControlNet depth map provides the geometric anchor that lets you push
denoise high enough for real transformation without losing the designed form.

**User expectation:** Users will notice if outputs are visually identical
across seeds. Always verify with `md5sum` or visual inspection that seeds
produce genuinely different images before presenting results. Low denoise
+ same prompt = identical hashes with imperceptible pixel differences — this
is a failure mode, not a feature.

### Blender 5.1 API Notes

- Compositor node tree: `scene.compositing_node_group` (not `scene.node_tree`)
- Must create: `bpy.data.node_groups.new("name", "CompositorNodeTree")`
- `CompositorNodeComposite` → removed, use `CompositorNodeViewer` or `CompositorNodeOutputFile`
- `CompositorNodeMixRGB` → removed, use `CompositorNodeAlphaOver`
- `CompositorNodeMapRange` → removed, normalize in Python instead
- `CompositorNodeGlare` → settings via input sockets, not properties
  - `.glare_type` → input "Type" = 'Fog Glow' (display name, not enum)
  - `.quality` → input "Quality" = 'High'
- `CompositorNodeColorBalance` → settings via input sockets
  - `.correction_method` → input "Type" = 'Lift/Gamma/Gain'
  - Lift/Gamma/Gain are RGBA input sockets (find by name + type == "RGBA")
- `CompositorNodeOutputFile` → no `base_path` attribute
- Sky texture: no 'NISHITA' type, options are 'PREETHAM', 'HOSEK_WILKIE', 'SINGLE_SCATTERING', 'MULTIPLE_SCATTERING'
- GPU: `prefs.compute_device_type = 'CUDA'`, then `prefs.get_devices()`, then enable NVIDIA devices
- Color management: AgX available as view_transform, look names use display names not enum
