# Cliff House demo operator contract

This demo runs as `project:cliff-house-01` with isolated Daystrom DML/CMA.
Rhino owns architectural geometry, Blender owns visualization, and ComfyUI may
stylize only approved Blender renders.

## Authoritative inputs

Hermes runs from `demos/cliff_house`; repository root is `../..`. Read:

- `../../aa_demo_versions/cliff_house_02/user_prompts/project_prompt.md`
- `../../system_prompts/00_session_startup.md`
- the applicable numbered phase prompt under `../../system_prompts/`
- `../../skills/import_with_metadata.py`
- `../../skills/validate_blender_scene.py`

The immutable Rhino source is
`../../aa_demo_versions/cliff_house_02/rhino_assets/base_model.3dm`. Never
overwrite it. Work only in a new timestamped file under `work/`. Existing `.blend`
files under `source/`, `sessions/`, and `hero/` are references or accepted
artifacts, not permission to skip validation.

## Agentic execution

Before each phase call `mcp_daystrom_dml_stats`, query the exact phase and prior
failures with `mcp_daystrom_dml_query`, then call `mcp_cma_augment`. Inspect the
application before mutation, make one bounded change through its registered MCP
tool, and inspect again. Write and ingest a structured success/failure event.
Call `mcp_cma_reinforce` only for objectively validated success. Never repeat an
unchanged failed approach.

Use the existing Rhino slot and Blender bridge; do not spawn duplicates. For
Rhino code use only `mcp_rhino_run_python` or `mcp_rhino_run_csharp`. For Blender
code use only `mcp_blender_execute_blender_code(code=...)`; no generic `run` tool
exists. Never use interactive Export/Save macros or periodic saves.

## Handoff and visual gates

Transfer a metadata-bearing `.3dm` through
`../../skills/import_with_metadata.py`; OBJ/FBX are prohibited. Join every part
returned by `Mesh.CreateFromBrep`, and require per-object source/mesh bounding-box
parity on X/Y/Z—not just equal counts. Validate handoff metadata with
`validate(require_material_slots=False)`; require slots after material assignment
with `validate(require_material_slots=True)`.

Capture and inspect plan plus axonometric screenshots after Rhino work, Blender
import, material/lighting work, and the final render. Flat sheets, missing house
mass, incorrect ocean-facing orientation, scale drift, or a screenshot that does
not visibly show the claimed result fails the phase. Preserve state and stop only
when DML or an application bridge is genuinely unavailable.
