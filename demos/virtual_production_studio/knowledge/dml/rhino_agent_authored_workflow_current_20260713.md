# Current Rhino workflow policy
project: vp-studio-01
phase: rhino
operation: agent-authored-studio-design
status: CURRENT_POLICY
supersedes: build_rhino_massing.py and every historical fixed-98-object builder recipe
source_provenance: user direction and current demos/virtual_production_studio prompt contract
decision: Hermes must design and generate the VP Studio geometry itself through bounded Rhino MCP calls.
required_method: Read the brief and current phase prompt; query DML; augment the proposed design through CMA; author Python or C# directly for one coherent element group; execute through Rhino MCP; inspect the resulting application state; record the attempt; then continue to the next group.
prohibited_method: Do not execute a checked-in geometry builder, import a JSON object schedule, call exec(open(...)) for geometry, copy an earlier complete 3dm, target 98 objects, or build the studio in one MCP call.
validation_policy: Use dynamic object counts and semantic gates for dimensions, names, layers, metadata, phase completeness, and viewport evidence. The Rhino-to-Blender source count is whatever the accepted agent-authored Rhino model contains.
scope_policy: Model only the building, LED volume, rooms/access, rigging, cameras, chairs, workstations, and physical production equipment. Electrical/HVAC/data/fire systems are documentation-only and must not become geometry.
load_note_policy: Write work/vp_studio_01_estimated_load.md with transparent planning arithmetic; do not infer a service size or engineering design.
save_policy: Do not save periodically. Save exactly once through mcp_rhino_save_doc after all four Rhino subphases and the full audit pass.
dml_policy: Historical builder successes remain factual records of earlier runs but are obsolete as reusable recipes and must not control a new run.
timestamp_utc: 2026-07-13T22:45:00Z
