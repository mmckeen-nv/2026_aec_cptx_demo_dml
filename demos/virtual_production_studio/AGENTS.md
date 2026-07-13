# VP Studio 01 operator contract

This directory is the active RTX Pro project. Build and modify the virtual-production studio through this fixed pipeline:

1. Rhino 8 through the `mcp_rhino_*` tools: site, shell, stage, LED-support geometry, production zones, infrastructure allowances, camera envelopes, and metadata.
2. Blender through the `mcp_blender_*` tools: import the validated Rhino model, then perform mesh cleanup, materials, LED emission, lighting, cameras, animation, and beauty/depth renders.
3. ComfyUI through its local REST API at `http://127.0.0.1:8188`: stylize approved Blender renders without replacing the modeled design.

Do not build the architectural studio directly in Blender. Do not install a package called `rhino-mcp`; the configured Rhino MCP router is already the authority. Do not advance to another application until the current phase passes its acceptance gate.

The agent must design and generate the Rhino geometry itself. There is no checked-in
studio builder, object schedule, JSON geometry plan, or complete model script to
replay. Follow the project brief and phase prompts, decide the composition, then
author bounded Python or C# directly in each `mcp_rhino_run_python` or
`mcp_rhino_run_csharp` call. A call may create one coherent element group only.
Inspect Rhino before and after it. Do not use `exec(open(...))`, import a project
geometry script, or assemble the entire studio in one tool call.

Use the same phase style as the original Cliff House workflow: purpose, inputs,
design decisions, execution steps, post-phase inspection, and a review gate.
Complete these Rhino subphases in order: site and shell; stage and LED volume;
rooms and access; rigging and cameras; electrical and mechanical; life safety and
data. Query DML and augment through CMA before each subphase. The brief supplies
requirements and planning assumptions, not a predetermined solution.

Do not use periodic saves. Never invoke `_Save`, `_SaveAs`, `Save`, `SaveAs`, or
a Rhino command macro for persistence. After every Rhino subphase passes and the
full model audit succeeds, call `mcp_rhino_save_doc` exactly once with a new
timestamped path. If validation fails, do not save and do not advance.

The Windows launcher starts Rhino's MCP listener on `127.0.0.1:10500` before Hermes. At phase 0, `mcp_rhino_list_slots` must return a ready slot before any modeling call. If it does not, stop and report the preflight failure. Do not edit Hermes MCP configuration, install another Rhino integration, repeatedly spawn slots, or fall back to shell/Blender geometry.

For a fresh-build run, query the active document before modeling and require zero
objects tagged `project=vp-studio-01`. Existing project geometry is not evidence of
agent work. If any is present, stop and ask the operator to open a new blank Rhino
document; do not reuse or silently delete it.

Before doing project work, read these files completely:

- `prompts/00_workflow_and_dml.md`
- `prompts/01_standard_vp_studio_brief.md`
- `prompts/02_rhino_modeling_contract.md`
- `prompts/02a_phase_site_shell.md`
- `prompts/02b_phase_stage_led.md`
- `prompts/02c_phase_rooms_access.md`
- `prompts/02d_phase_rigging_cameras.md`
- `prompts/02e_phase_electrical_mechanical.md`
- `prompts/02f_phase_life_safety_data.md`
- `prompts/03_asset_sourcing_contract.md`
- `prompts/04_comfyui_stylization_contract.md`
- `prompts/05_dml_learning_contract.md`
- `prompts/06_mcp_operations_contract.md`
- `../../system_prompts/07_phase_export_blender.md`
- `../../skills/import_with_metadata.py`
- `../../skills/validate_blender_scene.py`
- `assets/asset_manifest.yaml`

## Daystrom agentic path

The active identity is `project:vp-studio-01`. Daystrom DML and CMA are required parts of the work, not optional background memory.

At the beginning of every session and before every phase:

