# Verified host pipeline calls

status: SUCCESS_VALIDATED
memory_class: procedural_tool_call
retrieval_tags: successful mesh bridge ComfyUI FLUX2 host terminal exact command
memory_summary: SUCCESS: after Rhino save, terminal runs scripts/build_mesh_bridge.py with fresh 3DM, fresh mesh JSON, and --expect-objects <current validated count>; require exit 0 and Blender count parity. Final terminal runs scripts/comfyui_flux2_direct.py with comfy_source PNG, flux2_enhanced PNG, and approved --prompt-file; require COMFY_OUTPUT_PASS and sidecar; no SDXL.

After Rhino saves the fresh 3DM, use the host `terminal` tool once:

```text
python scripts/build_mesh_bridge.py --source "aa_demo_versions/cliff_house_single_frame_01/rhino_assets/base_model.3dm" --output "aa_demo_versions/cliff_house_single_frame_01/blender_assets/fresh_cliff_house.mesh.json" --expect-objects <current validated Rhino count>
```

Require exit code 0. In Blender, import it with checked-in
`skills/import_with_metadata.py`, setting `__file__`, and assert the imported
mesh count equals that same current-run count.

For the final image, use the host `terminal` tool once:

```text
python scripts/comfyui_flux2_direct.py --source "aa_demo_versions/cliff_house_single_frame_01/renders/single_frame/comfy_source/frame_0000.png" --output "aa_demo_versions/cliff_house_single_frame_01/renders/single_frame/flux2_enhanced/frame_0000.png" --prompt-file "aa_demo_versions/cliff_house_single_frame_01/user_prompts/comfy_style_prompt.txt"
```

Require `COMFY_OUTPUT_PASS stage=flux2-direct`, one 1920x1080 PNG, and its
`.comfy.json` provenance sidecar. Do not insert SDXL or a second generative
pass. Do not use DML to rediscover commands already recalled here.
