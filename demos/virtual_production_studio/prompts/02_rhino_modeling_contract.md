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
3. Call `vision_analyze` with the image URL returned by that capture and a
   phase-specific question about massing, proportion, scale, circulation, LED
   geometry, sightlines, collisions, floating geometry, and omissions. A
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

Read and execute these Cliff-House-style phase prompts in order:

1. `02a_phase_site_shell.md`
2. `02b_phase_stage_led.md`
3. `02c_phase_rooms_access.md`
4. `02d_phase_rigging_cameras.md`
5. `02e_phase_electrical_mechanical.md`
6. `02f_phase_life_safety_data.md`

Before every phase, query DML for the phase, prior geometry decisions, failures,
and acceptance evidence, then call CMA augment with the proposed design and MCP
operation. After every bounded mutation, validate and ingest a success or failure
event under `work/dml_events/`. Reinforce only validated success.

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
- `06_ELECTRICAL::Service_Distribution`, `06_ELECTRICAL::LED_Power`, `06_ELECTRICAL::Technical_Power_UPS`, `06_ELECTRICAL::Lighting_CompanySwitch`
- `07_MECHANICAL::Equipment_Zones`, `07_MECHANICAL::Stage_Air_Paths`
- `08_LIFE_SAFETY::Egress`, `08_LIFE_SAFETY::Fire_Access`
- `09_DATA::Control_Tracking_Networks`
- `90_ANNOTATION::Room_Load_Tags`, `99_VALIDATION::Issues`

## Object identity and metadata

Choose stable uppercase names that communicate design intent, such as
`ARCH_STAGE_FLOOR`, `LED_MAIN_WALL_SEGMENT_01`, `ELEC_LED_DIST_ZONE_A`, and
`CAM_A_HERO_TRACKED`. Do not rely on autogenerated names.

Every modeled object receives User Text for `project=vp-studio-01`, `discipline`,
`system`, `agentic_phase`, `phase=SCHEMATIC`, `assumption_status`, `source_basis`,
and `export_to_blender`. Electrical objects also carry applicable connected-load
and voltage-basis metadata plus `engineering_status=NOT_FOR_CONSTRUCTION`.

## Save discipline

Never invoke interactive Save/SaveAs commands and do not save periodically. The
model remains live in Rhino while the six phases are developed. After the final
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
  electrical/mechanical allowances, egress, and data/control zones.
- Confirm stable unique names, required User Text, valid geometry, intended
  closed solids, and no accidental duplicates.
- Capture plan, stage interior, exterior axonometric, and services-zone views.
- Save once, re-query the document, and ingest the artifact path plus objective
  evidence into DML.
