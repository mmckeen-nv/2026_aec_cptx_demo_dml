# DML attempt event
event_id: vp-studio-01-rhino-to-blender-20260713T203800Z-direct-3dm
project: vp-studio-01
phase: rhino-to-blender
application: Rhino and Blender
operation: metadata_preserving_direct_3dm_handoff
approach_signature: direct-3dm|embedded-render-meshes|rhino3dm-8.17|metadata|inches-to-metres-once
outcome: SUCCESS_VALIDATED
validation_status: PASSED
artifact_path: C:\Users\test\2026_aec_cptx_demo_dml\demos\virtual_production_studio\work\vp_studio_01_20260713_200000_handoff.blend
source_provenance: baseline system_prompts/07_phase_export_blender.md plus repaired skills/import_with_metadata.py
expected_gate: 98 individually named project meshes, preserved layer/User Text metadata, correct metre bounds, valid faces, no skipped Breps
observed_evidence: Rhino wrote a 2405788-byte handoff 3dm containing 98 Breps with render meshes and 588 render-mesh fragments. Blender imported 98 objects with zero skipped, 44 layers, 24903 vertices, 19440 faces, 98 unique names, project metadata and rhino_layer on all objects. Bounds were min (0,0,-0.3048) m and max (121.92,91.44,16.002) m. Saved blend contained exactly 98 project objects.
error: NONE
root_cause: NONE
avoidance_rule: Do not substitute OBJ/FBX or apply a second unit conversion
reusable_recipe: Cancel any pending Rhino command; create MeshType.Render meshes for every managed Brep; save a new 3dm with WriteUserData and IncludeRenderMeshes; audit the 3dm from Blender with rhino3dm; execute skills/import_with_metadata.py; validate 98 objects, names, metadata, faces, and metre bounds before scene work
next_safe_action: proceed to Blender production-scene materials, assets, cameras, and lighting
timestamp_utc: 2026-07-13T20:38:00Z
