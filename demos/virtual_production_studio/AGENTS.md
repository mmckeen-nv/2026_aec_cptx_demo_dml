# Virtual Production Studio demo operator contract

This demo runs as `project:vp-studio-01` with isolated Daystrom DML/CMA.
Rhino 8 owns architectural geometry, Blender owns visualization, and ComfyUI may
stylize only approved Blender renders.

## Authoritative inputs

Hermes runs from `demos/virtual_production_studio`; repository root is `../..`.
Use the same execution pattern and generic phase prompts as the working Cliff
House demo. Read only:

- `prompts/01_standard_vp_studio_brief.md` for what to design
- `../../system_prompts/00_session_startup.md`
- the one applicable numbered phase prompt under `../../system_prompts/`
- `../../skills/import_with_metadata.py` and
  `../../skills/validate_blender_scene.py` when the Blender handoff begins

Do not preload every VP prompt. The detailed files under `prompts/` are
references for the applicable phase only. Use `prompts/03_asset_sourcing_contract.md`,
`assets/asset_manifest.yaml`, and `prompts/04_comfyui_stylization_contract.md`
only after the Blender scene exists.

The immutable Rhino datum is `source/vp_studio_01_template.3dm`. It uses inches
and absolute tolerance `0.01`, with 16 locked reference curves/text dots and no
design solids. Open that exact document once with `mcp_rhino_open_doc`; never invoke `_New`,
`_NewSmall`, an interactive template chooser, or the completed
`vp_studio_01_base_model.3dm` reference artifact. Work only in new timestamped
files under `work/`.

## Agentic execution

The agent must design and generate the Rhino geometry itself. There is no
checked-in studio builder, predetermined object schedule, or complete model
script to replay. Author bounded Python or C# directly in
`mcp_rhino_run_python(script=...)` or `mcp_rhino_run_csharp(script=...)`. A call
should create or revise one coherent architectural group, then continue naturally
through site/shell, stage/LED volume, rooms/access, rigging/cameras,
electrical/mechanical allowances, and life-safety/data planning.

Use the working Cliff House rhythm: inspect the application, make a meaningful
bounded change, and inspect again at design checkpoints. Do not impose arbitrary
mutation counts. Save useful timestamped checkpoints with `mcp_rhino_save_doc`;
never use interactive Save, SaveAs, or Export macros and never trigger modal
dialogs.

Visual correction is core functionality, not optional presentation. At the end
of each major Rhino phase (site/shell, stage/LED, rooms/access, rigging/cameras,
electrical/mechanical, and life-safety/data), re-list the modeled objects and
capture the phase's required Rhino views with
`mcp_rhino_get_viewport_image`. Hermes must pass those images to the configured
auxiliary vision model, identify visible proportion, massing, circulation,
collision, sightline, and omission defects, revise the geometry when needed,
and recapture the affected view. The required review views are explicit workflow
requests, so camera/zoom tools may compose them without altering geometry.

Do not save a checkpoint, declare a Rhino phase complete, reinforce success in
CMA, or begin Blender import unless both fresh object-list evidence and fresh
viewport/vision evidence were produced after the latest Rhino mutation. This is
a phase-boundary gate, not a fixed mutation or token quota.

## Daystrom memory harness

Daystrom DML is the always-on continuity and learning layer behind the work.
Hermes already loads `memory.provider: daystrom_dml` with retrieval enabled and
DCN active-read iteration decisions. Do not turn memory into per-tool ceremony.

At session start and meaningful phase boundaries, use `mcp_daystrom_dml_stats`,
`mcp_daystrom_dml_query`, and `mcp_cma_augment` to retrieve relevant decisions,
validated dimensions, failures, and preferences. After a meaningful validated
phase or a real failure, ingest one concise structured record. Use
`mcp_cma_reinforce` only for objectively validated success. A partial application
mutation is `FAILURE_PARTIAL_MUTATION`; inspect its actual state before retrying.
Do not repeat an unchanged approach that already failed.

When recording the first meaningful success or failure in a session, read
`prompts/05_dml_learning_contract.md` for the compact record schema. Do not load
that file repeatedly between geometry calls.

DML may grant additional iterations when measurable progress continues and deny
them when the agent is repeating an unchanged failure. Memory activity must not
interrupt a coherent geometry operation merely because a fixed tool-call count
was reached.

## MCP and application state

The launcher owns the ready Rhino listener at `127.0.0.1:10500`. Confirm it with
`mcp_rhino_list_slots`. Do not edit Hermes MCP configuration, spawn or close
slots, close the document, or replace a healthy listener. Blender uses
`127.0.0.1:9876`.

If Rhino or Blender MCP registration/connection fails, stop the application
phase and report the exact preflight blocker. Do not use terminal/config commands
to repair Hermes from inside the run, do not launch another Rhino process, and
never invoke `RunPythonScript`, `EditPythonScript`, or open a `.py` file in
Rhino. Python and C# source must be passed only as the direct `script=` argument
of the registered MCP tools so no editor or file chooser can appear.

Use exact registered tool names. Blender Python is
`mcp_blender_execute_blender_code(code=...)`. Never call a generic tool named
`run`; it does not exist.
Do not build the studio architecture directly in Blender. If a tool fails, inspect
the error and change the approach instead of trying unrelated browser, shell, or
application-lifecycle recovery.

Consult `prompts/06_mcp_operations_contract.md` only when an MCP operation or
argument is unclear; do not preload it during ordinary geometry work.

## Rhino-to-Blender handoff

Use the metadata-preserving direct `.3dm` handoff described by
`../../system_prompts/07_phase_export_blender.md`. OBJ and FBX are prohibited.
Rhino must create render meshes for managed Breps and save with
`WriteUserData=true` and `IncludeRenderMeshes=true`. Join every part returned by
`Mesh.CreateFromBrep`; using only `parts[0]` is a known failure. Require names,
metadata, nonempty vertices/faces, and source/mesh bounding-box parity on X/Y/Z.

Import through `../../skills/import_with_metadata.py`, validate with
`validate(require_material_slots=False)`, and capture plan plus axonometric
screenshots. Require actual material slots after the material phase. Flat sheets,
missing mass, scale drift, or bounds inconsistent with Rhino fail the handoff.

## Assets, ComfyUI, and safety

Detailed Creative Commons equipment enters only in Blender from
`assets/asset_manifest.yaml`; Rhino uses proxy volumes. Preserve attribution and
license metadata. ComfyUI uses approved Blender renders as geometry authority and
does not replace the modeled design.

Electrical service, rigging, structural, fire/life-safety, accessibility, HVAC,
and egress values remain `PLANNING_ASSUMPTION` until reviewed by qualified
professionals and the authority having jurisdiction.
