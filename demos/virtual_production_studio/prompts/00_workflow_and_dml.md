# VP Studio 01 workflow and acceptance gates

## Phase 0: preflight

Run `deployment/rtx-pro-profile/Test-RTX-Pro-Preflight.ps1`. Required checks must pass for the local chat/vision APIs, Rhino MCP, Blender MCP, Daystrom DML, CMA, DML project identity, synchronized turns, and active-read retrieval. ComfyUI may remain stopped until stylization, but its installation must exist.

The required Rhino application bridge is `127.0.0.1:10500`. Confirm `mcp_rhino_list_slots` returns a ready slot. One failed check ends phase 0: do not repair profile configuration from inside the agent, install a substitute MCP, loop on `spawn_slot`, or proceed to Blender.

Use the tools that Hermes actually exposes. Rhino and Blender are MCP applications; ComfyUI is a local REST application in this installation.

## Phase 1: Rhino design model

Rhino owns all architectural and spatial geometry. Follow
`02_rhino_modeling_contract.md` and its six Cliff-House-style execution prompts.
The agent authors the geometry code directly in bounded MCP calls and validates
between element groups; it does not execute a complete checked-in builder. Save
only once to a timestamped working copy after the full Rhino gate passes.

Gate:

- Correct units and model tolerance.
- Required layers, named objects, and User Text exist.
- Building shell, stage floor, LED volume/support zones, rigging grid, rooms, circulation, electrical rooms, mechanical zones, loading access, camera positions, and safety clearances are present.
- Object/layer counts and viewport captures are recorded.
- `.3dm` saved successfully and the artifact path ingested into DML.

## Phase 2: Rhino-to-Blender handoff

Import only the approved `.3dm`. Compare source and destination counts by classification; do not accept an empty or partial import. Preserve Rhino names, layer paths, material intent, phase, system, and assumption-status metadata.

Before the handoff, read the repository-root
`system_prompts/07_phase_export_blender.md`, `skills/import_with_metadata.py`, and
`skills/validate_blender_scene.py`. Query DML for `project:vp-studio-01`,
`phase:rhino-to-blender`, the intended format, prior failures, unit conversion,
axis conversion, object counts, and bounding-box validation. Augment the exact
handoff plan through CMA.

Use the original direct `.3dm` path. In Rhino, generate render meshes for every
managed Brep and save a new handoff file with User Text and render meshes included.
In Blender, first audit that file with `rhino3dm`, then execute the checked-in
metadata importer through Blender MCP. OBJ and FBX are prohibited for this phase,
including checked-in or improvised writers, because they discard the metadata
contract.

Gate:

- No silent skipped Breps, Meshes, or Extrusions.
- Required architectural objects are present in Blender.
- Scale and world origin match Rhino.
- Missing materials, duplicate names, and critical overlaps fail validation.
- Every managed Rhino object from the accepted dynamic source count remains
  individually identifiable in Blender by stable name/collection; one flattened
  anonymous mesh or a source/destination count mismatch fails.
- Expected bounds are approximately `121.92 m x 91.44 m x 16.00 m`, with +Z up.
  Convert inches to meters exactly once.
- Face indices, non-degenerate faces, and connected-component/object counts pass
  before materials, lighting, cameras, or renders are created.

## Phase 3: Blender production scene

Blender owns render-specific work: mesh cleanup, UVs, materials, emissive LED content, practical fixtures, camera bodies and lenses, tracking markers, lighting, animation, and render passes. Keep architectural dimensions synchronized with Rhino; architectural changes go back to Rhino first.

Produce at least:

- Exterior establishing camera.
- Stage-wide hero camera.
- LED-volume interior camera.
- Dolly/tracking camera.
- Crane/jib camera envelope.
- Control-room witness camera.
- Beauty, diffuse/albedo, normal, depth, object-ID, and cryptomatte outputs where supported.

## Phase 4: ComfyUI stylization

Follow `04_comfyui_stylization_contract.md`. Use the REST API and a versioned workflow JSON. Begin from an approved Blender beauty render and its depth/control passes. Before prompting, read the cached-model evidence and inventory the visible `ASSET_<ASSET_KEY>` Blender collections; include only assets actually present in the render. Use low denoise by default so stylization preserves the modeled building, LED-wall curvature, camera perspective, openings, and equipment locations. Save the source render, workflow, seed, checkpoint/control-model names, prompt, denoise value, visible asset keys, control-pass paths, and output together.

Gate:

- No major geometry drift relative to the Blender source.
- No invented doors, columns, truss, LED seams, cameras, or unsafe rigging.
- Cached production equipment visible in Blender remains present, recognizable, and in the same location.
- The user can compare source and stylized images side by side.

## DML phase loop

Every phase follows `query -> augment -> act -> validate -> ingest -> reinforce`.

- Query before deciding.
- Augment before consequential tool use.
- Act only in the application assigned to the phase.
- Validate with objective tool output.
- Ingest durable, attributable facts.
- Reinforce only validated successes or user-approved preferences.

Every consequential attempt also follows the event-level loop in
`05_dml_learning_contract.md`: `query failures -> augment -> attempt -> validate ->
write event -> ingest event`. Failed attempts are learned, not reinforced. A retry
with the same approach signature is forbidden unless new evidence changes the
approach or invalidates the earlier diagnosis.
