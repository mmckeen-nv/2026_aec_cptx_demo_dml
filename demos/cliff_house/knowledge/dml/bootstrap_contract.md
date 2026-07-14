# Cliff House durable workflow knowledge

- project_id: `project:cliff-house-01`
- Rhino is the architectural geometry authority; Blender is the visualization authority.
- Inspect through MCP before mutation and validate after one bounded change.
- Repository root is `../..` from the demo. Transfer Rhino geometry through `../../skills/import_with_metadata.py`; OBJ and FBX are prohibited.
- Join all `Mesh.CreateFromBrep` parts and require per-object X/Y/Z bounding-box parity plus plan/axonometric screenshot inspection; count equality alone is insufficient.
- Use only exact registered tools, including `mcp_blender_execute_blender_code`; no generic `run` tool exists.
- Record validated successes and failures in DML. Reinforce only validated successes into CMA.
