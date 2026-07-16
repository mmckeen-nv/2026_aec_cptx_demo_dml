---
name: comfyui-cookbook
description: Use when the Virtual Production Studio demo has an approved Blender hero render and must run its final local ComfyUI stylization phase. Execute only the checked-in deterministic helper against launcher-owned ComfyUI; do not discover, launch, reconfigure, or automate ComfyUI through a browser.
license: MIT
metadata:
  hermes:
    tags: [comfyui, virtual-production, sdxl, controlnet, stylization]
    related_skills: [blender-comfyui-integration]
---

# VP Studio ComfyUI Cookbook

## Overview

Run one approved Blender hero render through the fixed local SDXL plus depth
ControlNet graph. The launcher owns ComfyUI at `http://127.0.0.1:8188`; the
checked-in helper owns upload, graph construction, polling, and download.

Do not substitute the Cliff House multi-frame script. The useful Cliff House
pattern is a prepared input and one bounded execution path, not its browser or
remote-server implementation.

## Preconditions

- Work from the VP demo root:
  `C:/Users/test/2026_aec_cptx_demo_dml/demos/virtual_production_studio`.
- Require `renders/vp_studio_hero_preview.png` to exist and be non-empty.
- Require the helper's source composition gate to pass; a blank, uniform gray,
  or nearly empty Blender render is a Blender blocker, not a ComfyUI input.
- Treat ComfyUI, models, and nodes as launcher-owned dependencies.
- Use the Hermes Bash `terminal` tool with repository-relative forward-slash
  paths. Run one command per tool call.

## Execute

The positive style prompt is user-owned. Before launch, users may edit
`user_prompts/comfy_style_prompt.txt`; the helper reads it automatically and
prints its source and SHA. Do not overwrite it or silently substitute agent
wording. For an explicit one-run override, the helper also accepts
`--prompt "..."` and `--negative-prompt "..."`.

1. Run exactly:

   ```bash
   python skills/comfyui_vp_stylize.py --dry-run
   ```

2. Continue only after stdout contains `COMFY_PREFLIGHT_PASS`.

3. Run exactly:

   ```bash
   python skills/comfyui_vp_stylize.py
   ```

4. Allow the command to remain active for up to ten minutes. Do not launch a
   second poller or resubmit while it runs.

5. Require these receipts in order:

   - `COMFY_PREFLIGHT_PASS`
   - `COMFY_QUEUED prompt_id=...`
   - `COMFY_OUTPUT_PASS ... bytes=...`

6. Accept only:
   `comfy_enhanced/vp_studio_stylized.png`.

## One Optional Correction

Compare source and result once with vision. If and only if vision identifies
visible geometry drift, run exactly:

```bash
python skills/comfyui_vp_stylize.py --denoise 0.20
```

Otherwise accept the first result. Do not change the graph, model, seed, camera,
resolution, sampler, steps, CFG, or ControlNet strength during the demo. Keep
the same user-selected prompt for the optional correction.

## Failure Handling

- `COMFY_SOURCE_FAIL`: report the missing approved Blender render.
- `COMFY_PREFLIGHT_FAIL`: report the exact missing endpoint, node, checkpoint,
  or ControlNet model. Do not install or launch anything.
- `COMFY_QUEUE_FAIL`: report the returned node errors. Do not create alternate
  workflow JSON.
- Timeout after `COMFY_QUEUED`: check once for the accepted output file. Do not
  resubmit blindly.
- `COMFY_OUTPUT_PASS`: record the artifact and fixed settings as one concise DML
  success lesson.

## Forbidden Paths

- Browser navigation or DOM automation for ComfyUI.
- `comfy launch`, WSL discovery, duplicate servers, or model downloads.
- Manual calls to `/prompt`, `/history`, `/view`, `/object_info`, or
  `/upload/image`.
- Writing Python, JSON, shell, PowerShell, batch, or temporary workflow files.
- Rebuilding the graph, using the Cliff House `comfyui_phase7.py`, or invoking
  arbitrary scripts.

## Verification Checklist

- [ ] Preflight receipt is present.
- [ ] Exactly one prompt was queued.
- [ ] Output receipt reports a non-zero byte count.
- [ ] The accepted PNG exists at the required path.
- [ ] At most one vision review and one denoise correction occurred.
- [ ] The success or exact blocker was recorded through DML.
