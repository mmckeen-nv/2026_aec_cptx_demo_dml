# Skills INDEX - BAC Teapot

This is a fast Blender-only interaction demo.

1. Read session state, project prompt, locked manifest, and current phase.
2. Load `skills/blender_teapot_interactions.py` only through Blender MCP.
3. Call `build_canonical_teapot(root, reset_scene=True)` once; require
   `CANONICAL_DATA_PASS` and `TEAPOT_BUILD_PASS`.
4. Call `prepare_product_stage()` and `render_preview()`; require look and
   preview receipts before audience interaction.
5. Respond naturally to material and camera requests with bounded helper calls.
6. Never call Rhino in BAC Teapot. Other demos retain their Rhino workflows.
7. The launcher owns application lifecycle. DML is advisory continuity.
8. On an explicit teapot-stylization request, run `skills/comfyui_teapot.py`
   through terminal only after `TEAPOT_PREVIEW_PASS`; require the SDXL and FLUX
   stage receipts. Do not run it for ordinary Blender material changes.

Target live duration: under five minutes to the first material change.
