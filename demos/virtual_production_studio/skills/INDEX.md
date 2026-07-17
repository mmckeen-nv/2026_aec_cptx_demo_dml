# Skills INDEX - VP Studio

## Read this file first

This project is a visible Rhino -> Blender -> ComfyUI demonstration. The
deliverable is an end-to-end workflow that an audience can follow.

## Operating rules

1. Read `skills/session_state.md` second.
2. Read `user_prompts/project_prompt.md`,
   `prompts/01a_locked_scene_manifest.md`, and only the current phase prompt.
3. Check Rhino, Blender, ComfyUI, DML, and CMA once at startup.
4. Create one coherent manifest-defined assembly per application mutation call,
   then print and validate every constituent object's bounds. Use as many
   coherent assembly calls as the phase requires; never degrade into accidental
   one-object retry churn or impose a turn quota.
5. Rhino geometry mutations use only `mcp_rhino_run_csharp(script=...)` and the
   exact C# scaffold embedded in the current phase prompt. Do not discover or
   substitute Python APIs. `skills/rhino_mcp_patterns.md` is the shared C# reference.
6. Use `../../skills/import_with_metadata.py` for `.3dm` import.
7. Use vision at meaningful review gates, not after every object.
8. The launcher owns application lifecycle; never spawn or close slots.
9. Rhino C# geometry executes only through `mcp_rhino_run_csharp`. Rhino Python
   is read-only inspection/capture through `mcp_rhino_run_python`. Do not use
   terminal, execute_code, run-command macros, editors, or file opens.
10. Numeric `NUMERIC_PASS` precedes viewport capture, vision, and checkpoint.
11. For the final ComfyUI phase, read `skills/COMFYUI_COOKBOOK.md` and execute
    only its checked-in two-stage SDXL -> FLUX helper commands, one terminal
    command at a time. Require the SDXL and FLUX stage receipts before accepting
    `COMFY_OUTPUT_PASS stage=sdxl+flux`.

## Pipeline

```text
template/reference audit
  -> site and shell
  -> stage and LED volume
  -> rooms and circulation
  -> rigging/cameras/production layout
  -> metadata-preserving .3dm handoff
  -> Blender assets/materials/lighting
  -> approved render
  -> SDXL depth-conditioned enhancement
  -> FLUX.2 Klein reference refinement
  -> final geometry-preservation review
```

## Source of truth order

1. current phase prompt;
2. locked scene manifest for every numeric value;
3. project prompt;
4. this skill index and Rhino API patterns;
5. compact relevant DML lessons.

Later-phase prompts never expand the current phase scope.
