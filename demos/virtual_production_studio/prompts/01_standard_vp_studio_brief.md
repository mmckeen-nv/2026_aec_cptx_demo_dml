# Standard-lot virtual-production studio: physical-layout brief

Status: **conceptual planning assumptions for a demonstration model**. This is
not engineering, permitting, procurement, or construction documentation.

## Design intent

Model a visually credible medium/large commercial virtual-production facility on
a conventional studio lot. The demo proves agent-authored building and stage
geometry, operational layout, Rhino-to-Blender handoff, reusable production
assets, and final stylization. Keep the design legible and achievable.

Use US customary dimensions and model in Rhino inches. Use absolute tolerance
0.01 in and angle tolerance 0.1 degrees.

## Site and building baseline

- Concept lot: 300 ft x 400 ft, approximately 2.75 acres.
- Main building: approximately 180 ft x 150 ft, 27,000 gross sq ft.
- Clear soundstage: at least 120 ft x 100 ft and 40 ft clear to the grid.
- Ancillary bar: control room, edit/color, media-server room, camera prep,
  wardrobe/makeup, green rooms, production office, shop/storage, and toilets.
- Loading: two 14 ft x 16 ft overhead doors, a 60 ft truck apron, and a scenery
  route to the stage that does not cross office or control space.
- Separate public/office, crew, loading, and service approaches.
- Keep exits and clear circulation visible. Final code compliance belongs to the
  design team and authority having jurisdiction.

## Stage and LED volume

- Main LED wall: 180-degree horseshoe, 80 ft nominal diameter, 24 ft active height.
- Wall planning module: 500 mm x 500 mm.
- Provide a 6 ft minimum service zone behind the wall and visible support depth.
- LED ceiling: 30 ft x 20 ft active area at nominal 24 ft trim, with a 16-32 ft
  operating envelope.
- Optional LED floor proxy: 40 ft x 30 ft.
- Preserve at least 50 ft x 40 ft of unobstructed central shooting floor.
- Keep a 10 ft preferred talent/key-light stand-off from the LED wall.
- Include tracking-marker datums, calibration-target storage, removable scenery
  zones, protected cable crossings, and equipment parking outside camera paths.

ROE Visual lists Black Pearl BP2V2 as a 500 mm square panel drawing 190 W
maximum and 95 W average, at 9.35 kg. Use this only as the transparent reference
basis for the estimate: https://www.roevisual.com/us-en/products/black-pearl-2v2

## Cameras, rigging, and tracking

Model simple named camera bodies plus lens frustums and movement envelopes:

- `CAM_A_HERO_TRACKED`: eye height 5.5 ft, 24-35 mm starting lens range.
- `CAM_B_DOLLY_TRACKED`: 40 ft clear dolly path, 35-50 mm lens range.
- `CAM_C_CRANE_TRACKED`: 25 ft radius swept envelope.
- `CAM_D_HANDHELD_TRACKED`: flexible cable-free operating zone.
- `CAM_E_WITNESS`: fixed wide reference view.
- `CAM_F_CONTROL_ROOM`: operational monitoring view.

Provide a conceptual roof grid/catwalk, practical-light positions, and overhead
and perimeter tracking-sensor datums with clear sightlines. Structural loads,
attachments, fall protection, and rigging engineering are outside this demo.

## Physical production layout

- Place six operator workstations and six operator chairs in the control room.
- Place 12 movable production chairs in a safe perimeter waiting/review area.
- Include proxies for tripods, a dolly, a jib/crane base, practical production
  lights, calibration targets, equipment carts, and road cases.
- Keep furniture and equipment outside camera movement, scenery, loading,
  LED-service, and clear-circulation routes.
- Rhino owns simple named proxy volumes. Blender replaces or supplements these
  with cached Creative Commons assets; do not detail furniture in Rhino.

## Estimated electrical load note — documentation only

Do not model electrical rooms, utility service, transformers, panels, feeders,
conduit, cable tray, company switches, UPS equipment, generators, HVAC equipment,
ductwork, data cabling, or fire-protection systems. After the physical Rhino gate
passes, write `work/vp_studio_01_estimated_load.md` and tag every value
`PLANNING_ASSUMPTION`.

Use this transparent arithmetic:

- Main wall: about 77 columns x 15 rows = 1,155 panels; approximately 219 kW
  maximum and 110 kW representative operating load.
- LED ceiling: about 223 panels; approximately 42 kW maximum and 21 kW
  representative operating load.
- Base LED reference: approximately 262 kW maximum and 131 kW representative.
- Production lighting allowance: 100 kW.
- Media servers, render nodes, processing, tracking, storage, and control: 100 kW.
- Rigging/hoists and stage machinery: 50 kW intermittent allowance.
- Shop, office, receptacle, and miscellaneous production allowance: 125 kW.
- Arithmetic subtotal: approximately **637 kW maximum connected planning
  allowance** and **506 kW representative operating planning allowance** when
  the LED system uses 131 kW and other allowances remain conservatively unchanged.
- HVAC and life-safety loads are excluded and must be added by the design team.

The note must say that these are rough demo estimates, not a recommended service
size. A qualified engineer must apply demand, continuous-load, harmonic,
power-factor, ambient/derating, redundancy, cooling, and adopted-code requirements.

## Required model metadata

Every physical object receives User Text for `project=vp-studio-01`, `system`,
`discipline`, `agentic_phase`, `phase=SCHEMATIC`, `assumption_status`,
`source_basis`, and `export_to_blender`. The load estimate stays in the Markdown
note; it must not generate modeled electrical objects.
