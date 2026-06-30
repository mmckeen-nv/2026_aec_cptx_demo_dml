# ComfyUI Render Enhancement Pipeline

Enhance 3D architectural renders (from Blender Cycles) into photorealistic hero images using ComfyUI SDXL img2img.

## ⚠ Fundamental Limitation: AI Post-Processing vs Source Quality

**Discovered June 15, 2026 after 23 variations across 3 approaches (img2img, ControlNet depth, hybrid):**

SDXL img2img and ControlNet work from 2D pixel data — they have zero understanding of 3D geometry. For complex architectural forms (Y-shaped terminals, multi-arm buildings, distinctive rooflines), this means:
- At low denoise (0.3–0.5): enhancement is negligible — output still looks like a CG render
- At medium denoise (0.65–0.75): atmosphere improves but building shape begins to drift toward generic forms
- At high denoise (0.80+): dramatic photorealism but the building morphs into something SDXL thinks a "futuristic airport" looks like — losing the actual design

**The honest path to a good architectural render is improving the Blender scene itself:**
1. Better PBR materials with proper color contrast (not micro-textures — invisible at aerial distance)
2. Physically-based sky (Hosek-Wilkie with high turbidity for golden hour)
3. GPU rendering with denoising (512 samples + OptiX/OIDN denoiser)
4. Compositor post-processing (glare, color grading, mist pass for distance fog)
5. AgX color management with exposure tuning

**When to use ComfyUI anyway:** It IS useful for (a) upscaling via ESRGAN 4x, (b) light texture enhancement at denoise ≤0.35 as a final polish pass after the Blender render is already good, (c) generating concept/mood exploration variants early in design before the model is detailed.

## Pipeline Overview

```
Rhino (geometry) → OBJ Export → Blender (PBR + Cycles render) → ComfyUI (img2img enhancement) → Hero images
```

The Blender render provides accurate geometry, camera framing, lighting direction, and material zones. ComfyUI's img2img adds photorealistic texture detail, atmospheric effects, and visual polish that Cycles alone can't achieve at low sample counts.

## Setup (verified June 15, 2026 on this machine)

- **ComfyUI version:** 0.24.0
- **Install location:** `C:\Users\test\ComfyUI`
- **comfy-cli:** 1.10.4 (installed via `uv tool install comfy-cli`)
- **GPUs:** 2× NVIDIA RTX PRO 5000 72GB Blackwell (142GB total VRAM)
- **Models available:** `sd_xl_base_1.0.safetensors`, ControlNet depth SDXL
- **Port:** 8188 (default)

### Launch sequence
```bash
comfy --skip-prompt launch --background
sleep 15
curl -s http://127.0.0.1:8188/system_stats  # verify
```

## img2img Workflow for Architectural Renders

Use the skill workflow `sdxl_img2img.json` from `creative/comfyui/workflows/`.

### Input image preparation (CRITICAL)

**Resize to SDXL-friendly resolution BEFORE submitting.** SDXL works best at 1024px on the long edge. A 1920x1080 input caused ComfyUI to hang completely (server became unresponsive, requiring restart). Resize to **1024x576** (16:9) using PIL:

```python
from PIL import Image
img = Image.open("hero_render.png").resize((1024, 576), Image.LANCZOS)
img.save("C:/Users/test/ComfyUI/input/render_1024.png")
```

ComfyUI's LoadImage node expects images in `C:\Users\test\ComfyUI\input\`. Copy/resize the Blender render there before submitting. Output images land in `C:\Users\test\ComfyUI\output\` with the `filename_prefix` you set.

### Recommended parameters for architectural renders

| Parameter | Value | Why |
|---|---|---|
| **denoise** | **0.65–0.80** | The critical parameter. See Denoise Tuning below |
| steps | 30–40 | Architecture needs more steps for clean lines |
| cfg | 7.0–8.0 | Strong guidance keeps buildings coherent |
| sampler | dpmpp_2m | Best balance of speed and quality |
| scheduler | karras | Slightly sharper than normal for hard edges |

