# Rhino Phase 2 — Stage and LED volume
### Agent-authored execution prompt

Read `06_mcp_operations_contract.md` once before the session's first Rhino
mutation. If it was already read in this session, do not load it again.

## Purpose

Design the shooting volume inside the accepted shell: curved main LED wall,
service/support zone, LED ceiling and operating envelope, optional floor zone,
unobstructed shooting area, and operational buffers.

## Inputs

- Passed site/shell geometry.
- LED and stage requirements in `01_standard_vp_studio_brief.md`.
- Retrieved DML evidence and CMA-augmented phase plan.

## Design decisions before modeling

Choose the horseshoe orientation, center, smooth construction method, opening
toward support space, ceiling position, cable/service access, and relationship to
loading and camera movement. Build a continuous curved surface/Brep with a
consistent radius and shallow realistic depth. Panel seams must not break the
continuous visible arc. The brief controls diameter and active height but does
not prescribe object coordinates.

## Execution steps

1. Inspect the stage interior and cite the accepted clear dimensions.
2. Author one bounded MCP call for the smooth 180-degree wall face and shallow
   backing/support assembly; inspect curvature, radius, thickness, height, names,
   edge continuity, and metadata.
3. Add panel intent only as lightweight seams, material/UV divisions, or shallow
   surface subdivisions. Never create a coarse ring of thick box panels.
4. In separate calls, model support/service clearance, ceiling active area and
   operating envelope, central shooting zone, and optional floor alternate.
5. Inspect from plan and stage-interior views and measure diameter/height/buffers.
6. Ingest objective success/failure evidence after every mutation group.

## Post-phase checklist

- Main wall is approximately 80 ft diameter, 180 degrees, and 24 ft active height.
- The visible wall is smooth and continuously curved, with realistic shallow
  depth and no faceted box silhouette, radial thickness spikes, or gaps.
- Service zone, support structure intent, and 10 ft operational buffer are legible.
- LED ceiling is 30 ft x 20 ft with its operating envelope represented.
- At least 50 ft x 40 ft of central shooting floor remains unobstructed.
- Geometry was authored by the agent in bounded calls, not loaded from a builder.

## Review gate

Present plan and interior perspective evidence with measured LED and shooting-zone
bounds. Do not proceed if the volume is flat, visibly faceted, excessively thick,
assembled from square placeholders, discontinuous, or blocking circulation.
