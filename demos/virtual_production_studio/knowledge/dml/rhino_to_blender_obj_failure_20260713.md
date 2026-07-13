# DML attempt event
event_id: vp-studio-01-rhino-to-blender-20260713T195200Z-manual-obj
project: vp-studio-01
phase: rhino-to-blender
application: pipeline
operation: export_import_rhino_obj
approach_signature: rhino-to-blender|hand-written-obj|local-face-indices|flattened|repeated-inch-meter-scaling
outcome: FAILURE_PARTIAL_MUTATION
validation_status: FAILED
artifact_path: G:\AEC-CPTX\demos\virtual_production_studio\work\vp_studio_01_20260713_140000_scaled.obj
source_provenance: improvised mcp_rhino_run_python OBJ writer followed by repeated mcp_blender_execute_blender_code repairs
expected_gate: 98 individually identifiable objects, preserved names/layers/metadata, dimensions approximately 121.92x91.44x16.00 m, valid topology, one unit conversion
observed_evidence: Blender contained one anonymous mesh with 24903 vertices and 7847 faces plus duplicate cameras/lights; renders showed faces radiating toward early vertices; scale was applied repeatedly across partially failing scripts
error: OBJ faces used per-mesh local indices without cumulative vertex offsets; quad D vertices were omitted; object groups and metadata were absent
root_cause: The manual exporter appended vertices from multiple Rhino meshes but wrote each face as A+1/B+1/C+1, so later faces referenced the first mesh vertices. Subsequent retries treated topology corruption as normals, rotation, lighting, and camera problems and repeatedly converted inches to meters.
avoidance_rule: Never reuse this OBJ or this manual writer. Never repair a failed topology gate with normals, materials, lights, cameras, or renders. Never reapply unit conversion after partial mutation without measuring current bounds.
reusable_recipe: NONE
next_safe_action: Return to the validated 3dm and use a checked-in tested structured handoff that preserves objects and applies unit conversion exactly once; validate counts, names, bounds, and topology before Blender scene work
timestamp_utc: 2026-07-13T19:52:00Z
