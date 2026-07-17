# Cliff House HERO - Under-Five-Minute Render Demo

## Goal

Open the verified HERO scene, select a tested camera, make one Blender render,
then generate user-directed ComfyUI variations. Do not model, import, relight,
or rebuild unless the user explicitly leaves the quick-demo scope.

## Phase 1 - HERO open and render

Through `mcp_blender_execute_blender_code(code=...)`, run:

```python
import os, importlib.util
root=os.environ["AEC_DEMO_ROOT"]
path=os.path.join(root,"demos","cliff_house","hero","skills","blender_cliff_hero.py")
spec=importlib.util.spec_from_file_location("cliff_hero",path)
hero=importlib.util.module_from_spec(spec);spec.loader.exec_module(hero)
print(hero.open_verified_hero(root))
print(hero.render_hero(root, camera_name="HeroCamera"))
```

Require:

- `CLIFF_HERO_OPEN_PASS objects=183 meshes=174 cameras=7 lights=2`
- `CLIFF_HERO_RENDER_PASS`

The checked-in scene and camera are authoritative and immutable. The helper
verifies the master SHA-256, copies it to
`work/cliff_house_02_HERO_working.blend`, and opens that disposable copy. All
material edits and saves belong to the working copy. Never save over
`cliff_house_02_HERO.blend`. Do not append another `.blend`, import Rhino
geometry, rebuild materials, or invent camera transforms.
If the user asks for another angle, call `list_cameras()` and choose an existing
named camera; do not make a new one during the quick demo.

## Phase 2 - User-directed ComfyUI render

The user controls the positive prompt. Read
`user_prompts/comfy_style_prompt.txt`; update only its prose when asked. Then
use the registered terminal tool, not Rhino or Blender MCP. Invoke the wrapper
by its repository-root path so this works from the BAC working directory:

```bash
python "$AEC_DEMO_ROOT/demos/cliff_house/hero/skills/comfyui_cliff_hero.py" --dry-run
python "$AEC_DEMO_ROOT/demos/cliff_house/hero/skills/comfyui_cliff_hero.py"
```

Never inline this workflow inside Blender. In particular, `SystemExit` in an
MCP-executed Blender snippet terminates Blender even when ComfyUI succeeds.

The wrapper uses the same tested two-stage graph as RTX Pro with the Cliff HERO
render as source: SDXL depth conditioning first, then FLUX.2 Klein reference
refinement. Require, in order:

- `COMFY_PREFLIGHT_PASS`
- `COMFY_SDXL_QUEUED` and `COMFY_SDXL_OUTPUT_PASS`
- `COMFY_FLUX_QUEUED` and `COMFY_FLUX_OUTPUT_PASS`
- `COMFY_DESKTOP_OUTPUT_PASS` for the accepted SDXL and FLUX artifacts
- `COMFY_OUTPUT_PASS stage=sdxl+flux`

The stage artifacts are `comfy_output/cliff_house_sdxl.png` and
`comfy_output/cliff_house_stylized.png`. The user prompt controls the visual
treatment, but both stages must preserve the verified house, camera, openings,
terrain, and composition.

For another look, edit the user prompt or use `--prompt "..."`; do not reopen
Blender or rerun Phase 1. One source render can produce many fast variations.

## Timing target

- HERO open and audit: under 30 seconds
- Blender preview: under 60 seconds
- Comfy dry-run plus one output: remaining demo time
