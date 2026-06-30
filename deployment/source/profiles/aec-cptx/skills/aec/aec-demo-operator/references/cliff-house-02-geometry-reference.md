# cliff_house_02 Reference Geometry Coordinates

From DEMO_RULES.md "What Has Been Built" section.
All values in **meters**. Document units are mm — **multiply by 1000**.

## building_site_v3

| Object | X min | X max | Y min | Y max | Z min | Z max |
|--------|-------|-------|-------|-------|-------|-------|
| terrain | -15 | 25 | -22 | 20 | -8 | 0 |
| combined_pad | 1.5 | 17 | -16.9 | 14 | -0.5 | 0.25 |
| curtain_wall | 1 | 17.5 | -17.4 | 14.5 | -2 | 0.25 |
| driveway | 17.5 | 25.03 | 3.96 | 13 | -0.2 | 0.25 |

### Pad bottom rule
Sample terrain Z at pad corners and midpoints. Pad bottom must be
at least 50mm below the minimum sampled Z value.

## massing_v3 (11 objects)

| Object | Layer | X min | X max | Y min | Y max | Z min | Z max |
|--------|-------|-------|-------|-------|-------|-------|-------|
| L1_east | L1_solids | 5 | 17 | 3 | 14 | 0.25 | 4 |
| L1_west | L1_solids | 5 | 13.5 | -15 | 3 | 0.3 | 4 |
| L2_east | L2_solids | 5 | 17 | 3 | 14 | 4.25 | 7.75 |
| L2_west | L2_solids | 3.5 | 13.5 | -15 | 3 | 4.25 | 7.75 |
| L2_balcony_south | L2_balcony_solids | 1.5 | 13.5 | -17.05 | 3 | 4 | 5.25 |
| L2_balcony_north | L2_balcony_solids | 5 | 17 | 14 | 16.25 | 4 | 5.15 |
| L2_balcony_step | L2_balcony_solids | 1.5 | 5 | 3 | 14 | 4 | 5.25 |
| L2_roof_garage | L2_roof_solids | 2.5 | 18.97 | 1.16 | 16.55 | 7.75 | 8.35 |
| L3_main | L3_solids | 1.5 | 13.5 | -10 | 3 | 7.75 | 11.5 |
| L3_balcony_south | L3_balcony_solids | 1.5 | 13.5 | -17 | -10 | 7.75 | 8.9 |
| L3_roof_slab | L3_roof_slab | -1 | 15 | -13.5 | 4.5 | 11.5 | 12.3 |

## Building orientation

- West/South = ocean side (cliff drop-off, view side)
- East = street side (garage, entry, driveway)
- Y axis: negative = south (ocean), positive = north (street approach)
- X axis: negative = west (cliff), positive = east (street)
- Terrain slopes steeply down to the west (cliff face)

## Layer structure (DEMO_RULES massing_v3 — prior sessions)

```
building_site_v3/
  terrain
  combined_pad
  curtain_wall
  driveway

massing_v3/
  L1_solids
  L2_solids
  L2_balcony_solids
  L2_roof_solids
  L3_solids
  L3_balcony_solids
  L3_roof_slab
```

## June 12, 2026 clean-build massing (default design brief)

This session built from a fresh base_model.3dm with default [FILL IN] values.
Simpler 2-story + garage structure. All values in meters (document units mm).

### Site (Terrain, Building_Pad, Patio, Garage_Pad, Driveway, Retaining_Wall)

| Object | X min | X max | Y min | Y max | Z min | Z max |
|--------|-------|-------|-------|-------|-------|-------|
| terrain_surface | -15 | 25 | -20 | 16 | -5.0 | 0.4 |
| building_pad | 1.5 | 13.5 | -15.5 | 4.5 | -1.0 | 0.3 |
| patio_pad | -6 | 0 | -16 | 5 | -2.4 | -0.7 |
| garage_pad | 7 | 17 | 4.5 | 15 | -0.2 | 0.3 |
| driveway | 17 | 25 | 6.5 | 13.5 | -0.2 | 0.1 |

### Massing (L1_Walls, L1_Slab, L2_Walls, L2_Slab, Roof_Slab, Garage_Volume)

| Object | X min | X max | Y min | Y max | Z min | Z max |
|--------|-------|-------|-------|-------|-------|-------|
| L1_walls | 4.5 | 13.5 | -15.5 | 4.5 | 0.3 | 3.5 |
| L1_slab | 4.5 | 13.5 | -15.5 | 4.5 | 3.5 | 3.8 |
| L2_walls | 1.5 | 13.5 | -15.5 | 4.5 | 3.8 | 7.0 |
| L2_slab | 1.5 | 13.5 | -15.5 | 4.5 | 7.0 | 7.3 |
| roof_slab | 0.5 | 14.5 | -16.5 | 5.5 | 7.3 | 7.5 |
| garage_volume | 7 | 17 | 4.5 | 15 | 0.3 | 3.1 |
| garage_roof | 6 | 18 | 3.5 | 16 | 3.1 | 3.3 |

