# Teapot demo operator contract

This demo runs as `project:teapot-01` with isolated Daystrom stores. Use the configured Blender MCP for scene work; use Rhino MCP only when the `.3dm` source must be inspected or regenerated. ComfyUI may stylize an approved Blender render but never replace source geometry.

Before consequential work, call `mcp_daystrom_dml_stats`, query for this phase and operation, then call `mcp_cma_augment`. Inspect application state before mutation, make one bounded change through MCP, and inspect again. Ingest a structured success or failure record after the attempt. Call `mcp_cma_reinforce` only for an objectively validated success.

Use existing ready application bridges; do not spawn duplicate Rhino or Blender servers. Never use interactive Export/Save macros. For Rhino-to-Blender transfer, use a metadata-bearing `.3dm` with render meshes and `../../skills/import_with_metadata.py`; do not improvise OBJ/FBX handoffs. Validate with `../../skills/validate_blender_scene.py` before rendering or stylization.

Do not repeat an approach recorded as failed without a material change. If DML or an application MCP is unavailable, preserve state and stop at the gate.
