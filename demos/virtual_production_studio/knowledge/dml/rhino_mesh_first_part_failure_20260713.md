---
status: CURRENT_POLICY
project_id: project:vp-studio-01
phase: rhino-to-blender
outcome: FAILURE_VALIDATED
approach_signature: mesh_create_from_brep_take_first_part
artifact_path: work/vp_studio_01_handoff.3dm
observed_evidence: 123 Breps and 123 Mesh objects passed count equality, but most imported meshes had a zero Y extent and Blender screenshots showed disconnected flat sheets
root_cause: Mesh.CreateFromBrep returned Mesh[] and the handoff operation retained only the first face mesh for each Brep
avoidance_rule: append every nonempty Mesh.CreateFromBrep array member into one joined mesh and require per-object source-Brep versus joined-mesh bounding-box parity before save
visual_gate: inspect plan and axonometric Blender MCP screenshots; count equality alone never passes
material_gate: require material custom-property metadata at handoff and require Blender material slots only after the material phase
---

This failure must be retrieved before future Rhino-to-Blender handoffs. The agent
owns the repair through Rhino and Blender MCP. It must not report success, advance,
or delegate cleanup when any joined mesh loses a source axis, extent, name, or
metadata field.
