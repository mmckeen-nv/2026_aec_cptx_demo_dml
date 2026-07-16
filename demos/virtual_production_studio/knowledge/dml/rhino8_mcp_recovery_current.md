---
project: vp-studio-01
memory_class: current_recovery_recipe
phase: rhino
outcome: VALIDATED
supersedes: hard-turn-limit VP execution rails
---

# Current Rhino 8 MCP recovery recipe

Match the original Cliff House execution style. DML advises; it does not police
turns. There is no hard mutation-call limit. Build coherent assemblies, inspect
them, and make targeted corrections without trapping natural recovery.

Rhino geometry runs inline only through `mcp_rhino_run_csharp(script=...)` using
the exact scaffold embedded in the current phase prompt. Use injected `doc`,
absolute `Interval` values, `Box.ToBrep()`, and prebuilt `ObjectAttributes`.
Every `Objects.Add*` result is a `Guid`, never an ObjectTable integer index.
Python is read-only inspection/capture only; never use it for geometry.

The MCP transport may succeed while Rhino stdout contains a traceback. Any
traceback or nonempty script error means the call failed and must consume zero
mutation budget/state. Correct only the invalid API and retry once.