### Denoise Tuning (tested June 15, 2026)

This is the most important parameter. Tested on airport Y-shaped terminal render:

| Denoise | Quality | Form Preservation | Verdict |
|---------|---------|-------------------|---------|
| 0.45–0.50 | 4.5/10 | Perfect form | **Too low** — barely changes image, still looks like raw CG |
| 0.65 | 5-6/10 | Good form | Improved atmosphere but still reads as enhanced 3D render |
| 0.70 | 6-7/10 | Acceptable | Good balance for form-critical renders |
| 0.75 | 5.5/10 | **Form drift** | Lost Y-shape, became crescent. Seed-dependent |
| **0.80** | **8.0/10** | Moderate drift | **Best overall** — "competition-quality" atmosphere, mountains, golden hour, aircraft visible. Some geometry reinterpretation |

**Recommendation:** Start at **0.70** for form-critical renders, **0.80** for atmosphere-critical renders. Always generate 4-6 seeds at each denoise level and pick the best. Form drift at 0.75+ is seed-dependent — some seeds preserve form, others don't.

**⚠ The 0.40-0.50 range does NOT work for architectural enhancement.** It was originally assumed to be the sweet spot but testing showed it produces negligible improvement over the raw Blender render. The model needs ≥0.65 denoise to meaningfully restyle surfaces and add atmospheric effects.

### Prompt template for airports/large buildings

```
stunning photorealistic aerial photograph of [BUILDING DESCRIPTION with explicit shape],
[N] distinct [concourse/wing] arms extending at [angle] from central [hub/core],
[MATERIAL DETAILS], [ENVIRONMENTAL CONTEXT like Rocky Mountain backdrop],
golden hour sunset light from [direction], warm amber glow, long dramatic shadows,
[AIRCRAFT/VEHICLES], atmospheric haze, volumetric god rays,
professional aerial architectural photography, Canon EOS R5, 24mm, f/8,
award-winning architecture magazine cover, 8k ultra sharp detail
```

**Form preservation trick:** Explicitly describe the building's geometric shape in the prompt ("Y-shaped", "three arms at 120 degrees") AND add shape-drift negations to the negative prompt ("single arm, two arms, curved building, crescent shape"). This helps SDXL maintain the intended form at higher denoise values.

### Negative prompt (architecture-specific)
```
cartoon, anime, drawing, illustration, painting, sketch, low quality, blurry, noisy,
distorted, deformed, ugly, text, watermark, oversaturated, flat lighting, unrealistic,
toy, miniature, tilt-shift, CG render, 3D render, fake, plastic,
[ANTI-DRIFT SHAPES: single arm, two arms, curved building, crescent shape]
```

## Critical Pitfall: First Model Load Hangs Server

When SDXL loads for the first time after server start, the `/api/prompt` POST blocks for 60-120s. But worse: **submitting multiple jobs while the model is loading causes ComfyUI to become completely unresponsive** — the server hangs, stops answering `/system_stats`, and requires a full restart.

**Solution — prime the model first:**

1. After server start, submit ONE simple job (e.g. 8-step txt2img) and wait for it to complete.
2. Only then submit img2img or batch jobs.
3. Always use `timeout=600` on `requests.post()` for the first submission.

**Server recovery when hung:**
```bash
comfy --skip-prompt stop
sleep 5
comfy --skip-prompt launch --background
sleep 15
curl -s http://127.0.0.1:8188/system_stats  # verify
```

## Submission Script Pattern (proven)

The `comfyui` skill's `run_workflow.py` has a 120s submit timeout that is too short for first model load. Use a custom Python script:

