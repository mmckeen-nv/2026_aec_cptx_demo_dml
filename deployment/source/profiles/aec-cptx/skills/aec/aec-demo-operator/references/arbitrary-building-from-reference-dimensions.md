# Building Any Structure from Known Reference Dimensions

Proven pattern for building physically accurate models of real buildings (not just cliff_house_02) using the same Rhino→Blender pipeline.

## When to use

When asked to model a real-world building (Empire State Building, Chrysler Building, etc.) or any structure with known published dimensions.

## Approach: setback massing from architectural knowledge

1. **Gather dimensions** — use well-known architectural records (floor count, lot size, setback heights, antenna/spire heights). DML won't have these — use domain knowledge.
2. **Define coordinate system** — origin at building center at ground level, X = long axis, Y = short axis, Z = up.
3. **Build bottom-up as stacked boxes** — one box per setback tier. Each tier has: footprint (hw × hd), Z range (floor × floor_height). This gives the correct silhouette.
4. **Add detailing** — window strips, spandrels, mullions as thin boxes on faces. Use modular bay spacing (e.g., 3.9m module for ESB).
5. **Save checkpoint** — always before moving to Blender.
6. **Recreate in Blender** — same boxes, meters directly (no mm conversion). Assign materials inline.

## Empire State Building reference (built June 12, 2026)

### Key dimensions (meters)
- Lot: 129m (E-W) × 57m (N-S)
- Floor height: 3.66m (12 ft typical 1930s office)
- Total height to roof: 381m (1,250 ft)
- Antenna tip: 443m (1,454 ft)

### Setback tiers (7 total)

| Tier | Floors | Footprint | Z range (m) |
|------|--------|-----------|-------------|
| Base | 1-5 | 129 × 57 | 0 → 18.3 |
| Setback 1 | 6-25 | 115 × 43 | 18.3 → 91.5 |
| Setback 2 | 26-36 | 101 × 35 | 91.5 → 131.8 |
| Main tower | 37-71 | 57 × 25 | 131.8 → 259.9 |
| Upper tower | 72-86 | 41 × 19 | 259.9 → 314.8 |
| Crown (3 sub-steps) | 86-102 | 33→25→18 | 314.8 → 381 |
| Antenna mast (3 sub-steps) | — | 10→6→2 | 381 → 443 |

### Art Deco detailing parameters
- Window strip width: 2.4m, pier width: 1.5m → 3.9m bay module
- Window inset from face: 0.15m
- Window thickness: 0.05m
- Chrome mullion: 0.10m wide × 0.08m deep
- Spandrel panel height: 0.4m at each floor level

### Materials (Blender Cycles)
- M_Limestone: (0.82, 0.78, 0.72), roughness 0.7 — walls
- M_Chrome: (0.85, 0.85, 0.90), roughness 0.1, metallic — crown accents
- M_Glass_ESB: (0.3, 0.35, 0.4), transmission 0.6 — windows
- M_Antenna: (0.5, 0.5, 0.55), roughness 0.15, metallic — mast
- M_Entrance: (0.7, 0.55, 0.35), roughness 0.4, metallic 0.5 — Art Deco entrance

### Camera for skyscrapers
- Use wide angle (24mm) and low dramatic position to emphasize height
- ESB hero cam: (-120, -180, 80) aimed at (0, 0, 250) — upward street-level angle
- Contrast with cliff_house_02 which used 28mm at human height

## Rhino units pitfall

Rhino document units are millimeters. ALL meter values must be multiplied by 1000. This applies to every building, not just cliff_house_02. The `add_box` helper should always sort coordinates (see `references/rhino-python-geometry-pitfalls.md`).

## Artifacts from ESB session
- Rhino: `C:/Users/test/Documents/empire_state_building_checkpoint_01.3dm` (161 objects)
- Blender: `C:/Users/test/Documents/empire_state_building_scene.blend`
- Render: `C:/Users/test/Documents/empire_state_building_render.png`
