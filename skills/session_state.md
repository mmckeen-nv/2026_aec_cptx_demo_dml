# Session State -- aec_cptx_demo
# skills/session_state.md
# Read this immediately after INDEX.md at the start of every session.
# Last updated: May 2026

---

## ROOT

C:\Users\swags\Documents\2026_aec_cptx_demo

---

## MCP connections

| MCP             | Required for    | How to start                                             | Status  |
|-----------------|-----------------|----------------------------------------------------------|---------|
| Filesystem      | All             | Auto (Cowork connector)                                  | Working |
| rhinoceros3d    | Phases 1-5      | Cowork connector -> localhost:3001                       | Working |
| blender         | Phases 5-9      | Blender Scripting tab: bpy.ops.blendermcp.start_server() | Working |
| obs             | Recording       | Auto-restart via tools/obs_mcp_wrapper.ps1               | Working |
| davinci-resolve | Post-production | Wired in config, not yet tested end-to-end               | Pending |

OBS WebSocket password: bigfish (port 4455)
BlenderMCP port: 9876

---

## Active project

cliff_house_02
Location: C:\Users\swags\Documents\2026_aec_cptx_demo\aa_demo_versions\cliff_house_02\
All new and active projects are under the new root.

---

## System status

New 2026_aec_cptx_demo root is live and clean. Old aec_demo_master is untouched.

Key differences from old system:
- system_prompts/ contains both session rules AND phase prompts (01-11)
- Dead prompts (07 landscaping, 08 entourage, 09-11 superseded) do not exist here
- APPENDIX_pitfalls/materials/segmentation are standalone single-source files
- OBS: Claude writes current_stage.json only -- tray app controls all recording
- All paths relative to ROOT (one absolute path in 00_session_startup.md)

Large binaries remain in old root (not copied -- too large):
- HDRIs: {ASSET_ROOT}\assets\
- Architectural references: {ASSET_ROOT}\architectural_references\

---

## Architecture decisions confirmed

- Terrain tolerance: 0.0001 / 0.0001 / 1.0
- Balconies: within footprint, outside upper floor walls
- Floor slab: one object per floor, includes cantilever
- Render resolution: 1920x1080 (final), 960x540 (test)
- EXR depth channel: Depth.V (FLOAT)
- HDRI sun orientation: Z rotation = 90 degrees puts sun in west (-X)
- Camera animation: per-frame keyframes, smoothstep easing, no scene.frame_set() in loop
