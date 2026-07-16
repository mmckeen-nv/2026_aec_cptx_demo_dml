# Teapot durable workflow knowledge

- project_id: `project:teapot-01`
- BAC Teapot is Blender-only; Rhino is never used in this demo.
- The authoritative geometry is `demos/teapot/utah_teapot.obj`, SHA-256
  `a447b8936e70678c70438a4155b6ef5310c4d0a647cee362f84d53c8b38baf9f`.
- Build through `build_canonical_teapot()` loaded inside Blender MCP.
- Require four named meshes, 0.30 m width, Z=0 ground contact, material,
  camera, three lights, and visible preview evidence.
- DML records validated successes and failures; it does not control tool calls.
