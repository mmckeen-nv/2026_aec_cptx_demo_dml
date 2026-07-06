# International Airport 01 — Geometry Reference

Summit International Airport. Document units: millimeters. Reference coords below in meters (multiply by 1000).

**Last updated:** Phase 4b (June 15 2026). ~2,156 objects (after detail pass).

## Phase 4 changes (material tagging + OBJ export)

- **Removed:** 132 detached glass wall panels + vertical mullions (were floating alongside terminals, not attached)
- **Added:** 3 hub-to-terminal roof transition lofts (Solar_BIPV layer) + 6 side wall panels (Glass_Walls layer)
- **Material unification:** Terminal volumes (terminal_W, terminal_NE, terminal_SE) set to M_Solar_BIPV (same as hub roof)
- **OBJ export:** 217MB, 1.9M vertices, 922 mesh groups (curves excluded), 9 materials
- **Blender result:** 9 objects (one per material) after separate-by-material

## Site layout (centered at origin)

- **Terrain:** 3km × 3km, flat high plains, gentle 2-5m undulation, slight westward slope
- **Tarmac:** 2400m × 1400m (X:-800 to 1600, Y:-700 to 700)
- **Lot boundary:** 1600m × 1400m (X:-800 to 900, Y:-700 to 700)

## Y-shaped terminal plan

Hub centered at origin, three branches radiate outward:

| Element | Position | Dimensions |
|---------|----------|------------|
| Central hub roof | Origin | Flowing mountain-ridge form (NOT revolution surface), ~210m span, peak 50m |
| Hub pad | X:-110→110, Y:-110→110 | 220m × 220m square, Z: +0.5 to -5m |
| W branch | Along -X axis, 100→600m from origin | Taper 84m→40m wide, undulating roof 36m→12m |
| NE branch | 60° from +X, 100→600m from origin | Same proportions as W |
| SE branch | -60° from +X, 100→600m from origin | Same proportions as W |

Branch pads are trapezoid extrusions (not axis-aligned boxes) at Z: +0.5 to -5m.

## Hub roof design (Phase 3b revision)

The hub roof is a **lofted surface from 7 N-S profile curves** at X = -100, -65, -30, 0, +30, +65, +100m. Each profile has a unique mountain-ridge silhouette with asymmetric peaks. The central profile (X=0) has the main summit at Y=+10m, Z=50m, with secondary ridges.

**Key design:** NOT a dome or revolution surface. Evokes Rocky Mountain Front Range silhouette — asymmetric peaks, valleys between ridges, low at edges.

## Terminal branch design (Phase 3b revision)

Each branch has 8 cross-sections lofted together. The roofline is **undulating** with peaks and valleys:
- Hub junction: 36m roof height (peak)
- ~220m from center: 28m (valley)
- ~300m: 30m (secondary peak)
- ~380m: 22m (valley)
- ~450m: 24m (third peak)
- ~530m: 16m (descending)
- Tip (600m): 12m

Each cross-section is a closed NurbsCurve with 8 points: floor at -9m, walls to roof, peaked arch at center. Width tapers 84m→40m.

## Solar panel grid (Phase 3b — deep detail)

784 diamond-shaped BIPV panels on hub roof, created via UV parametric sampling (28×28 grid). Each panel is a NurbsSurface.CreateFromCorners of 4 surface-sampled points. 524 mullion edge segments (line curves every 3rd panel). Material: M_Solar_BIPV.

## Structural ribs

- **Hub:** 7 radial ribs (M_Concrete_DarkRib), swept breps from center to rim
- **Terminal branches:** 36 ribs (12 per branch), created via `Surface.CreateExtrusion` of arch NurbsCurves along branch direction. Each rib is a sin-arch profile spanning full width at its position. Material: M_Concrete_DarkRib.

## Glazing

- **Glass walls:** 66 panels (22 per branch), NurbsSurface.CreateFromCorners on both sides of each branch between rib positions. Floor to 85% of roof height. Material: M_Glass_Clear.
- **Vertical mullions:** 66 (22 per branch), thin panels at each rib position on both sides. Material: M_Aluminum_DarkBronze.

## Gates

54 jetway bridges (18 per branch), alternating sides. 15m long × 5m wide at Z=3m, extending outward from terminal walls. Material: M_Steel_Brushed.

