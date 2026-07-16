# ComfyUI stylization phase

ComfyUI is the final presentation phase. Rhino remains authoritative for the
building and studio layout; Blender remains authoritative for assets,
materials, lighting, camera perspective, and placement. ComfyUI may enhance the
approved Blender render but may not redesign it.

## Exact local execution path

This phase never uses Rhino MCP or Blender MCP. The registered `terminal` tool
is available and is the required execution path for the checked-in helper.
Do not claim terminal access is unavailable without actually receiving a tool
transport error from the exact command below. Never call any `mcp_rhino_*`
tool after `VP_HANDOFF_PASS`.

Read `skills/COMFYUI_COOKBOOK.md` first. It is the authoritative operational
recipe and failure matrix for this phase.

The positive style prompt is user-controlled. Before dry-run, read
`user_prompts/comfy_style_prompt.txt`; the user may edit that file or ask the
agent to update its prose. The helper reads it automatically and prints a
prompt SHA-256 receipt. Do not silently replace the user's prompt with a fixed
internal prompt. Manual operators may also use `--prompt "..."`, which takes
precedence over the file.

Do not construct a workflow in the browser and do not adapt the Cliff House
frame-sequence script. Use the checked-in single-render helper exactly:

```powershell
python skills/comfyui_vp_stylize.py --dry-run
python skills/comfyui_vp_stylize.py
```

The helper owns the complete API sequence:

1. Verify `GET http://127.0.0.1:8188/system_stats` and inventory
   `GET /object_info`.
2. Require the locally installed `sd_xl_base_1.0.safetensors`,
   `controlnet-depth-sdxl-1.0\\diffusion_pytorch_model.safetensors`, and the
   exact nodes used by the graph.
3. Require `renders/vp_studio_hero_preview.png` as the approved source. Reject
   low-contrast or nearly empty frames with `COMFY_SOURCE_FAIL`; file existence
   and byte size alone do not pass. Upload only a passing source with
   `POST /upload/image`.
4. Submit the fixed SDXL depth-conditioned img2img graph with `POST /prompt`.
   Defaults are seed `42`, denoise `0.28`, 24 steps, CFG 6, depth strength
   0.72, and a geometry-preserving positive/negative prompt.
5. Poll `GET /history/{prompt_id}` until completion, download through
   `GET /view`, and write
   `comfy_enhanced/vp_studio_stylized.png`.

Success requires the helper's three explicit receipts in order:

- `COMFY_PREFLIGHT_PASS`
- `COMFY_QUEUED prompt_id=...`
- `COMFY_OUTPUT_PASS ... output=... bytes=...`

If dry-run fails, report the exact missing service, model, node, or source
render. Never launch another ComfyUI instance, install models, search WSL, or
invent an alternate graph during the demo. Do not use browser automation for
ordinary submission or polling.

After `COMFY_OUTPUT_PASS`, send the source and result to vision for one focused
geometry-preservation review. If concrete drift is identified, rerun once with
only `--denoise 0.20`; otherwise accept the first result.

After a meaningful validated result or failure, store one compact DML lesson
containing the model names, seed, denoise, output path, and preservation result.