```python
import json, requests, time, os, copy

HOST = "http://127.0.0.1:8188"
with open("workflow.json") as f:
    workflow = json.load(f)

# CRITICAL: Remove _comment key — ComfyUI rejects non-numeric top-level keys
workflow.pop("_comment", None)

# Inject parameters
workflow["1"]["inputs"]["image"] = "render_1024.png"
workflow["3"]["inputs"]["denoise"] = 0.70
workflow["3"]["inputs"]["seed"] = 12345
workflow["3"]["inputs"]["steps"] = 35
workflow["3"]["inputs"]["cfg"] = 7.5
workflow["6"]["inputs"]["text"] = "prompt..."
workflow["7"]["inputs"]["text"] = "negative prompt..."
workflow["9"]["inputs"]["filename_prefix"] = "output_name"

r = requests.post(f"{HOST}/prompt", json={"prompt": workflow}, timeout=600)
pid = r.json()["prompt_id"]

# Poll for THIS SPECIFIC prompt_id
start = time.time()
while time.time() - start < 300:
    time.sleep(3)
    try:
        h = requests.get(f"{HOST}/history/{pid}", timeout=10).json()
        if pid in h:
            outputs = h[pid].get("outputs", {})
            status_str = h[pid].get("status", {}).get("status_str", "")
            if status_str == "error":
                print(f"ERROR: {h[pid]['status']}")
                break
            if outputs:
                for nid, nout in outputs.items():
                    if "images" in nout:
                        for img in nout["images"]:
                            fname = img["filename"]
                            params = {"filename": fname, "subfolder": img.get("subfolder",""), "type": "output"}
                            img_r = requests.get(f"{HOST}/view", params=params, timeout=30)
                            with open(os.path.join("output_dir", fname), "wb") as f:
                                f.write(img_r.content)
                            print(f"Saved: {fname}")
                break
    except:
        pass
```

### Batch pattern

Submit sequentially (not all at once — avoids the multi-submit hang):

```python
for var in variations:
    workflow_copy = copy.deepcopy(base_workflow)
    # ... inject params for this variation ...
    r = requests.post(f"{HOST}/prompt", json={"prompt": workflow_copy}, timeout=300)
    pid = r.json()["prompt_id"]
    # Poll until complete, THEN submit next
```

With model already loaded, each SDXL img2img at 1024x576 completes in ~6 seconds on RTX PRO 5000.

## Batch Generation Strategy

For hero image selection, generate 4-8 variations:
1. Fix denoise=0.70, vary seeds (4 seeds) → find best composition/texture
2. Fix denoise=0.80, vary seeds (4 seeds) → find best atmosphere
3. Pick best seed from each, compare 0.70 vs 0.80 result
4. Final hero = the one with best balance of form preservation + photorealism

## ControlNet Depth Pipeline (tested June 15, 2026)

The SDXL depth ControlNet is installed at `controlnet-depth-sdxl-1.0\diffusion_pytorch_model.safetensors`. Note the **backslash** in the model path — ComfyUI on Windows requires it.

### ControlNet model path lookup
Always verify the exact path via the API before building a workflow:
```python
import requests, json
r = requests.get("http://127.0.0.1:8188/api/object_info/ControlNetLoader", timeout=10)
paths = r.json()["ControlNetLoader"]["input"]["required"]["control_net_name"][0]
# Returns: ['controlnet-depth-sdxl-1.0\\diffusion_pytorch_model.safetensors']
```

### Three approaches tested — tradeoff matrix

| Approach | Photorealism | Form Preservation | Verdict |
|----------|-------------|-------------------|---------|
| **Pure img2img** (denoise 0.80) | **8/10** (best overall) | 6/10 (seed-dependent drift) | **Best for atmosphere-critical renders** |
| **ControlNet depth** (txt2img, strength 0.90) | 4/10 (reads as CG illustration) | **8/10** (locked Y-shape) | Form lock but kills realism |
| **ControlNet depth** (txt2img, strength 0.65) | **7.5/10** (good realism) | 5/10 (Y-shape drifted) | Best realism but form loss |
| **Hybrid** (ControlNet + img2img) | 3.5/10 (barely changed render) | 8/10 (locked perfectly) | **Does not work** — double conditioning fights itself |

