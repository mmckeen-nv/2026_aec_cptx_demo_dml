# Cliff House compatibility entry point

Project memory namespace: `project:cliff-house-01`.

The canonical Cliff House workflow runs from repository root, exactly like the
pristine control. If this directory is opened directly, first read:

1. `../../system_prompts/00_session_startup.md`
2. `../../skills/INDEX.md`
3. `../../skills/session_state.md`
4. `../../aa_demo_versions/cliff_house_02/user_prompts/project_prompt.md`
5. `../../hermes/DEMO_RULES.md`
6. only the current numbered phase prompt under `../../system_prompts/`

The original pacing is authoritative: one visible object per MCP call, a short
unannounced pause between objects, narrow phase scope, review gate, and named
checkpoint. Do not replace that with coherent multi-object scripts or a second
controller workflow. Daystrom DML supplies advisory continuity and compact
validated lessons; it does not gate calls.

The launcher owns application lifecycle. Never spawn/close Rhino slots, close
or reopen the active document, or launch/repair Blender from the run.
