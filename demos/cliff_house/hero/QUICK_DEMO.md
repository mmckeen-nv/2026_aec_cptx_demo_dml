# Cliff House HERO - Under-Five-Minute Render Demo

## Goal

Open the operator-approved QUICK scene, make one Blender render from its
`ocean_view` camera,
then generate one direct FLUX.2 result. Do not model, import, relight, rebuild,
or run Rhino.

## Phase 1 - HERO open and render

Through `mcp_blender_execute_blender_code(code=...)`, load
`skills/blender_cliff_quick.py`, then call:

```python
print(quick.open_verified_quick(root))
print(quick.render_quick(root, camera_name="ocean_view"))
```

Require:

- `CLIFF_QUICK_OPEN_PASS objects=98 meshes=94 cameras=2 lights=2`
- `CLIFF_QUICK_RENDER_PASS`

The checked-in QUICK scene and camera are authoritative and immutable. The
helper verifies the master SHA-256, copies it to
`work/cliff_house_QUICK_working.blend`, and opens that disposable copy. All
material edits and saves belong to the working copy. Never save over
`cliff_house_QUICK_MASTER.blend`. Do not append another `.blend`, import Rhino
geometry, rebuild materials, or invent camera transforms.
If the user asks for another angle, call `list_cameras()` and choose an existing
named camera; do not make a new one during the quick demo.

## Phase 2 - User-directed ComfyUI render

The user controls the positive prompt. Read
`user_prompts/comfy_style_prompt.txt`; update only its prose when asked. Then
use the registered terminal tool, not Rhino or Blender MCP. Invoke the wrapper
by its repository-root path so this works from the BAC working directory:

```bash
python "$AEC_DEMO_ROOT/demos/cliff_house/hero/skills/comfyui_cliff_hero.py" --steps 12 --max-generation-dimension 1280
```

Never inline this workflow inside Blender. In particular, `SystemExit` in an
MCP-executed Blender snippet terminates Blender even when ComfyUI succeeds.

The wrapper uses the checked-in direct FLUX.2 Klein reference workflow with the
Cliff HERO render as source. Require, in order:

- `COMFY_FLUX2_PREFLIGHT_PASS`
- `COMFY_OUTPUT_PASS stage=flux2-direct`

The final artifact is `comfy_output/cliff_house_stylized.png`. The user prompt
controls the visual treatment, but FLUX.2 must preserve the verified house,
camera, openings, pool, and composition.

For another look, edit the user prompt or use `--prompt "..."`; do not reopen
Blender or rerun Phase 1. One source render can produce many fast variations.

## Timing target

- HERO open, audit, and Blender source render: under 60 seconds
- One direct FLUX.2 result: remaining demo time
- No preflight-only call, SDXL intermediate, depth pass, or animation
