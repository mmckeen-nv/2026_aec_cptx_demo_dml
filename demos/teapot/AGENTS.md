# BAC Teapot demo

Project memory namespace: `project:teapot-01`.

BAC Teapot is Blender-only. Rhino is not part of this demo. Its secondary HERO
lane uses the immutable `hero/BAC_TEAPOT_HERO.blend`; do not use the standalone
Cliff House HERO scene. The Cliff House and Virtual Production Studio demos
keep their workflows unchanged.

BAC HERO pool dressing has two mandatory audience gates. Only an explicit
"add the floaties" request may call `add_pool_floaties`; render and stylize that
stage, then stop. Only a later, separate "add the other pool assets" request may
call `add_pool_furniture`. Never call both functions in one turn and never call
the disabled all-at-once helper. The checked-in helper exclusively owns the
verified pool, deck, north-patio coordinates, hashes, and 1:1000 conversion.

At startup read, in order:

1. `system_prompts/00_session_startup.md`
2. `skills/INDEX.md`
3. `skills/session_state.md`
4. `user_prompts/project_prompt.md`
5. `prompts/01_locked_teapot_manifest.md`
6. only the current numbered phase prompt

Use Blender MCP and the checked-in helper to construct the verified 1987 Frank
Crow Utah teapot directly from `utah_teapot.obj`. Require the canonical hash,
topology, names, 0.30 m width, and ground contact before staging or materials.
Never substitute primitives or run external scripts. After the first preview,
allow natural audience-directed material and presentation requests. DML is
advisory continuity, not turn-by-turn control.

Startup is intentionally idle. Do not construct anything until the user gives a
natural-language build request such as "let's build a Utah teapot".

If the user explicitly asks to stylize the current teapot render, use only
`skills/comfyui_teapot.py` through the terminal after a valid
`TEAPOT_PREVIEW_PASS`. It runs SDXL depth conditioning followed by FLUX.2 Klein
reference refinement and must end at `COMFY_OUTPUT_PASS stage=sdxl+flux`.
ComfyUI is optional and user-triggered in this demo; it never rebuilds the
teapot or replaces the open-ended Blender material interaction loop.
