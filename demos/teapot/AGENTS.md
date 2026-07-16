# BAC Teapot demo

Project memory namespace: `project:teapot-01`.

BAC Teapot is Blender-only. Rhino is not part of this demo. The Cliff House
and Virtual Production Studio demos keep their Rhino workflows unchanged.

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
