# Current Rhino workflow policy
project: vp-studio-01
phase: rhino
operation: agent-authored-studio-design
status: CURRENT_POLICY
supersedes: build_rhino_massing.py and every historical fixed-98-object builder recipe
source_provenance: user direction and current demos/virtual_production_studio prompt contract
decision: Hermes must design and generate the VP Studio geometry itself through narrow Rhino MCP calls paced like the original Cliff House demo.
required_method: Read the brief, prompts/01a_locked_scene_manifest.md, and only the current phase prompt; use DML/CMA as advisory context; author Python or C# directly for one manifest-defined bounded assembly; execute through Rhino MCP; print and validate world bounds; inspect at recognizable checkpoints; complete the phase review gate and checkpoint save; then load the next phase.
prohibited_method: Do not execute a checked-in geometry builder, import a JSON object schedule, call exec(open(...)) for geometry, copy an earlier complete 3dm, target 98 objects, or build the studio in one MCP call.
validation_policy: Use dynamic object counts and semantic gates for dimensions, names, layers, metadata, phase completeness, and viewport evidence. The Rhino-to-Blender source count is whatever the accepted agent-authored Rhino model contains.
locked_manifest_policy: The scene manifest is the numeric authority. Use inches, datum (0,0,0), absolute coordinates, explicit curve centers, and listed containment envelopes. Never invent a phase-local origin or accept visual review before numeric containment passes.
scope_policy: Model only the building, LED volume, rooms/access, rigging, cameras, chairs, workstations, and physical production equipment. Electrical/HVAC/data/fire systems are documentation-only and must not become geometry.
quality_policy: Finished architecture must be recognizable geometry, not anonymous boxes. Build the LED wall as a thin smooth continuous curved assembly; panel intent must not create a thick faceted ring of cuboids.
blender_policy: After the metadata-preserving handoff, replace every visible required equipment/furniture proxy with approved cached assets, assign actual materials, and complete motivated LED/key/fill/rim/practical lighting before beauty rendering or ComfyUI.
load_note_policy: Write work/vp_studio_01_estimated_load.md with transparent planning arithmetic; do not infer a service size or engineering design.
save_policy: Do not trigger interactive or timer-based saves. Save once through mcp_rhino_save_doc after each accepted Rhino phase review gate, using a distinct checkpoint path.
dml_policy: Historical builder successes remain factual records of earlier runs but are obsolete as reusable recipes and must not control a new run.
timestamp_utc: 2026-07-13T22:45:00Z