### ControlNet strength tuning

| Strength | Effect |
|----------|--------|
| 0.90 | Form perfectly locked, but output looks like a technical illustration — flat sky, posterized mountains, 4/10 realism |
| 0.85 | Y-shape clear, some desert/arid environments hallucinated, 5/10 realism |
| 0.80 | Sweet spot IF a real depth map is used (see below). With RGB-as-depth, 5-6/10 realism |
| 0.75 | Good balance, multi-armed star form preserved, mountain backdrop decent, 6/10 |
| 0.65 | Best realism (7.5/10) — warm golden hour, snow-capped mountains, atmospheric haze — but Y-shape drifts to generic organic form |

### Critical finding: Normal maps >> Depth maps for aerial architecture

At aerial camera distances (400m+), depth maps are nearly useless because:
- Building height (20-50m) vs camera distance (600m) = <10% depth variation
- Terminal, ground, and nearby pavement all compress to the same depth value
- Even inverse depth (1/d normalization) only marginally improves contrast
- Result: depth map shows "flat ground + mountains + sky" — terminal invisible

**Normal maps work dramatically better** because they encode surface ORIENTATION:
- Roof curvature and structural ribs show as smooth color gradients
- Wall/floor/ceiling transitions show as sharp color discontinuities
- Aircraft silhouettes visible as small colored marks at gates
- Mountain ridge detail fully preserved
- All architectural form visible regardless of camera distance

**Tested results (June 15 2026, 8 variations):**

| Conditioning Image | Photorealism | Form Fidelity | Best Score |
|---|---|---|---|
| RGB render (img2img) | 8/10 | 3/10 | Wrong building |
| Depth map (inverse) | 5/10 | 6.5/10 | Terminal barely visible |
| **Normal map** | **8/10** | **8.5/10** | **Best overall** |

### Rendering normal map from Blender (proven)

```python
# Enable normal pass
scene.view_layers["ViewLayer"].use_pass_normal = True
scene.cycles.samples = 1  # normals don't need samples

# Compositor: RenderLayers → "Normal" output → Viewer Node
# (In Blender 5.1: use scene.compositing_node_group, not scene.node_tree)
cng = scene.compositing_node_group
rl = cng.nodes.new("CompositorNodeRLayers")
viewer = cng.nodes.new("CompositorNodeViewer")
cng.links.new(rl.outputs["Normal"], viewer.inputs[0])

bpy.ops.render.render()
img = bpy.data.images["Viewer Node"]
img.save_render(r"C:\Users\test\ComfyUI\input\airport_normal.png")
```

Resolution: 1024x576 (match SDXL input). Render time: ~1s.

### Rendering depth map from Blender (if needed)

Depth maps still useful for combined approaches. Use inverse depth for better near-range contrast:

```python
# After getting raw depth from Viewer Node:
for each pixel:
    if depth >= 100000:  # sky
        val = 0.0
    else:
        inv = 1.0 / depth
        val = (inv - min_inv) / (max_inv - min_inv)  # normalize
        val = clamp(0, 1)
```

Note: `CompositorNodeMapRange` is REMOVED in Blender 5.1 — must normalize in Python.

### Updated tradeoff matrix (with normal map data)

| Approach | Photorealism | Form Preservation | Verdict |
|----------|-------------|-------------------|---------  |
| Pure img2img (d=0.80) | 8/10 | 3/10 | Wrong building |
| ControlNet + depth map | 5/10 | 6.5/10 | Terminal invisible in depth |
| **ControlNet + normal map** (str=0.75) | **8/10** | **7/10** | **Best balance** |
| **ControlNet + normal map** (str=0.80) | **7/10** | **8.5/10** | **Best form lock** |
| ControlNet + normal map (str=0.90) | 5/10 | 8/10 | Illustration look |
| Hybrid (CN + img2img) | 3.5/10 | 8/10 | Does NOT work |

**Optimal pipeline: Normal map at strength 0.75-0.80, txt2img, 6-10 seed sweep.**

