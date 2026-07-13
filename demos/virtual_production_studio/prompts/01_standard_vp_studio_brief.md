# Standard-lot virtual-production studio: conceptual design brief

Status: **conceptual planning assumptions for a demonstration model**. This is not engineering, permitting, procurement, or construction documentation.

## Design intent

Model a credible medium/large commercial virtual-production facility on a conventional studio lot. It must support in-camera VFX, commercial/episodic work, vehicle and scenery access, camera tracking, practical lighting, production control, equipment maintenance, and safe crew circulation.

Use US customary dimensions as the displayed design language and model in Rhino inches. Set absolute tolerance to 0.01 in and angle tolerance to 0.1 degrees.

## Site and building baseline

- Concept lot: 300 ft x 400 ft, approximately 2.75 acres.
- Main building: approximately 180 ft x 150 ft, 27,000 gross sq ft.
- Clear soundstage: 120 ft x 100 ft minimum, 40 ft clear to underside of structure/grid.
- Ancillary bar: control rooms, edit/color, machine/media-server room, electrical rooms, camera prep, wardrobe/makeup, green rooms, production offices, shop/storage, toilets, and quiet mechanical support.
- Loading: two 14 ft x 16 ft overhead doors, 60 ft truck maneuvering apron, scenery route to stage without passing through control or office space.
- Separate public/office entry, crew entry, loading access, and service-yard access.
- Provide conceptual egress paths and keep required exits visible; final quantity, separation, ratings, travel distance, accessibility, and occupant load belong to the code team/AHJ.

## Stage and LED volume

- Main LED wall: 180-degree horseshoe, 80 ft nominal diameter, 24 ft active height.
- Wall panel planning module: 500 mm x 500 mm.
- Provide a 6 ft minimum service zone behind the wall, plus support structure and cable-management zones.
- LED ceiling: motorized 30 ft x 20 ft active area, modeled at a nominal 24 ft trim with a 16-32 ft operating envelope.
- Optional practical LED floor zone: 40 ft x 30 ft, shown as an alternate, not assumed in base electrical load.
- Practical shooting floor inside volume: preserve at least 50 ft x 40 ft unobstructed central area.
- Talent/key-light stand-off: show a 10 ft preferred no-light-spill buffer from the LED wall; treat it as an operational guide, not a code clearance.
- Add tracking-marker datum locations, calibration target storage, removable wild-wall/scenery zones, cable trenches or protected cable crossings, and equipment parking outside camera paths.

ROE Visual lists its widely deployed Black Pearl BP2V2 as a 500 mm square panel drawing 190 W maximum and 95 W average. It also lists 9.35 kg panel weight. These values are a transparent reference basis, not a selected product commitment: https://www.roevisual.com/us-en/products/black-pearl-2v2

## Camera and tracking provisions

Model cameras as named bodies plus lens frustums and movement envelopes:

- `CAM_A_HERO_TRACKED`: eye height 5.5 ft, 24-35 mm starting lens range, central stage-wide composition.
- `CAM_B_DOLLY_TRACKED`: 40 ft clear dolly path, 35-50 mm starting lens range.
- `CAM_C_CRANE_TRACKED`: 25 ft radius swept envelope and overhead clearance volume.
- `CAM_D_HANDHELD_TRACKED`: flexible operating zone with protected cable-free circulation.
- `CAM_E_WITNESS`: fixed wide reference view.
- `CAM_F_CONTROL_ROOM`: operational witness/monitoring view, not a beauty camera.

Provide overhead and perimeter tracking-sensor locations with clear sightlines to the working volume. Keep tracking, genlock/timecode, media-server, LED-processing, camera, and production networks represented as separate logical systems even if final hardware consolidates them.

## Electrical planning model

All values below are tagged `PLANNING_ASSUMPTION`. The model must expose the arithmetic and retain editable demand factors.

### LED reference load

