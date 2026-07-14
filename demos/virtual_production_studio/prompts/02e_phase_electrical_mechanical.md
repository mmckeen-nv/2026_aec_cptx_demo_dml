# Rhino Phase 5 — Electrical and mechanical planning zones
### Agent-authored execution prompt

Before any Rhino call, read `06_mcp_operations_contract.md` and use its exact
Rhino 8 MCP 0.1.5 ABI and local-file viewport/vision handoff.
Keep this phase context-bounded: one final object listing, one focused local-PNG
vision verdict, then ingest the <=1,200-character phase-state record before advancing.

## Purpose

Represent editable planning envelopes for production power, technical power/UPS,
LED distribution, company switches, service/expansion, mechanical equipment, and
quiet stage-air paths. This is not engineered construction documentation.

## Inputs

- Accepted architectural, LED, access, rigging, and camera geometry.
- Electrical-load arithmetic and heat-removal assumptions in the brief.

## Design decisions before modeling

Choose service/distribution locations with safe conceptual access, short rational
paths to loads, separation of noisy motor/HVAC systems from sensitive production
systems, and mechanical zones outside the acoustic stage envelope.

## Execution steps

1. Query DML and augment the systems-zoning strategy through CMA.
2. Author separate bounded MCP calls for main service/expansion and transformations;
   LED/lighting distribution; technical UPS/control; then mechanical equipment and
   stage-air paths.
3. After each call inspect access, adjacency, names, and metadata. Keep all loads
   tagged `PLANNING_ASSUMPTION` and `NOT_FOR_CONSTRUCTION`.
4. Verify metadata exposes connected/reference load, voltage basis, source basis,
   and heat-removal relationship where applicable.
5. Ingest objective evidence and reinforce only validated zoning decisions.

## Post-phase checklist

- 750–1,000 kVA 480Y/277 V conceptual service envelope and expansion are visible.
- LED maximum/average references, production lighting, technical systems, rigging,
  and support allowances remain editable and correctly qualified.
- UPS is not implied to carry the complete LED volume.
- LED/server/control heat-removal zones and quiet stage-air paths are distinct.

## Review gate

Present services-zone views and metadata evidence; never claim feeder/HVAC sizing.
