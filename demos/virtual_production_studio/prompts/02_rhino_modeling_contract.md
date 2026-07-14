# Rhino MCP agent-authored modeling contract

## Purpose

Hermes designs and models the studio in Rhino from the brief. The repository
does not contain a complete geometry builder or object-by-object schedule. Treat
the dimensions in `01_standard_vp_studio_brief.md` as requirements and planning
envelopes; make and document the actual spatial decisions needed to satisfy them.

## Tool discipline

Use only registered `mcp_rhino_*` tools for architectural modeling. Begin with
`mcp_rhino_list_slots`, attach to the existing ready Rhino 8 slot, inspect the
active document, and establish units/tolerances. A fresh-build run requires zero
objects tagged `project=vp-studio-01`; if any exist, stop and request a new blank
document rather than reusing or deleting them. Author the Python or C# for each
bounded modeling operation yourself and send it directly to
`mcp_rhino_run_python` or `mcp_rhino_run_csharp`.

Before the first mutation, read the installation-specific Rhino 8 ABI and
viewport handoff in `06_mcp_operations_contract.md`. Do not use nonexistent
`rs.LayerIndex` or `rs.ObjectAttributes`, treat `FindByFullPath` as a Layer
object, or invent a remote URL for Rhino MCP 0.1.5 viewport bytes.

Prohibited shortcuts:

- Do not read or execute a checked-in geometry builder; none is authoritative.
- Do not use `exec(open(...))`, a JSON geometry plan, or a generated disk script.
- Do not create the whole building or all required systems in one MCP call.
- Do not copy geometry from an earlier `.3dm` as a substitute for designing it.
- Do not move architectural modeling to Blender.

One mutation call handles one coherent element group and should normally create
no more than 20 objects. Keep helpers local to that call. Numerical inspection
may occur between element groups, but visual correction is mandatory at each
major phase boundary. A successful script return or numerical audit alone is
not a passed phase.

## Visual correction protocol

At the end of every numbered Rhino phase, after its latest mutation:

1. Call `mcp_rhino_list_objects` and verify the phase's names, layers, metadata,
   types, counts, and measured bounds.
2. Compose the phase's required plan, axonometric, interior, or services view
   using dedicated camera/zoom tools, then capture it with
   `mcp_rhino_get_viewport_image`. Never use `mcp_rhino_run_command`; Rhino
   command macros can wait for UI input and deadlock MCP.
3. Follow the Rhino MCP 0.1.5 viewport handoff in
   `06_mcp_operations_contract.md`: save the same active view to a local PNG
   with the verified read-only `ActiveView.CaptureToBitmap` recipe, then call
   `vision_analyze` with that absolute path and a phase-specific defect
   question. Never invent a URL or decode nested base64 with `execute_code`. A
   captured viewport without a successful `vision_analyze` is not validation.
4. Use that vision result to assess visible massing,
   proportion and scale, access/circulation, LED curvature, camera sightlines,
   collisions, disconnected/floating geometry, and missing required elements.
5. If vision reports a plausible defect, inspect it numerically, revise it in a
   bounded MCP mutation, then repeat the object-list and affected viewport check.
6. Record the images, vision result, and disposition of every issue in the phase evidence.

Do not substitute bounding-box text, object counts, metadata, or a Python audit
for viewport evidence. No checkpoint save, `SUCCESS_VALIDATED` DML record, CMA
reinforcement, final Rhino acceptance, or Blender import may occur until this
post-mutation object-and-vision pair passes. There is no fixed mutation-count
gate between these phase boundaries.

## Phase sequence

Read and execute only these four Cliff-House-style phase prompts in order:

1. `02a_phase_site_shell.md`
2. `02b_phase_stage_led.md`
3. `02c_phase_rooms_access.md`
4. `02d_phase_rigging_cameras.md`