1. Call `mcp_daystrom_dml_stats` to confirm the project store is available.
2. Call `mcp_daystrom_dml_query` for prior decisions, dimensions, failures, validations, and user preferences relevant to the exact phase.
3. Call `mcp_cma_augment` when planning a consequential operation so retrieved project context participates in the decision.
4. Cite the retrieved decision or state that no applicable memory was found. Never silently invent remembered facts.

After a phase:

1. Validate the artifact through the application MCP and record objective evidence.
2. Use `mcp_daystrom_dml_ingest` for durable facts: approved dimensions, named objects/layers, artifact paths, validation counts, known failures, and fixes.
3. Use `mcp_cma_reinforce` only after a result is validated or explicitly approved by the user. Do not reinforce guesses, provisional electrical assumptions, or failed attempts.
4. Keep source/provenance, phase, timestamp, artifact path, and validation status with learned information.

After every consequential attempt, including a failed one, follow
`prompts/05_dml_learning_contract.md`. Write a UTF-8 Markdown attempt record, ingest
that record, and confirm the ingest reports at least one file before retrying or
advancing. Binary application artifacts such as `.3dm` and `.blend` are evidence
paths, not DML ingest targets.

Failures belong in DML with their approach signature, observed evidence, root
cause when known, and a specific avoidance rule. Never reinforce a failure into
CMA. Validated successes belong in DML and may be reinforced into CMA. Before a
retry, query DML using the phase, operation, approach signature, error, and failed
gate; then call `mcp_cma_augment` with the retrieved record. Do not repeat an unchanged approach that DML records as failed.

An application script that mutates state before raising an exception is a
`FAILURE_PARTIAL_MUTATION`, not a no-op. Re-query the application state and
record the partial mutation before deciding whether a retry is safe. Extra iterations may be used
only for a materially changed approach after this retrieval loop; they must not
extend an unchanged failure loop.

If DML is unavailable, stop before destructive or irreversible work. Report the failure and preserve the current application state.

## Rhino-to-Blender authority

Restore and follow the repository's original metadata-preserving handoff. Rhino
must create render meshes for every managed Brep and write a new `.3dm` handoff
with `WriteUserData=true` and `IncludeRenderMeshes=true`. Blender must read that
file directly through `../../skills/import_with_metadata.py`. Do not export or
import OBJ or FBX, do not use Rhino's interactive Export command, and do not write
a replacement exporter. Before import, use Blender MCP and `rhino3dm` read-only to
confirm that the current managed-object count equals both the Brep count and the
render-meshed Brep count, and confirm `UnitSystem.Inches`. The importer
converts inches to metres exactly once and preserves Rhino names, layers, and User
Text.

If a timed-out interactive Rhino command leaves the application waiting for
input, cancel that command and recheck the existing slot. Do not infer that
`run_python` is broken, spawn a replacement slot, or change the MCP installation.

## External assets

Rhino uses lightweight proxy volumes for movable production equipment. Detailed third-party models enter only in Blender and only from `assets/asset_manifest.yaml`. Resolve `assets/cache/cache_index.json` relative to its own directory and use a verified cached package before attempting network access. Do not use assets marked NonCommercial, NoDerivatives, ShareAlike, editorial-only, or NoAI. Preserve creator, source URL, asset ID, license, and modifications in `assets/ATTRIBUTIONS.md`; ingest the selected-asset record into DML after successful import and validation.

For the ComfyUI phase, treat the Blender scene as the geometry authority. ComfyUI never imports the cached 3D packages directly. Read `prompts/04_comfyui_stylization_contract.md`, inventory the visible `ASSET_<ASSET_KEY>` Blender collections, and carry their keys and object-ID/cryptomatte masks into the stylization manifest so the workflow preserves the equipment that is actually present.

## Safety and design authority

This is a conceptual demonstration model, not permit or construction documentation. Electrical service, structural/rigging loads, fire/life-safety, egress, accessibility, acoustics, and HVAC must remain labeled `PLANNING_ASSUMPTION` until reviewed by the appropriate licensed professionals and the authority having jurisdiction.
