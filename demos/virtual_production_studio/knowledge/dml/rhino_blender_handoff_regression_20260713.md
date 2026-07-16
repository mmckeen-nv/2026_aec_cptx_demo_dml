# DML attempt event
event_id: vp-studio-01-rhino-to-blender-20260713T203300Z-context-regression
project: vp-studio-01
phase: rhino-to-blender
application: pipeline
operation: select_and_execute_handoff
approach_signature: active-vp-contract|missing-original-phase07|interactive-export|obsolete-rhino3dm-importer
outcome: FAILURE_VALIDATED
validation_status: FAILED
artifact_path: C:\Users\test\2026_aec_cptx_demo_dml\demos\virtual_production_studio\work\vp_studio_01_20260713_200000.3dm
source_provenance: comparison with repository baseline commit 09b15e6 and live Rhino/Blender MCP audits
expected_gate: original direct 3dm metadata handoff imports 98 named Breps into Blender
observed_evidence: active VP contract omitted system_prompts/07_phase_export_blender.md and skills/import_with_metadata.py, so the agent improvised OBJ; an interactive Export command remained active and made later run_python calls return empty; the saved 3dm had zero embedded render meshes; the original importer used removed rhino3dm 8.17 APIs ToFloatArray and ToIntArray
error: handoff authority was dropped from active context and runtime compatibility was not tested
root_cause: deployment retained the original importer but the demo-specific prompt stopped loading it; the massing save did not require embedded render meshes; the importer was not updated for rhino3dm 8.17
avoidance_rule: Always load the original Phase 07 handoff and metadata importer. Never use interactive Rhino Export, OBJ, or FBX. Require 98 Breps with render meshes before import. Treat an already-running Rhino command as a command-state blocker and cancel it before diagnosing MCP execution.
reusable_recipe: NONE
next_safe_action: use the validated direct-3dm handoff recipe recorded in rhino_to_blender_3dm_success_20260713.md
timestamp_utc: 2026-07-13T20:33:00Z
