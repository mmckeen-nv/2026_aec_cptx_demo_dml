# VP Studio Demo Rules

## Session flow

Work through one numbered phase at a time. Briefly announce the design move,
build it visibly, review the group, and wait at the written review gate before
advancing.

## Reference geometry

Objects on `VP00_TEMPLATE_*` layers are read-only. Inspect their geometry and
bounds silently before building. Never modify, duplicate, export, or present
them as finished design.

## Build pacing

- Build one coherent manifest assembly per MCP mutation call. An assembly may
  create all of its named constituent objects (for example the six shell
  solids, one complete camera proxy, or one truss grid), and must print their
  names and world bounds in the same call.
- Use a few coherent assembly mutation calls per Rhino phase, followed by
  targeted corrections when inspection finds a real problem. Do not create one box, chair, light, or
  wall segment per call.
- Do not generate or execute a whole-studio builder. Phase-bounded assembly
  scripts are expected and are not monolithic builders.
- Build only the current phase; later-phase objects are prohibited.
- Once a phase's first Rhino mutation begins, do not patch or write local
  Python/C# files. Compose the bounded script directly in the MCP call.

## Viewport rules

- Start in a useful Perspective or plan view.
- After a phase group, capture the current view to a uniquely named local PNG.
- Analyze that exact new PNG with a focused question.
- Correct concrete visible defects one object at a time.
- Leave Rhino in a useful Perspective view after review.

## Tool rules

- Rhino C# parameter is `script`, not `code`.
- Execute every Rhino geometry mutation with `mcp_rhino_run_csharp(script=...)`
  using the current phase's exact scaffold. Python is read-only. Never execute either language
  from `terminal`, `execute_code`, Rhino command macros, an editor, or a file
  association.
- Blender Python parameter is `code`.
- Add metadata with `SetUserString`.
- Save only with the registered noninteractive save tool.
- Never call Rhino slot spawn/close, document close/reopen, `_New`, interactive
  Save/Export, application launchers, or add-on repair.

## Phase gate

Each phase ends in exactly this order:

1. one read-only Rhino MCP validator prints `NUMERIC_PASS` plus document units,
   tolerances, object names, and manifest comparisons;
2. one fresh viewport PNG is captured through Rhino MCP;
3. local Nemotron vision returns PASS or one focused REVISE list;
4. targeted correction calls followed by numeric revalidation;
5. one noninteractive `mcp_rhino_save_doc` checkpoint.

Never capture vision, advance phase, or save a success checkpoint before
`NUMERIC_PASS`.

## DML

DML supplies advisory continuity. Retrieve at most one relevant recipe at the
start of a phase when useful and record one compact validated lesson at the
end. Never insert memory calls between visible objects.
