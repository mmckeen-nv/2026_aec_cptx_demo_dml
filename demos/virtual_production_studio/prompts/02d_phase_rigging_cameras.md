# Rhino Phase 4 — Rigging, cameras, and tracking
### Agent-authored execution prompt

Before any Rhino call, read `06_mcp_operations_contract.md` and use its exact
Rhino 8 MCP 0.1.5 ABI and local-file viewport/vision handoff.

## Purpose

Create conceptual rigging/catwalk/hoist zones and the named camera, lens-frustum,
movement, and tracking envelopes needed to evaluate the virtual-production stage.

## Inputs

- Accepted stage/LED and circulation geometry.
- Camera and structural/rigging planning requirements in the brief.

## Design decisions before modeling

Choose a grid/catwalk organization and camera placements that serve useful shots
without blocking exits, scenery movement, LED service, or one another. Camera
objects are operational proxies, not detailed third-party models.

## Execution steps

1. Query DML and augment the rigging/camera plan through CMA.
2. Author a bounded MCP call for rigging grid and catwalk zones; inspect height and
   clearance above the LED ceiling envelope.
3. Add hoist/service envelopes in a separate bounded call and inspect overlaps.
4. Add the six required named camera bodies in small groups, then separately add
   frustums and movement envelopes, including the 40 ft dolly path and 25 ft crane radius.
5. Add overhead/perimeter tracking-sensor datum proxies and inspect sightlines.
6. Record objective counts, names, bounds, and failures in DML.

## Post-phase checklist

- `CAM_A_HERO_TRACKED` through `CAM_F_CONTROL_ROOM` are present and distinct.
- Dolly, crane, handheld, hero, witness, and control-room intents are legible.
- Grid/catwalk/hoist zones remain conceptual planning assumptions.
- Camera/rigging envelopes do not silently block required circulation.

## Review gate

Present stage-interior and plan evidence showing camera coverage and overhead zones.
