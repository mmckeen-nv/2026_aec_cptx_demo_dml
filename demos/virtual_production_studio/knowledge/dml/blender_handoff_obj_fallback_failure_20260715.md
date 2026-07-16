---
project: vp-studio-01
memory_class: failure_event
phase: rhino_to_blender
outcome: FAILURE_VALIDATED
status: CURRENT_POLICY
source: rtx_pro logs and vp_studio_01.3dm inspection on 2026-07-15
validation: saved file contained 206 Breps, zero Mesh objects, and zero Brep face render meshes; agent probed obsolete Blender add-on APIs, improvised OBJ, parsed global indices as local indices, and lost the Blender bridge
---

# Deterministic Rhino-to-Blender recovery

Never use OBJ, FBX, Blender import add-ons, `bpy.ops.import_scene`, or a
handwritten vertex/face parser. Before saving the handoff `.3dm`, run the exact
C# scaffold in `prompts/07_phase_export_blender.md`: call
`Mesh.CreateFromBrep`, append every nonempty returned mesh part, validate X/Y/Z
bounds against the source Brep, copy name/layer/User Text, and require
`HANDOFF_MESH_PASS`.

In Blender, load `skills/import_with_metadata.py` through
`mcp_blender_execute_blender_code` and require `VP_HANDOFF_PASS`. Rhino and
Blender are both Z-up, so import vertices as `(X,Y,Z)` with only the inch-to-metre
scale; never swap Y and Z or apply a corrective 90-degree rotation. Architectural
coplanar contacts remain diagnostics unless strict validation is explicitly
requested.