### Design key points
- L1 recessed to east (X=4.5) creating 3m west veranda under L2 cantilever
- L2 cantilevered to pad west edge (X=1.5)
- Floor height: 3.2m, slab thickness: 300mm
- Flat roof with 1m overhang, building top at 7.5m
- Garage separate volume NE, 2.8m clear height

## June 15, 2026 fresh-build site prep (filled design brief)

Built from base_model.3dm with fully filled project_prompt.md.
All values in meters (document units mm). Layer parent: `building_site`.

### Source curve coordinates (from base_model.3dm, already in mm)

| Curve | X min | X max | Y min | Y max | Z min | Z max |
|-------|-------|-------|-------|-------|-------|-------|
| pad_plan ("building_plan") | 1.5 | 13.5 | -15.5 | 4.5 | 0 | 0 |
| patio_plan | -6 | 0 | -16 | 5 | -1 | -1 |
| garage_plan | 7 | 17 | 4.5 | 15 | 0 | 0 |
| driveway_plan | 17 | 25 | 6.5 | 13.5 | 0 | 0 |
| stairs_plan | -3 | 1 | -3 | -1 | 0 | 0 |
| uCurves ×3 | -15→25 | (N-S runs) | -20→16 | varies | -5→0 | varies |
| vCurves ×2 | -15→25 | (E-W rails) | -20→16 | varies | -5→0 | varies |

### Site objects created

| Object | Layer | X min | X max | Y min | Y max | Z min | Z max | Notes |
|--------|-------|-------|-------|-------|-------|-------|-------|-------|
| terrain_surface | terrain | -15 | 25 | -20 | 16 | -5.0 | 0.4 | Lofted from 3 u-curves sorted by X |
| building_pad | building_pad | 1.5 | 13.5 | -15.5 | 4.5 | -1.0 | 0.3 | Terrain Z min under pad: -0.8m |
| patio_pad | patio_pad | -6 | 1.5 | -16 | 5 | -2.4 | -0.7 | Stepped down, overlaps pad west edge |
| garage_pad | garage_pad | 7 | 17 | 4.5 | 15 | -0.1 | 0.3 | Flush with building pad top |
| driveway | driveway | 17 | 25 | 6.5 | 13.5 | -0.2 | 0.1 | Thin slab, road to garage |
| retaining_wall | retaining_wall | 1.0 | 14.0 | -16 | 5 | -1.1 | 0.3 | 500mm thick hollow box, boolean diff |

### Terrain Z samples at key points
- Building pad corners: min -0.8m, max +0.4m
- Patio corners: min -2.2m, max -0.1m
- Retaining wall perimeter: min -0.9m, max +0.3m
- Pad/wall bottoms set 200mm below min sampled terrain Z

## June 15, 2026 massing (3-tier, filled design brief)

Layer parent: `massing`. All values in mm. 11 objects.

| Object | Layer | X min | X max | Y min | Y max | Z min | Z max |
|--------|-------|-------|-------|-------|-------|-------|-------|
| L1_east | L1_solids | 5000 | 17000 | 3000 | 14000 | 300 | 4050 |
| L1_west | L1_solids | 5000 | 13500 | -15000 | 3000 | 300 | 4050 |
| L2_east | L2_solids | 5000 | 17000 | 3000 | 14000 | 4300 | 8050 |
| L2_west | L2_solids | 3500 | 13500 | -15000 | 3000 | 4300 | 8050 |
| L2_balcony_south | L2_balcony_solids | 1500 | 13500 | -17500 | -15000 | 3800 | 4300 |
| L2_balcony_north | L2_balcony_solids | 5000 | 17000 | 14000 | 16500 | 3800 | 4300 |
| L2_balcony_step | L2_balcony_solids | 1500 | 5000 | -15000 | 14000 | 3800 | 4300 |
| L2_roof_garage | L2_roof_solids | 2500 | 19000 | 1000 | 16500 | 4050 | 4350 |
| L3_main | L3_solids | 1500 | 13500 | -10000 | 3000 | 8300 | 12050 |
| L3_balcony_south | L3_balcony_solids | 1500 | 13500 | -17000 | -10000 | 8050 | 8500 |
| L3_roof_slab | L3_roof_slab | -500 | 15000 | -13500 | 4500 | 12050 | 12350 |

### Key design decisions (June 15)
- 3-tier not 2-story: L3 penthouse over west wing only (Y:-10000 to 3000)
- L1 recessed east (X=5000) creating covered veranda under L2 cantilever (L2 extends to X=3500)
- Building top at 12.35m. Slab gaps 250mm between floors.
- Floor heights: L1 3.75m, L2 3.75m, L3 3.75m
- L2 balcony south extends 2.5m beyond building face for infinity pool views

## June 15, 2026 detailing summary

Total: 381 visible objects (16 source + 6 site + 11 massing + 288 detailing + 59 interior + 17 exterior features). Checkpoint: `cliff_house_02_checkpoint_20250615_phase3.3dm`
