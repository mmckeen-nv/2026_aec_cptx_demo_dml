# System Prompt - VP Studio Session Startup

## Purpose

Run `vp-studio-01` with the same visible, phase-driven cadence as the pristine
Cliff House demo.

## Startup order

1. Read `skills/INDEX.md`.
2. Read `skills/session_state.md`.
3. Read `user_prompts/project_prompt.md`.
4. Read `prompts/01a_locked_scene_manifest.md` and retain its units, world
   datum, coordinates, object sizes, names, and containment envelopes verbatim.
5. Check required MCPs once and report a real blocker instead of repairing it.
6. Inspect `mcp_rhino_list_slots` once, then make one read-only
   `mcp_rhino_run_python(script='print("ACTIVE_DOCUMENT_PATH "+__rhino_doc__.Path)')`
   call because `list_slots` does not include the document path. The launcher
   normally already owns an active document whose exact path is
   `source/vp_studio_01_template.3dm`. If that exact template is active, **do
   not call `mcp_rhino_open_doc`**. If another document is active, call
   `mcp_rhino_open_doc` exactly once. Never call it twice, invoke `_New`, or use
   a previous finished base model. Reopening the active template duplicates its
   datum guides. A resumed same-run handoff may reuse the exact active
   `rhino/vp_studio_01.3dm` output without reopening it.
7. Read `prompts/02_rhino_modeling_contract.md`.
8. Read the current numbered phase prompt. Its embedded C# scaffold is the
   mutation implementation; do not substitute Python or invent another API.

## Determine the current phase from the live Rhino document

Disk checkpoints, old `.3dm` files, DML summaries, and the compacted transcript
never prove that a phase is complete. Query the active Rhino document and choose
the first incomplete row below:

1. Phase 1 until `SLAB_FLOOR`, `ROOF_SLAB`, and `STAGE_VOLUME` exist.
2. Phase 2 until `LED_ACTIVE_WALL`, `LED_REAR_SUPPORT`, `LED_FLOOR_PROXY`, and
   `LED_CEILING_ACTIVE` exist and the two wall objects report Z bounds
   `0..288 in` and `0..312 in` respectively.
3. Phase 3 until `CONTROL_VIEW_GLAZING`, `WEST_48IN_CLEAR_AISLE`, and
   `SOUTH_SCENERY_ROUTE` exist.
4. Phase 4 until `STAGE_LIGHT_01`, `CAM_A_HERO_TRACKED_BODY`,
   `WORKSTATION_01`, `REVIEW_CHAIR_01`, and `ROAD_CASE_01` exist.
5. Only then run the deterministic handoff.

If later-phase objects exist while an earlier row is incomplete, repair the
earlier phase first. Never infer phase completion from a checkpoint filename or
from an older Blender scene.

## Phase execution

Before each phase, read the phase prompt, project prompt, and locked manifest.
The manifest overrides every loose example or default. Build one bounded,
scheduled assembly per MCP mutation call. A scheduled assembly may contain its
named constituent objects, but it may not span multiple phase groups. Use
coherent assembly mutation calls and targeted corrections when inspection finds
a real problem. Do not enforce a hard mutation count. After
each assembly, print its object bounds and compare them numerically with its
permitted envelope. End the phase with one read-only validator that prints
`NUMERIC_PASS`. Only then capture one fresh viewport, use local Nemotron vision,
make targeted correction calls, revalidate, and save the named
checkpoint.

Do not preload later phases. Do not write a whole-studio builder. Do not create
one object per call when a manifest-defined assembly can be safely created and
validated together. Execute Rhino geometry mutations only via
`mcp_rhino_run_csharp(script=...)` using the current phase's embedded scaffold;
never substitute Python, terminal, execute_code, Rhino commands,
editors, or file associations. Once modeling begins, do not patch local script
files. Do not close, spawn, or replace launcher-owned application slots.

After any context rotation, re-read `skills/session_state.md`, the locked
manifest, and the current phase prompt before the next mutation. Inspect Rhino
state first and never repeat geometry based only on the compacted transcript.

`skills/session_state.md`, prompts, rails, and helper files are immutable during
a demo. Never patch, overwrite, append, redirect terminal output into, or mark
them complete. They are configuration inputs, not an agent-authored progress
log. Record continuity only through validated receipts, saved application
checkpoints, and DML ingest.

The four original objects on `VP00_TEMPLATE_DATUMS` are launcher-owned datum
guides. Never copy, recreate, test-delete, purge, or count them as phase output.
Do not create `GUIDE_*` or `TEST_*` scratch objects. A fresh run must still have
exactly those four template datums when Rhino modeling finishes.

## Pipeline

1. `prompts/02a_phase_site_shell.md`
2. `prompts/02b_phase_stage_led.md`
3. `prompts/02c_phase_rooms_access.md`
4. `prompts/02d_phase_rigging_cameras.md`
5. `prompts/07_phase_export_blender.md`
6. `prompts/03_asset_sourcing_contract.md`
7. `prompts/04_comfyui_stylization_contract.md`

The last prompt is a real two-stage execution phase, not a suggestion to invent
a workflow. After the Blender beauty passes, run the checked-in helper once for
SDXL depth conditioning and FLUX.2 Klein reference refinement. The final phase
is complete only at `COMFY_OUTPUT_PASS stage=sdxl+flux`.

For an end-to-end request, Rhino completion is never a terminal condition and
must not produce a final answer. Immediately continue with
`prompts/07_phase_export_blender.md`. `VP_HANDOFF_PASS`, `VP_RENDER_PASS`, and
`COMFY_PREFLIGHT_PASS` are intermediate receipts. The only successful terminal
receipt is `COMFY_OUTPUT_PASS stage=sdxl+flux`; otherwise report one concrete
rail-defined blocker.

Daystrom DML supplies compact continuity and reusable experience. It does not
replace the phase prompt, control tool calls, or authorize skipping review.

Blender always begins from the launcher-owned generic scene. Never open any
existing `.blend` as an input. `blender_assets/vp_studio_01.blend` is an output
checkpoint written only after the current `.3dm` is imported and fingerprinted.
