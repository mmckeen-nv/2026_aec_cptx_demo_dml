# VP Studio ComfyUI cookbook

This is the only supported ComfyUI execution path for the VP Studio demo.
ComfyUI is already launcher-owned and running on Windows. The agent submits one
approved Blender hero render through a checked-in API helper. It does not open
the ComfyUI browser UI, create workflow JSON, launch services, or install models.

## Terminal and path rules

- The Hermes `terminal` tool is Bash even though the host is Windows.
- Start in the demo directory:
  `C:/Users/test/2026_aec_cptx_demo_dml/demos/virtual_production_studio`.
- Use repository-relative forward-slash paths only.
- Never use `if exist`, PowerShell, backslash paths, drive-qualified paths,
  `curl`, `Invoke-RestMethod`, a heredoc, or a temporary workflow file.
- Run one command at a time. Do not join the two commands with `&&`, `;`, or a
  newline in one tool call.

## Recipe

## User-controlled style prompt

The default positive prompt is intentionally user-editable at:

```text
user_prompts/comfy_style_prompt.txt
```

Edit that text file before the run to change the visual treatment. The helper
prints the selected prompt source and a prompt SHA in preflight/output receipts,
so the run remains reproducible. The agent must not rewrite the user's prompt.
An explicit CLI override is also supported with `--prompt "..."`; the normal
demo command uses the file automatically. The negative prompt can be overridden
with `--negative-prompt "..."`.

### Step 1 - preflight

Run exactly:

```bash
python skills/comfyui_vp_stylize.py --dry-run
```

Do not perform any discovery before this command. The helper verifies:

- `http://127.0.0.1:8188/system_stats`;
- the installed node inventory;
- `sd_xl_base_1.0.safetensors`;
- `controlnet-depth-sdxl-1.0/diffusion_pytorch_model.safetensors`;
- `renders/vp_studio_hero_preview.png`.
- source-image contrast and visible foreground occupancy from the Blender
  production render.

Proceed only when stdout contains `COMFY_PREFLIGHT_PASS`.

### Step 2 - submit and wait

Run exactly:

```bash
python skills/comfyui_vp_stylize.py
```

The same process uploads the render, queues the fixed depth-conditioned SDXL
img2img graph, polls history, downloads the output, and exits. Do not poll with
another tool while this command is running. Allow up to ten minutes.

Required stdout receipts are:

1. `COMFY_PREFLIGHT_PASS`
2. `COMFY_QUEUED prompt_id=...`
3. `COMFY_OUTPUT_PASS ... bytes=...`

The accepted artifact is:

```text
comfy_enhanced/vp_studio_stylized.png
```

### Step 3 - one optional correction

Compare the source and result once with vision. If and only if visible geometry
drift is identified, run exactly:

```bash
python skills/comfyui_vp_stylize.py --denoise 0.20
```

Otherwise accept the first result. Do not change the model, graph, seed, camera,
dimensions, sampler, or ControlNet strength during the demo. Preserve the
user-selected prompt across the initial run and optional correction.

## Failure matrix

| Receipt or error | Meaning | Required action |
|---|---|---|
| `COMFY_SOURCE_FAIL` | Approved Blender render missing/empty | Report the exact source-render blocker; return to Blender only if authorized |
| `COMFY_PREFLIGHT_FAIL` | Endpoint, model, or node absent | Report the exact named dependency; do not install or launch anything |
| `COMFY_QUEUE_FAIL` | Fixed graph rejected | Report the returned node errors; do not create alternate JSON |
| Command timeout after `COMFY_QUEUED` | Generation still running or failed | Check once for the expected output file; do not resubmit blindly |
| `COMFY_OUTPUT_PASS` | Phase succeeded | Record the artifact and settings in one concise DML success lesson |

## Forbidden recovery paths

- Browser navigation to ComfyUI.
- `comfy launch`, duplicate servers, WSL discovery, or model downloads.
- Writing Python, JSON, shell, PowerShell, or batch files.
- Calling `/prompt`, `/history`, `/view`, or `/upload/image` manually.
- Rebuilding the graph from `/object_info`.
- Reusing the Cliff House multi-frame `scripts/comfyui_phase7.py` script.
