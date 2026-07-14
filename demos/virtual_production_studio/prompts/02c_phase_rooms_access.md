# Rhino Phase 3 — Rooms, circulation, and loading access
### Agent-authored execution prompt

Read `06_mcp_operations_contract.md` once before the session's first Rhino
mutation. If it was already read in this session, do not load it again.
Keep this phase context-bounded: one final object listing, one focused local-PNG
vision verdict, then ingest the <=1,200-character phase-state record before advancing.

## Purpose

Plan the ancillary bar and operational routes around the accepted stage without
eroding the soundstage clear volume.

## Inputs

- Accepted shell/stage/LED geometry.
- Room, entry, loading, scenery-route, and access requirements in the brief.

## Design decisions before modeling

Develop a credible adjacency diagram: control and witness spaces near the volume;
media/server and control spaces near the volume; camera prep, wardrobe/makeup,
green rooms, offices, shop/storage, and toilets; separate public, crew, service,
and loading paths. Do not reserve or model electrical or mechanical rooms.

## Execution steps

1. Query DML and augment the adjacency/circulation proposal through CMA.
2. Inspect remaining shell area and stage clearances.
3. Author separate bounded MCP calls for room groups, interior partitions, then
   openings/loading-door proxies and scenery/circulation routes.
4. Inspect after each call; measure routes and verify no stage/LED encroachment.
5. Tag room and route assumptions; ingest the result and any unresolved issues.

## Post-phase checklist

- Required room types are represented with stable names and meaningful adjacency.
- Two 14 ft x 16 ft loading-door envelopes and 60 ft truck apron are visible.
- Scenery reaches the stage without crossing office/control space.
- Public, crew, loading, and service access remain separable.

## Review gate

Present a plan view with labeled room/route objects and measured loading evidence.
Advance only when the operational diagram is plausible.
