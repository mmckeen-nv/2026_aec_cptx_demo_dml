# Rhino Phase 4 — Rigging, cameras, and physical equipment
### Agent-authored execution prompt

Read `06_mcp_operations_contract.md` once before the session's first Rhino
mutation. If it was already read in this session, do not load it again.
Keep this phase context-bounded: one final object listing, one focused local-PNG
vision verdict, then ingest the <=1,200-character phase-state record before advancing.

## Purpose

Create conceptual rigging/catwalk/hoist zones and the named camera, lens-frustum,
movement, and tracking envelopes needed to evaluate the virtual-production stage.
Complete the visually legible physical layout with chairs, workstations, carts,
road cases, calibration targets, and practical-light proxies.

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
6. In bounded groups, add six control-room operator chairs/workstations, 12
   movable production chairs, carts/road cases, calibration targets, and
   practical-light proxies. Keep them outside camera, scenery, loading, LED
   service, and clear-circulation zones.
7. Perform the final object, duplicate-name, geometry, plan, stage-interior,
   exterior, and equipment-layout audits. Write the estimated-load Markdown note,
   save Rhino exactly once, and ingest the validated artifacts into DML.

## Post-phase checklist

- `CAM_A_HERO_TRACKED` through `CAM_F_CONTROL_ROOM` are present and distinct.
- Dolly, crane, handheld, hero, witness, and control-room intents are legible.
- Grid/catwalk/hoist zones remain conceptual planning assumptions.
- Camera/rigging envelopes do not silently block required circulation.
- Furniture and equipment proxies are named, visibly placed, and suitable for
  replacement by cached Blender assets.
- No electrical, HVAC, data-distribution, or fire-protection geometry exists.

## Review gate

Present plan, stage-interior, exterior-axonometric, and equipment-layout evidence
showing camera coverage, overhead zones, furniture, and clear physical routes.
