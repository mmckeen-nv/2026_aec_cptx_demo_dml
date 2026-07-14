# Teapot durable workflow knowledge

- project_id: `project:teapot-01`
- Blender MCP is the primary scene bridge; Rhino MCP is used for source `.3dm` inspection or regeneration.
- Inspect through MCP before mutation and validate after one bounded change.
- Repository root is `../..` from the demo. Prefer the metadata-bearing `.3dm` path through `../../skills/import_with_metadata.py`; do not improvise OBJ/FBX handoffs.
- Hermes builds through bounded `mcp_blender_execute_blender_code` calls and visually inspects the viewport/render; `build_teapot_demo.py` is an offline smoke-test utility, not the agent workflow.
- Require one teapot near 0.30 m, ground contact, real material, camera, lighting, a saved work artifact, and visible screenshot evidence.
- Record validated successes and failures in DML. Reinforce only validated successes into CMA.
