# BAC Teapot Demo Rules

- BAC Teapot is Blender-only. Never call a Rhino tool in this demo.
- Start idle. No Blender mutation is permitted until the user explicitly asks
  to build or start the Utah teapot.
- Read the locked manifest and only the current phase prompt.
- Through Blender MCP, load `skills/blender_teapot_interactions.py` and call
  `build_canonical_teapot(root, reset_scene=True)`.
- Require the locked OBJ SHA-256, 18,530 vertices, 18,432 faces, four named
  component meshes, exact 0.30 m width, and Z=0 ground contact.
- Never substitute primitives, proxy geometry, or the legacy `.3dm`.
- Use `mcp_blender_execute_blender_code(code=...)`; no generic `run` tool exists.
- Never execute an external `.py` file. Loading the checked-in helper inside
  Blender MCP is the only permitted Python path.
- Open-ended material requests may not deform, duplicate, or rebuild geometry.
- DML is advisory and belongs at meaningful boundaries only.
