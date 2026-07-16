# MCP operations reference

Consult this file only when a tool name, argument, or installed-version behavior
is unclear. It is a reference, not a mandatory per-turn checklist.

## Execution rhythm

Follow the original Cliff House pattern:

1. Inspect the owning application and read the current phase prompt.
2. Plan one coherent manifest assembly that belongs to the current phase.
3. Author one bounded inline mutation and execute it through Rhino MCP. The call
   may create all named constituent objects and must print their bounds.
4. Complete the phase with its embedded C# scaffold, then run one read-only numeric
   validator. Do not inspect after every object.
5. After `NUMERIC_PASS`, capture one useful view, ask local Nemotron vision for
   concrete feedback, and make targeted corrections.
6. Revalidate and save one useful phase checkpoint.

Do not author a whole-studio builder. A phase-bounded assembly call is expected:
for example, the shell, the smooth LED assembly, the room bar, the truss grid,
or the scheduled camera set. Do not split repeated furniture, lights, wall
segments, or truss members into one-object calls.

## Rhino 8 / Rhino MCP Platform 0.1.5

- Use the launcher-owned ready slot on `127.0.0.1:10500`. Do not spawn, close,
  or replace it while healthy.
- Start VP Studio from `source/vp_studio_01_template.3dm` with
  `mcp_rhino_open_doc`.
- Execute geometry with `mcp_rhino_run_csharp(script=...)`. Copy the current
  phase scaffold exactly. Python is permitted only for read-only inspection or
  viewport capture. Never use
  terminal, execute_code, a desktop file association, Rhino's editor, or
  `mcp_rhino_run_command`.
- In C# use the injected `doc`, absolute `Interval` values, `Box.ToBrep()`, and
  prebuilt `ObjectAttributes`. Treat `Objects.Add*` results as `Guid`.
- Inspect both the MCP result and script output. Transport success does not prove
  that geometry was created.
- Keep mutation code inline and phase-bounded. Do not patch a local script
  between dozens of tiny calls, and do not use `open`, `compile`, or `exec` to
  hide a whole-studio builder behind a short call.
- Never call `mcp_rhino_run_command` during this workflow. Avoid modal command
  macros, `_RunPythonScript`, the Python editor, and interactive Save/Export
  dialogs. Use direct MCP tools and RhinoCommon.
- Save with `mcp_rhino_save_doc`.

For visual review, call `mcp_rhino_get_viewport_image` once after
`NUMERIC_PASS`; Hermes routes that fresh image to the configured local vision
model. If an explicit local file is required, capture it with a small inline
`mcp_rhino_run_python` call using `ActiveView.CaptureToBitmap`—never by opening
or replaying a `.py` file. Ask for concrete current-phase defects, not a general
description, and never repeatedly capture an unchanged view.

## Blender

- Use the existing bridge on `127.0.0.1:9876`.
- Inspect with `mcp_blender_get_scene_info`.
- Execute Blender Python only with
  `mcp_blender_execute_blender_code(code=...)`. No generic tool named `run`
  exists.
- The shared importer and validator are at
  `../../skills/import_with_metadata.py` and
  `../../skills/validate_blender_scene.py` from the VP demo directory.
- Preserve the `.3dm` handoff, names, layers, metadata, units, and per-axis
  bounds. Do not substitute OBJ/FBX when the direct handoff is available.
- After meaningful asset/material/lighting work, capture a Blender viewport or
  render and use vision for concrete corrections before the final render.

If a registered application bridge is unavailable, report the exact preflight
blocker. Do not patch Hermes, repair add-ons, or launch duplicate application
instances from inside the demo run.

## Daystrom and CMA

Active-read is automatic. Query when prior experience is useful, ingest one
compact record capped at 1,200 characters at a meaningful success or failure,
and reinforce only validated success. These calls support the agent; they never
gate ordinary Rhino, Blender, or ComfyUI work.
