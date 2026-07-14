# Rhino Phase 2 — Stage and LED volume
### Agent-authored execution prompt

Before any Rhino call, read `06_mcp_operations_contract.md` and use its exact
Rhino 8 MCP 0.1.5 ABI and local-file viewport/vision handoff.

## Purpose

Design the shooting volume inside the accepted shell: curved main LED wall,
service/support zone, LED ceiling and operating envelope, optional floor zone,
unobstructed shooting area, and operational buffers.

## Inputs

- Passed site/shell geometry.
- LED and stage requirements in `01_standard_vp_studio_brief.md`.
- Retrieved DML evidence and CMA-augmented phase plan.

## Design decisions before modeling

Choose the horseshoe orientation, center, segmentation/rationalization, opening
toward support space, ceiling position, cable/service access, and relationship to
loading and camera movement. The brief controls diameter and active height but
does not prescribe object coordinates or segment count.

## Execution steps

1. Inspect the stage interior and cite the accepted clear dimensions.
2. Author a bounded MCP call for a manageable group of curved-wall segments;
   inspect curvature, radius, height, names, and metadata before adding more.
3. Continue in bounded groups until the 180-degree wall reads continuously.
4. In separate calls, model support/service clearance, ceiling active area and
   operating envelope, central shooting zone, and optional floor alternate.
5. Inspect from plan and stage-interior views and measure diameter/height/buffers.
6. Ingest objective success/failure evidence after every mutation group.

## Post-phase checklist

- Main wall is approximately 80 ft diameter, 180 degrees, and 24 ft active height.
- Service zone, support structure intent, and 10 ft operational buffer are legible.
- LED ceiling is 30 ft x 20 ft with its operating envelope represented.
- At least 50 ft x 40 ft of central shooting floor remains unobstructed.
- Geometry was authored by the agent in bounded calls, not loaded from a builder.

## Review gate

Present plan and interior perspective evidence with measured LED and shooting-zone
bounds. Do not proceed if the volume is merely a flat wall or blocks circulation.