## Interior glow planes

6 terminal glow planes (2 per branch, left and right, 3m inset from glass wall). 1 hub glow plane (square 180m×180m at Z=2m). Material: M_Interior_Glow.

## Entrance roads (Phase 3b — new)

| Road | Path | Elevation | Width |
|------|------|-----------|-------|
| Departures road | X:900→115, sweeping curve (slight northward) | Z:6m→2m (descending) | 18m |
| Arrivals road | X:900→115, sweeping curve (slight southward) | Z:2m→-2m (descending below grade) | 18m |

Both roads are lofted rectangular cross-sections along NurbsCurve paths (7 sections each). Material: M_Tarmac.

## Tunnel portals (Phase 3b — new)

| Tunnel | Position | Dimensions | Purpose |
|--------|----------|------------|---------|
| arrivals_tunnel | X:85→115, Y:-12→12 | Z:-4→-1m | Arrivals road descends to L-1 |
| parking_tunnel_N | X:280→310, Y:40→65 | Z:-6→-1m | North parking ramp to L-2 |
| parking_tunnel_S | X:280→310, Y:-65→-40 | Z:-6→-1m | South parking ramp to L-2 |

All are Box breps on Hub_Structure layer. Material: M_Concrete_DarkRib.

## Drop-off canopy (Phase 3b — revised)

Larger flowing canopy east of hub: 4 profile curves lofted at X=105, 120, 140, 160m. Width tapers 110m→50m, height descends 14m→8m with gentle arch. Material: M_Solar_BIPV.

## Aprons (aircraft parking)

| Apron | X range | Y range | Z top |
|-------|---------|---------|-------|
| apron_west | -700→-300 | -200→200 | 0.1m |
| apron_ne | 50→550 | 150→450 | 0.1m |
| apron_se | 50→550 | -450→-150 | 0.1m |

## Parking structure

- Lofted organic form 300m × 150m, centered at X=400, Y=0
- 5 cross-sections at X=250,325,400,475,550 with width taper (150→120m at ends)
- Arched roof: 15m center, 12m ends
- 4 floor slabs (L-2 through L1) as box breps within footprint
- 2 glass skywalks: X:110→250, Y:±25 (8m wide), Z:8→13m
- Pad: X:300→550, Y:-75→75, Z: +0.5 to -5m

## Floor levels

| Level | Name | Height | Floor-to-floor |
|-------|------|--------|----------------|
| L-2 | Underground parking/transit | -9m | 4.5m |
| L-1 | Arrivals/baggage | -4.5m | 4.5m |
| L0 | Departures/check-in | 0m (ground) | 8m |
| L1 | Mezzanine/lounges | 8m | 5m |
| Roof | Hub peak | 50m | — |

## Material tags

```
M_Glass_Clear           — structural glass walls, clear with subtle dark tint
M_Solar_BIPV            — transparent solar roof panels, blue-grey tint
M_Concrete_DarkRib      — structural ribs, dark charcoal smooth concrete
M_Concrete_LightFloor   — floor slabs, light grey polished
M_Aluminum_DarkBronze   — mullion framing, dark bronze anodised
M_Wood_WarmWalnut       — interior accent wood
M_Steel_Brushed         — stainless steel fixtures / gate jetways
M_Terrain_Prairie       — native grassland ground plane
M_Tarmac                — runway/taxiway asphalt / approach roads
M_Concrete_Apron        — aircraft apron concrete
M_Interior_Glow         — warm amber emission planes (Blender only)
M_Aircraft_White        — white aircraft fuselage/wings
M_Marking_White         — runway centerline and threshold markings
M_Mountain_Rock         — brownish exposed rock (Front Range)
M_Mountain_Snow         — snow-capped peaks (back range)
M_Mountain_Forest       — dark green forested foothills
```

## Layer structure (29 layers)

Site (Terrain, Tarmac, Apron, Taxiways, Approach_Roads, Lot_Lines, Mountains, Environment)
Building (Hub_Structure, Hub_Roof, Hub_Floor_Slabs, Terminal_W, Terminal_NE, Terminal_SE)
Glazing (Glass_Walls, Solar_BIPV, Mullions)
Parking (Parking_Structure, Skywalks)
Details (Canopy, Interior_Glow, Gates, Aircraft)
Pads (Building_Pad, Parking_Pad)

