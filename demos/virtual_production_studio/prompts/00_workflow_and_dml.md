# VP Studio session startup

The active project is `vp-studio-01`. The working directory is this demo root.
All paths in the VP prompt suite are relative to this directory.

## Session startup

1. Read `skills/INDEX.md` and `skills/session_state.md`.
2. Read `user_prompts/project_prompt.md`.
3. Confirm Rhino, Blender, ComfyUI, DML, and CMA status once.
4. Open `source/vp_studio_01_template.3dm` only if the launcher-owned Rhino
   document is not already that file.
5. Read only the current numbered phase prompt.

Determine that phase only from live Rhino object names and numeric bounds, using
the ordered table in `system_prompts/00_session_startup.md`. Ignore existing
checkpoint files from previous runs. A user request such as "next phase" means
"run the first incomplete live-document phase," not "increment a remembered
phase number."

## Phase execution

Each phase uses the Cliff House rhythm:

1. inspect the active scene and read-only reference geometry;
2. explain the immediate design move briefly;
3. create coherent manifest assemblies with the tested phase C# scaffold;
4. run the phase numeric validator after the meaningful group is complete;
5. only after `NUMERIC_PASS`, capture the current viewport, ask local vision a focused design question, and
   correct concrete visible defects;
6. present the review gate and save one checkpoint after acceptance.

Do not create later-phase objects early. Do not generate or replay a monolithic
studio builder. Small helper code may be reused inside a call, and one bounded
call may create all named constituents or repeated instances of one assembly.
Rhino geometry mutations execute only through `mcp_rhino_run_csharp` with the
current phase's embedded scaffold. Python is read-only.

Use direct metadata-preserving `.3dm` handoff. OBJ and FBX are prohibited.
ComfyUI processes only an approved Blender render. Its fixed first stage uses
SDXL plus depth ControlNet; its fixed second stage uses the accepted SDXL image
as FLUX.2 Klein reference conditioning. It enhances presentation and never
replaces modeled design, changes camera/layout, or authorizes invented objects.

At Blender handoff, remain in the launcher-owned generic scene. Do not open,
append, or reuse any `.blend`. Call the checked-in current-handoff helper; it
clears generic/stale scene data, imports exactly `rhino/vp_studio_01.3dm`, and
fingerprints that source before production work begins.

The handoff is a one-way phase boundary. After `VP_HANDOFF_PASS`, never call
any `mcp_rhino_*` tool again in that run. Blender MCP exclusively owns import,
assets, materials, lighting, cameras, and rendering. After a composition-gated
`VP_RENDER_PASS`, the registered terminal tool exclusively runs the checked-in
ComfyUI helper. Require `COMFY_SDXL_OUTPUT_PASS`, `COMFY_FLUX_OUTPUT_PASS`, and
`COMFY_OUTPUT_PASS stage=sdxl+flux`. Rhino is never an execution path for
Blender or ComfyUI.

Daystrom active-read provides continuity automatically. Use memory sparingly at
phase boundaries; never insert DML/CMA ceremony between visible modeling calls.
