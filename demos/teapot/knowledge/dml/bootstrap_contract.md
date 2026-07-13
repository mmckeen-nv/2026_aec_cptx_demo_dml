# Teapot durable workflow knowledge

- project_id: `project:teapot-01`
- Blender MCP is the primary scene bridge; Rhino MCP is used for source `.3dm` inspection or regeneration.
- Inspect through MCP before mutation and validate after one bounded change.
- Prefer the metadata-bearing `.3dm` path through `skills/import_with_metadata.py`; do not improvise OBJ/FBX handoffs.
- Record validated successes and failures in DML. Reinforce only validated successes into CMA.