## Phase 4b additions (detail pass — June 15 2026)

### Aircraft at gates

54 aircraft mesh instances on `Details::Aircraft` layer. Template: fuselage cylinder (r=2m, L=38m, 8-segment) + delta wings (34m span, 10m chord at X=15m) + vertical tail (triangle at X=35m, 10m tall) + horizontal tail (12m span at X=35m). 57 verts / 52 faces per aircraft. Placed at each gate, oriented nose-out along the branch direction. Material: `M_Aircraft_White`.

**Placement logic:** For each gate, determine branch angle, compute perpendicular direction, offset aircraft 15m outward from gate center. Heading = branch angle (template nose along +X, rotated to match).

### Taxiways and runways

On `Site::Taxiways` layer. Created as centerline polyline → `Curve.Offset()` both sides → `Brep.CreateFromLoft()` between offsets.

| Element | Position | Width | Length | Material |
|---------|----------|-------|--------|----------|
| taxiway_alpha | E-W spine X:-1000→700, Y=0 | 25m | 1700m | M_Tarmac |
| runway_west | N-S at X=-900, Y:-700→700 | 45m | 1400m | M_Tarmac |
| runway_east | N-S at X=+600, Y:-700→700 | 45m | 1400m | M_Tarmac |
| taxiway_W1/W2 | Hub to W terminal, offset ±50m | 20m | ~400m | M_Tarmac |
| taxiway_NE1/NE2 | Hub to NE terminal | 20m | ~500m | M_Tarmac |
| taxiway_SE1/SE2 | Hub to SE terminal | 20m | ~500m | M_Tarmac |
| taxiway_conn_W1/W2 | W runway to spine | 20m | ~500m | M_Tarmac |
| taxiway_conn_E1/E2 | E runway to spine | 20m | ~200m | M_Tarmac |

### Runway markings

84 markings per runway (168 total) on `Site::Taxiways` layer at Z=0.2m:
- Centerline dashes: 30m long × 1.5m wide, every 50m
- Threshold stripes: 8 parallel bars (2m wide, 30m long, 4m spacing) at each end
- Number rectangles: 10m × 16m at each threshold
Material: `M_Marking_White`.

### Mountain ranges

On `Site::Mountains` layer. Each range is 3 lofted N-S profile curves at different X distances (front/mid/back) with height scale factors (1.0, 0.7, 0.4). Random jaggedness ±20-40m, edge tapering.

| Range | Y center | Y extent | X base | Peaks | Max height | Material |
|-------|----------|----------|--------|-------|------------|----------|
| front_range_main | 0 | 2000m | -3000m | 8 | 600m | M_Mountain_Rock |
| back_range | 0 | 2500m | -4500m | 6 | 450m | M_Mountain_Snow |
| foothills_nw | +500m | 1000m | -2000m | 5 | 180m | M_Mountain_Forest |
| foothills_sw | -500m | 1000m | -2000m | 5 | 160m | M_Mountain_Forest |

### Extended prairie

On `Site::Environment` layer. 9km × 8km flat surface at Z=-0.5m (X:-6000→3000, Y:-4000→4000). Extends well beyond airport footprint to the mountain bases. Material: `M_Terrain_Prairie`.

## Object count by layer (Phase 4b)

| Layer | Count |
|-------|-------|
| Building::Hub_Floor_Slabs | 4 |
| Building::Hub_Roof | 1 |
| Building::Hub_Structure | 39 (7 hub ribs + 36 terminal ribs → to be split if needed) |
| Building::Terminal_W/NE/SE | 3 |
| Details::Canopy | 1 |
| Details::Gates | 54 |
| Details::Interior_Glow | 7 |
| Glazing::Glass_Walls | 66 |
| Glazing::Mullions | 590 (66 vertical + 524 solar edge) |
| Glazing::Solar_BIPV | 784 |
| Pads::Building_Pad + Parking_Pad | 6 |
| Parking::Parking_Structure | 5 |
| Parking::Skywalks | 2 |
| Site (all sublayers) | 8 |
| Details::Aircraft | 54 |
| Site::Taxiways (incl. runways + markings) | 181 |
| Site::Mountains | 4 |
| Site::Environment | 1 |
| **Total** | **~2,156** |
