---
status: CURRENT_POLICY
project_id: project:vp-studio-01
phase: rhino-to-blender
outcome: FAILURE_VALIDATED_AND_REPAIRED
approach_signature: demo_local_skills_path_or_generic_run_tool
observed_error: missing demos/virtual_production_studio/skills/import_with_metadata.py followed by invalid tool call run
root_cause: repository-root shared scripts were expressed ambiguously and BlenderMCP execution did not name the registered tool
avoidance_rule: resolve shared files as ../../skills from the demo working directory and execute Blender Python only with mcp_blender_execute_blender_code using its code argument
validation_rule: call mcp_blender_get_scene_info before execution and compare dynamic Rhino and Blender object counts afterward
---

The RTX Pro profile has no generic `run` tool. The Blender Python execution tool
is `mcp_blender_execute_blender_code`. The demo working directory is
`demos/virtual_production_studio`, so the metadata importer and validator are
`../../skills/import_with_metadata.py` and
`../../skills/validate_blender_scene.py`. Never search under a demo-local
`skills/` directory and never retry the invalid `run` call.