After phase 4 passes, write `work/vp_studio_01_estimated_load.md` from the brief's
transparent arithmetic. This is a documentation task, not a Rhino phase, and
must not create electrical, mechanical, data, or fire-protection geometry.

Before every phase, query DML once for prior geometry decisions, failures, and
acceptance evidence, then call CMA augment once with the proposed phase plan.
Ingest one compact record when the phase passes, or immediately after a real
failure/partial mutation. Do not insert DML calls or records between ordinary
successful geometry groups. Reinforce only validated phase success.

## Coordinate and units contract

- Units: inches.
- Origin: southwest lot corner at `(0,0,0)`.
- +X: east; +Y: north; +Z: up.
- Finished stage floor elevation: 0 in local building datum.
- Absolute tolerance: 0.01 in; angle tolerance: 0.1 degrees.
- Keep geometry within a numerically stable distance of the origin.

## Required layer tree

Create layers as they become necessary; do not create empty layers merely to
inflate a checklist. Use these canonical paths:

- `00_REFERENCE::Lot_Datum`, `00_REFERENCE::Clearances`
- `01_SITE::Property`, `01_SITE::Drives_Loading`, `01_SITE::Parking_Service`
- `02_ARCH::Shell`, `02_ARCH::Stage_Floor`, `02_ARCH::Interior_Partitions`
- `02_ARCH::Doors_Loading`, `02_ARCH::Rooms_Ancillary`
- `03_LED::Main_Wall`, `03_LED::Ceiling`, `03_LED::Floor_Alternate`, `03_LED::Support_ServiceZone`
- `04_RIGGING::Grid_Catwalks`, `04_RIGGING::Hoist_Envelopes`
- `05_CAMERA::Bodies`, `05_CAMERA::Frustums`, `05_CAMERA::Movement_Envelopes`, `05_CAMERA::Tracking_Sensors`
- `06_EQUIPMENT::Furniture`, `06_EQUIPMENT::Workstations`,
  `06_EQUIPMENT::Carts_Cases`, `06_EQUIPMENT::Practical_Lights`
- `08_CIRCULATION::Egress_Clear`, `90_ANNOTATION::Room_Tags`,
  `99_VALIDATION::Issues`

## Object identity and metadata

Choose stable uppercase names that communicate design intent, such as
`ARCH_STAGE_FLOOR`, `LED_MAIN_WALL_SEGMENT_01`, `CHAIR_CONTROL_01`, and
`CAM_A_HERO_TRACKED`. Do not rely on autogenerated names.

Every modeled object receives User Text for `project=vp-studio-01`, `discipline`,
`system`, `agentic_phase`, `phase=SCHEMATIC`, `assumption_status`, `source_basis`,
and `export_to_blender`. Do not create modeled electrical or HVAC objects.

## Save discipline

Never invoke interactive Save/SaveAs commands and do not save periodically. The
model remains live in Rhino while the four phases are developed. After the final
audit passes, call `mcp_rhino_save_doc` exactly once to a new timestamped path
under `work/`. If the save fails, stop; do not retry through a command macro.

## Final Rhino acceptance gate

Before claiming completion:

- Report dynamic object counts by agentic phase and layer; no fixed count is a
  design target.
- Confirm the 300 ft x 400 ft lot, approximately 180 ft x 150 ft building,
  minimum 120 ft x 100 ft x 40 ft clear stage, and 80 ft diameter x 24 ft high
  180-degree LED volume numerically.
- Confirm required rooms, loading path, camera names/envelopes, rigging zones,
  chairs, workstations, production equipment, and clear circulation.
- Confirm there is no electrical, mechanical, data-distribution, or
  fire-protection geometry and that the separate estimated-load note exists.
- Confirm stable unique names, required User Text, valid geometry, intended
  closed solids, and no accidental duplicates.
- Capture plan, stage interior, exterior axonometric, and equipment-layout views.
- Save once, re-query the document, and ingest the artifact path plus objective
  evidence into DML.