See ComfyUI skill's `references/controlnet-archviz-pipeline.md` for the full technique.

### Hybrid approach: same-image = bad, dual-image = good (proven June 30 2026)

**Same-image hybrid** (ControlNet depth + img2img from the SAME image) was tested
at 8 parameter combinations. Results: double conditioning causes the model to
reproduce the input almost exactly. At cn_strength=0.75 + denoise=0.80, output
rated 3.5/10 — essentially unchanged.

**Dual-image hybrid** (SEPARATE beauty render for VAEEncode + ground-truth depth
map for ControlNet) was tested June 30 2026 on VP studio (18 images across 6
views, 3 seeds each). This WORKS because the two images serve different roles:
- Beauty render → VAEEncode → latent starting point (img2img) — provides color/texture base
- Depth map → ControlNetApplyAdvanced — constrains 3D form independently

Parameters that work: denoise 0.42-0.50, CN strength 0.75-0.80, CN end 0.85-0.90,
dpmpp_2m/karras, 30 steps, CFG 8.0. The user's V2 (plain img2img, no depth)
verdict was "they all look the same" — flat and lifeless. V3 (dual-image with
depth conditioning) fixed this by forcing the diffusion to respect the actual
3D geometry while still adding atmosphere, texture, and cinematic lighting.

**Ground-truth depth from Blender** (ShaderNodeCameraData View Distance +
ShaderNodeMapRange 5m-150m + Emission, zero bounces, 1 sample, 16-bit PNG)
is superior to MiDaS-estimated depth for interior scenes because the depth
variation is meaningful at 5-50m ranges. See ComfyUI skill's
`references/controlnet-archviz-pipeline.md` for the Blender depth rendering technique.

**Recommendation by scenario:**
- **Interior/close-range (<150m):** Dual-image hybrid (beauty + ground-truth depth)
  at denoise 0.42-0.50, CN strength 0.75-0.80
- **Aerial/exterior (>300m):** ControlNet txt2img with normal map (not depth —
  depth is too flat at aerial distances)
- **Atmosphere-only (form not critical):** Pure img2img at denoise 0.80

### ControlNet workflow template (txt2img + depth)

```json
{
  "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"}},
  "2": {"class_type": "CLIPTextEncode", "inputs": {"text": "PROMPT", "clip": ["1", 1]}},
  "3": {"class_type": "CLIPTextEncode", "inputs": {"text": "NEGATIVE", "clip": ["1", 1]}},
  "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 576, "batch_size": 1}},
  "5": {"class_type": "LoadImage", "inputs": {"image": "depth_or_render.png"}},
  "6": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "controlnet-depth-sdxl-1.0\\diffusion_pytorch_model.safetensors"}},
  "7": {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["2",0], "negative": ["3",0], "control_net": ["6",0], "image": ["5",0], "strength": 0.80, "start_percent": 0.0, "end_percent": 0.85}},
  "8": {"class_type": "KSampler", "inputs": {"model": ["1",0], "positive": ["7",0], "negative": ["7",1], "latent_image": ["4",0], "seed": 42, "steps": 35, "cfg": 7.5, "sampler_name": "dpmpp_2m", "scheduler": "karras", "denoise": 1.0}},
  "9": {"class_type": "VAEDecode", "inputs": {"samples": ["8",0], "vae": ["1",2]}},
  "10": {"class_type": "SaveImage", "inputs": {"filename_prefix": "controlnet_output", "images": ["9",0]}}
}
```

## Future: Flux Dev

With 72GB VRAM per GPU, Flux Dev (fp8 or fp16) would produce superior architectural renders — much better text understanding, composition, and photorealism. Download:
```bash
comfy model download \
  --url "https://huggingface.co/Comfy-Org/flux1-dev/resolve/main/flux1-dev-fp8.safetensors" \
  --relative-path models/checkpoints
```
Requires a Flux-specific workflow (txt2img or img2img variant).
