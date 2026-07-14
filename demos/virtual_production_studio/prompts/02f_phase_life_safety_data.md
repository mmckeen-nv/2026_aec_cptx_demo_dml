# Rhino Phase 6 — Life safety, fire access, and production data
### Agent-authored execution prompt

Before any Rhino call, read `06_mcp_operations_contract.md` and use its exact
Rhino 8 MCP 0.1.5 ABI and local-file viewport/vision handoff.
Keep this phase context-bounded: one final object listing, one focused local-PNG
vision verdict, then ingest the <=1,200-character phase-state record before advancing.

## Purpose

Complete the conceptual Rhino model with visible egress/fire-access assumptions
and distinct tracking, genlock/timecode, media, control, and production-network zones.

## Inputs

- All accepted prior Rhino phases.
- Safety, accessibility, fire access, and logical-network requirements in the brief.

## Design decisions before modeling

Choose conceptual exit/circulation and fire-access paths that respond to the actual
agent-designed plan. Keep network systems logically distinct and route them without
inventing final code compliance or engineered cable design.

## Execution steps

1. Query DML and augment the final safety/data plan through CMA.
2. Inspect current routes and conflicts before adding geometry.
3. Author one bounded MCP call for egress/accessibility/fire-access proxies, inspect
   continuity and clashes, then a separate call for data/control/network zones.
4. Run an agent-authored read-only audit through Rhino MCP: dynamic counts by phase
   and layer, unique names, metadata completeness, invalid/open geometry, required
   dimensions, camera names, and planning-assumption labels.
5. Capture plan, interior, exterior axonometric, and services-zone evidence.
6. If and only if the full gate passes, save once through `mcp_rhino_save_doc` to a
   timestamped `work/` path and ingest that artifact/evidence into DML.

## Post-phase checklist

- Egress, accessible-route intent, fire access, and exit visibility are represented.
- Tracking, genlock/timecode, media-server, LED-processing, camera, and production
  networks remain logically distinguishable.
- Full audit uses the actual object count; it does not target a historical count.
- One gated save occurred and no interactive save dialog was triggered.

## Review gate

Present the complete audit and four viewport captures. Unresolved professional/AHJ
items remain explicitly labeled; then proceed to the direct `.3dm` handoff.
