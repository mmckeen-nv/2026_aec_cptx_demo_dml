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
- Both execution tools require the exact argument name `script`. This
  installation is Rhino MCP Platform 0.1.5 with Rhino 8 CPython: use
  `doc = __rhino_doc__`; `doc.Layers.FindByFullPath(path, True)` returns an
  integer index (`-1` when absent), not a Layer object; and
  `rhinoscriptsyntax.LayerIndex` plus `rhinoscriptsyntax.ObjectAttributes` do
  not exist. Use `Rhino.DocObjects.ObjectAttributes`, set its integer
  `LayerIndex`, `Name`, and User Text, and pass it to the applicable
  `doc.Objects.Add*` method. Create nested layers parent-first with
  `Rhino.DocObjects.Layer` and `ParentLayerId`. Never assign layer index `-1`.
- Inspect `payload.error` and stdout after every script. A transport-level MCP
  success can still contain a Rhino script error or create zero objects.
- Never call `mcp_rhino_run_command`. Even apparently harmless macros can wait
  for interactive input and deadlock the MCP request. Use dedicated camera,
  zoom, selection, open, and save tools or direct bounded Python/C#.
- Rhino MCP 0.1.5 returns `get_viewport_image` as nested base64, not a usable
  URL. Never invent a URL and never copy that base64 into `execute_code`.
  Do not loop on `mcp_rhino_get_viewport_image`. Save the active view with one
  read-only Rhino Python call; the controller treats the successful
  `CaptureToBitmap` call itself as the viewport checkpoint:

  ```python
  import System
  view = __rhino_doc__.Views.ActiveView
  bitmap = view.CaptureToBitmap(System.Drawing.Size(960, 540))
  image_path = r"C:\absolute\demo\work\rhino_phase_view.png"
  bitmap.Save(image_path)
  print(image_path)
  ```

  You must call `vision_analyze(image_url=image_path, question=...)` with that absolute
  local path. Capture alone is not visual validation. Ask only for the phase gate:
  whether required elements are visible, whether a named clearance/overlap defect is
  present, and a short PASS/REVISE verdict. Do not request a general description,
  inventory, tutorial, or restatement of the image.
- Keep inspection evidence bounded. Call `mcp_rhino_list_objects` once after the
  final mutation group for a phase, then distill its result into counts, missing
  required names, invalid/open geometry counts, and bounds. Do not echo, rewrite,
  or reread the full object payload, and do not repeat it unless geometry changes.
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
- Rhino and Blender visual gates are independent. After Blender mutation, call
  `mcp_blender_get_viewport_screenshot` once, then call `vision_analyze` on that
  screenshot's local path and require a literal PASS verdict. Never rerun Rhino
  validation merely because Blender changed.

## Daystrom DML and CMA

- Use `mcp_daystrom_dml_stats` and a phase-specific `mcp_daystrom_dml_query` before planning.
- Use `mcp_cma_augment` for the consequential plan after retrieval.
- Write and ingest one compact record after a validated phase success or a real
  failure/partial mutation. Do not record every ordinary successful geometry call.
- The launcher/controller pre-creates `work/dml_events/`. At every validated
  phase save, write one compact `work/dml_events/phase_N_state.md`
  record capped at 1,200 characters. Include only phase, accepted decisions,
  objective counts/bounds, local viewport and `.3dm` paths, vision PASS/REVISE,
  remaining defects, and the next phase. Ingest it immediately and use this record,
  not raw prior tool output, as the next phase's retrieval context.
- Start every new phase with one phase-specific DML query and one CMA augmentation.
  Do not paste retrieved documents back into the conversation; cite their short
  source names and apply only the relevant decisions.
- Reinforce only a validated success with `mcp_cma_reinforce`. Failures are DML avoidance knowledge, never CMA reinforcement.
- A retry is allowed only after retrieving the prior attempt and materially changing the approach.

Tool output is the phase-gate evidence. A prose claim without a fresh MCP inspection is not validation.
