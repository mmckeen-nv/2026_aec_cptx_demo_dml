# Profile bootstrap

Use the working directory's startup prompt, `skills/INDEX.md`, session state,
project prompt, and current numbered phase prompt. Do not add a second workflow
or orchestration layer at profile scope. Daystrom DML remains advisory memory.

The canonical workflow has two execution styles. Manual mode keeps the original
object-by-object pacing and review gates. The explicit trigger "Run the Cliff
House build automatically" selects
`cliff-house-automatic-run.txt`, which batches the same phases using the
validated production fast path. This is mode routing inside the existing
workflow, not a second orchestration layer. Call it an automatic run, never a
benchmark, in user-facing output.

## Application lifecycle boundary

Rhino is started and owned by the operator/launcher. Use the adopted Rhino
session, but never spawn, close, restart, or replace a Rhino slot and never
close or reopen the active Rhino document. In particular, never call
`mcp__rhino__spawn_slot` or `mcp__rhino__close_slot`. If Rhino becomes
unreachable, preserve the application and document, stop retrying lifecycle
operations, and report the connection failure so the router or Hermes can be
reconnected without terminating Rhino.

Daystrom DML contains prior successful experience with these tool calls. When
the memory provider recalls a procedure that clearly applies to the current
tool and phase, prefer its validated tool envelope and scaffold, keep the
analysis brief, and move directly to execution instead of deriving the same
approach again. This is a soft preference, not blind replay: the current scene,
canonical geometry contract, and live validation remain authoritative. Reason
normally when recalled memory is absent, irrelevant, conflicts with the current
contract, or produces a real tool failure. The memory provider normally recalls
relevant procedures automatically; do not repeat that recall with an explicit
DML query merely for reassurance. If no applicable procedural memory was
surfaced, one explicit query is allowed before authoring Rhino scripts, and a
later query is appropriate only after a relevant tool failure or context
compression. Use procedural tool memory, not generic project recall.

Geometry mutation uses
`mcp__rhino__run_csharp`; Rhino Python is read-only inspection or capture. A
non-empty nested `payload.error`, exception, or traceback is a tool failure
even if MCP transport reports success. Never repeat the same failure twice.
