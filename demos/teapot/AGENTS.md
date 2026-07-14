# BAC Teapot demo operator contract

This demo runs as `project:teapot-01` with isolated Daystrom DML/CMA. Blender is
the scene authority; Rhino is used only to inspect or regenerate the source
`utah_teapot.3dm`. ComfyUI may stylize an approved render but never replace the
teapot geometry.

## Inputs and execution

Hermes runs from `demos/teapot`; repository root is `../..`. The preferred source
is `utah_teapot.3dm`; `utah_teapot.obj` is a documented fallback. Existing
`teapot_demo.blend` and `renders/blender_teapot_hero.png` are reference artifacts.
`build_teapot_demo.py` is an offline deterministic smoke-test utility, not an
instruction for Hermes to execute the complete scene in one call.

Hermes must build or modify the demonstration itself through bounded
`mcp_blender_execute_blender_code(code=...)` calls: inspect/clear only demo-owned
objects, import the teapot, normalize and place it, assign materials, create the
ground, add lighting, compose the camera, render, and validate. Inspect after each
group. Never emit a generic `run` tool call, drive Blender UI macros, or overwrite
source files. Save once to a new timestamped file under `work/` after the final
gate.

## DML/CMA loop

Before each consequential step call `mcp_daystrom_dml_stats`, query the phase and
prior attempts through `mcp_daystrom_dml_query`, then call `mcp_cma_augment`.
Afterward ingest a structured success/failure event. Reinforce only validated
success through `mcp_cma_reinforce`; never repeat an unchanged failed approach.

## Acceptance gate

The final scene must contain exactly one demo-owned teapot, a ground object, a
render camera, and intentional lights. The teapot must have nondegenerate mesh
geometry, largest dimension approximately `0.30 m`, sit on the ground without
penetration, and carry a real Blender material slot. Render at least one hero PNG,
then call `mcp_blender_get_viewport_screenshot` and inspect it. A prose claim,
object count, or saved file without visible teapot evidence does not pass.

For `.3dm` transfer, use `../../skills/import_with_metadata.py`, compare per-axis
source/import bounds, and validate with `../../skills/validate_blender_scene.py`.
OBJ/FBX improvisation is prohibited when the `.3dm` route is healthy. Preserve
state and stop only when DML or an application bridge is genuinely unavailable.
