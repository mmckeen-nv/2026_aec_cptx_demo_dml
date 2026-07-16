---
project: vp-studio-01
memory_class: workflow_failure
outcome: FAILURE_VALIDATED
status: HISTORICAL_OBSOLETE_DO_NOT_REUSE
superseded_by: rhino_agent_authored_workflow_current_20260713.md
---

# Obsolete session-start plan

The 2026-07-14 session loaded one broad phase that mixed shell, LED volume,
rooms, cameras, and later building systems. That scope encouraged large scripts,
late inspection, and poor recovery.

Do not reuse its phase list. The current workflow loads only one canonical phase
prompt at a time: site/shell, stage/LED, rooms/access, then rigging/cameras.
Electrical, HVAC, fire-protection, and data are not modeled; only the required
estimated-load note is written. Use 1-4 coherent manifest-assembly mutations per
phase, never one-object calls. Require numeric `NUMERIC_PASS` before the focused
viewport/vision review, then write one named save after each accepted phase.
Rhino geometry uses only inline C# through `mcp_rhino_run_csharp`; Python is
read-only inspection/capture through `mcp_rhino_run_python`. DML/CMA remain advisory and
do not gate ordinary modeling calls.
