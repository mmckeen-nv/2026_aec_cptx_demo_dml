# VP Studio Rhino-to-Blender execution adapter

## Purpose

Apply the repository's Phase 7 handoff using the tools and paths actually
registered in the RTX Pro Hermes profile.

## Path contract

Hermes runs from `demos/virtual_production_studio`. The repository root is
`../..`. Read these exact relative paths:

- `../../system_prompts/07_phase_export_blender.md`
- `../../skills/import_with_metadata.py`
- `../../skills/validate_blender_scene.py`

There is no `demos/virtual_production_studio/skills/` directory. A missing path
there is a path-resolution error; do not retry it, create that directory, or
write a replacement importer there.

## Exact Blender tool contract

The registered Blender tools include `mcp_blender_get_scene_info`,
`mcp_blender_execute_blender_code`, and
`mcp_blender_get_viewport_screenshot`. No tool named `run` exists. Never emit
`run`, `python`, or `execute` as a tool name.

1. Call `mcp_blender_get_scene_info` to prove the bridge is live.
2. Read the importer from `../../skills/import_with_metadata.py`.
3. Call `mcp_blender_execute_blender_code` with the required `code` argument.
   The code must load the checked-in importer with its absolute path supplied as
   `__file__`, call `import_3dm()` for the accepted handoff `.3dm`, and print the
   returned counts. Do not rewrite the importer.
4. Re-query scene info and compare the dynamic Rhino managed-object count with
   the Blender imported-object count.
5. Read `../../skills/validate_blender_scene.py` and execute it through the same
   `mcp_blender_execute_blender_code(code=...)` tool, with `__file__` set, then
   call `validate()` and print its findings.
6. Capture a viewport screenshot. Advance only when counts, metre bounds,
   metadata, names, faces, and validation all pass.

OBJ and FBX are prohibited. A failed exact tool call is recorded in DML before a
materially different retry. Do not change tools or paths speculatively.
