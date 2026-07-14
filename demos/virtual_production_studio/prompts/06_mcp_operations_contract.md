# MCP operations contract

Use the configured application MCP servers as stateful application bridges. Inspect before mutating, make one bounded change, then inspect again and record evidence.

## Rhino

- The configured Rhino router and the existing Rhino 8 slot on `127.0.0.1:10500` are authoritative.
- Call `mcp_rhino_list_slots`, attach to the ready slot, and never spawn a replacement while that slot is healthy.
- Start from `source/vp_studio_01_template.3dm`, opened only through
  `mcp_rhino_open_doc`. Never call `_New`, `_NewSmall`, `New`, close the datum
  document, or trigger Rhino's interactive **Open Template File** dialog. Never
  open the completed `vp_studio_01_base_model.3dm` reference artifact.
- Author bounded Python or C# directly for one coherent element group at a time
  and send it through `mcp_rhino_run_python` or `mcp_rhino_run_csharp`. Inspect
  after every mutation. Do not execute a disk geometry script, JSON object plan,
  or complete studio builder. Use `mcp_rhino_save_doc` for the single gated save.
- Never call `mcp_rhino_run_command`. Even apparently harmless macros can wait
  for interactive input and deadlock the MCP request. Use dedicated camera,
  zoom, selection, open, and save tools or direct bounded Python/C#.
- After each required viewport capture, call `vision_analyze` with the returned
  image URL and a specific phase-review question. Capture alone is not visual validation.
- For Blender handoff, generate render meshes and save a metadata-bearing `.3dm`; do not invent OBJ or FBX export paths.

## Blender

- Use the configured Blender MCP bridge on `127.0.0.1:9876`; do not launch a second Blender bridge when it is ready.
- If Blender MCP is absent from the registered tool list, stop and report the
  preflight failure. Never launch Blender, repair/enable add-ons, write startup
  scripts, or use terminal/browser fallbacks from inside the demo.
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
