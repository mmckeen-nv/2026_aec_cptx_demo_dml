---
name: vp-studio-rhino-build
description: Build VP Studio 01 in Rhino from the locked manifest using bounded MCP-only phase assemblies, numeric validation, local vision, and checkpoints.
version: 2.0
---

# VP Studio Rhino build rails

Read `../../prompts/01a_locked_scene_manifest.md` before geometry and after any
context rotation. It is the sole authority for units, datum, names, dimensions,
coordinates, and envelopes. Use inches, absolute tolerance 0.01, angle tolerance
0.1 degrees, and world datum `(0,0,0)`.

## Non-negotiable execution contract

- The launcher owns the ready Rhino slot. Never spawn, close, replace, or repair
  Rhino or its MCP bridge.
- Execute every Rhino geometry mutation with `mcp_rhino_run_csharp(script=...)`
  using the exact scaffold embedded in the current phase prompt. Python is
  read-only inspection/capture only.
- Never execute Python/C# through terminal, execute_code, `run`, Rhino command
  macros, editors, desktop file opens, `_RunPythonScript`, or `_RunScript`.
- Compose scripts inline. After a phase's first mutation, do not patch/write a
  local script and do not read it back in fragments.
- Never call `mcp_rhino_run_command`.

## Four phase-local Rhino C# builds

1. Site/shell: coherent shell assemblies, then any evidence-based correction.
2. Stage/LED: smooth LED-wall assembly and related scheduled elements.
3. Rooms/access: east room bar and west support/circulation assemblies.
4. Rigging/cameras/layout: rigging, cameras, and repeated scheduled proxies.

One phase call may create its named components and repeated scheduled instances.
Never create one wall segment, chair, light, truss member, or camera part per
model turn. Never create a whole-studio replay script and never impose a hard
turn budget.

Each mutation returns compact evidence: created names/IDs, count, and world
bounds. On failure, correct the API or payload once; do not rewrite the phase or
switch execution paths.

## Mandatory phase gate

1. Run one read-only Rhino MCP validator. It prints document units/tolerances,
   every phase object's name and bounds, exact manifest comparisons, and
   `NUMERIC_PASS`. Any mismatch prints `NUMERIC_FAIL` and is corrected first.
2. Only after `NUMERIC_PASS`, capture one fresh local viewport PNG through Rhino
   MCP and send that exact path to local Nemotron vision.
3. Apply focused correction calls. Re-run the numeric validator.
4. Save one noninteractive phase checkpoint with `mcp_rhino_save_doc`.
5. Update compact session state and let Daystrom retain one validated lesson.

After context rotation, re-read session state, this skill, the manifest, and the
current phase prompt; inspect Rhino before mutating and never repeat completed
geometry. DML advises and accelerates the agent but never replaces these sources
of truth or controls ordinary modeling calls.