For the 80 ft diameter, 180-degree, 24 ft high wall, a 500 mm module yields approximately 77 columns x 15 rows = 1,155 panels before detailed edge/curvature rationalization.

- Main wall connected load: 1,155 x 190 W = approximately 219 kW maximum.
- Main wall representative operating load: 1,155 x 95 W = approximately 110 kW average.
- A 30 ft x 20 ft ceiling is approximately 223 panels: 42 kW maximum and 21 kW average.
- Base LED system reference: approximately 262 kW maximum and 131 kW representative average, before processors, networking, losses, spares, or future expansion.
- Sensible heat planning: electrical input ultimately becomes room heat. Use 3,412 Btu/h per kW, giving approximately 894,000 Btu/h at the LED maximum reference and 447,000 Btu/h at representative average.

Do not size feeders from average draw. Use manufacturer maximum/connected load, applicable continuous-load treatment, diversity rules, ambient/derating, power-factor/harmonic data, and the adopted electrical code.

### Other production allowances

- Production lighting connected allowance: 100 kW. Keep it adjustable. ARRI publishes 800 W, 1,600 W, and 2,400 W for SkyPanel X21/X22/X23 configurations: https://www.arri.com/en/lighting/led-panel-lights/skypanel-x/tech-data
- Media servers, render nodes, LED processors, KVM/network, tracking, storage, and control: 100 kW connected allowance, with dedicated UPS-backed control subset.
- Rigging/hoists and stage machinery: 50 kW intermittent allowance; coordinate regenerative drives and simultaneous-operation assumptions.
- Shop, office, support, receptacle, and miscellaneous production allowance: 125 kW before final load calculations.
- HVAC and life-safety loads remain separate and must be added by the MEP engineer.

Use a **750-1,000 kVA, 480Y/277 V, three-phase conceptual service placeholder** with a reserved expansion position. This is a planning envelope only—not a service-size conclusion. Show dedicated transformation/distribution for 208Y/120 V technical and convenience loads; segregate noisy motor/HVAC loads from sensitive production systems; provide labeled company-switch/distribution zones; and reserve generator connection and UPS space for safe shutdown of control, tracking, network, and media systems. Do not imply that the UPS carries the full LED volume unless specifically engineered.

Coordinate grounding/bonding, neutral harmonic loading, fault-current ratings, selective coordination, emergency power, cable ampacity/derating, disconnect access, and listed distribution equipment. Applicable design review includes the adopted NEC and, depending on use and occupancy, NEC Articles 520 and 530. NFPA materials identify Article 520 with theaters/audience and production areas and Article 530 with motion-picture/television studios: https://www.nfpa.org/api/files?path=%2Ffiles%2FAboutTheCodes%2F70%2F70_A2025_NEC_AAC_SD_SCRReport.pdf

## Mechanical, acoustic, structure, and safety placeholders

- Provide quiet, low-velocity stage air distribution; locate major mechanical equipment outside the soundstage envelope and isolate vibration. Final sound criteria and NC/RC targets require an acoustical consultant.
- Provide dedicated heat-removal zoning for LED wall/ceiling, media-server room, control rooms, and occupied stage. Do not bury the LED heat load in a generic area-based HVAC estimate.
- Show a conceptual roof/rigging grid, catwalks, fall-protection zones, hoist service access, and structural support behind LED surfaces. Loads and attachment details require structural and rigging engineering.
- Show sprinkler/fire-protection zones, fire department access, emergency lighting, exit signage, rated-room placeholders, and clear egress. Final systems require fire-protection engineering and AHJ review.
- Maintain accessible routes to occupied public and staff spaces; do not treat temporary production equipment as permission to block them.

## Required model metadata

Every infrastructure object must include User Text for `system`, `discipline`, `phase`, `assumption_status`, `source_basis`, and `load_or_capacity` where applicable. Use `assumption_status=PLANNING_ASSUMPTION` until professional/user approval changes it.

