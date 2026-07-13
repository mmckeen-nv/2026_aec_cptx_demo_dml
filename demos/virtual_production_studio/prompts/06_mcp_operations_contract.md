# MCP operations contract

Use the configured application MCP servers as stateful application bridges. Inspect before mutating, make one bounded change, then inspect again and record evidence.

## Rhino

- The configured Rhino router and the existing Rhino 8 slot on `127.0.0.1:10500` are authoritative.
- Call `mcp_rhino_list_slots`, attach to the ready slot, and never spawn a replacement while that slot is healthy.
- Author bounded Python or C# directly for one coherent element group at a time
  and send it through `mcp_rhino_run_python` or `mcp_rhino_run_csharp`. Inspect
  after every mutation. Do not execute a disk geometry script, JSON object plan,
  or complete studio builder. Use `mcp_rhino_save_doc` for the single gated save.
- Never drive interactive `Export`, `Save`, or `SaveAs` commands. If Rhino reports that a command is already running, cancel the pending interactive command, re-list the slot, and probe `run_python` before diagnosing MCP or Python.
- For Blender handoff, generate render meshes and save a metadata-bearing `.3dm`; do not invent OBJ or FBX export paths.

## Blender

- Use the configured Blender MCP bridge on `127.0.0.1:9876`; do not launch a second Blender bridge when it is ready.
- Inspect with `mcp_blender_get_scene_info` before mutation. Execute Blender
  Python only with `mcp_blender_execute_blender_code` and its `code` argument.
  Never emit a tool call named `run`; that tool does not exist.
- The working directory is `demos/virtual_production_studio`. Read the checked-in
  `../../skills/import_with_metadata.py` for Rhino handoff and
  `../../skills/validate_blender_scene.py` for the acceptance gate. There is no
  demo-local `skills/` directory.
- Do not substitute an improvised importer or advance to ComfyUI until object counts, metadata, units, and bounds pass.

## Daystrom DML and CMA

- Use `mcp_daystrom_dml_stats` and a phase-specific `mcp_daystrom_dml_query` before planning.
- Use `mcp_cma_augment` for the consequential plan after retrieval.
- Write and ingest a structured attempt record after every consequential success or failure. Confirm the ingest reports at least one file.
- Reinforce only a validated success with `mcp_cma_reinforce`. Failures are DML avoidance knowledge, never CMA reinforcement.
- A retry is allowed only after retrieving the prior attempt and materially changing the approach.

Tool output is the phase-gate evidence. A prose claim without a fresh MCP inspection is not validation.
