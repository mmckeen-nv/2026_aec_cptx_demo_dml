# VP Studio 01 — Geometry Reference Coordinates

Phase 0 baseline geometry established 2026-06-29.

## Coordinate System
- Origin: Center of stage house footprint, at grade (Z=0)
- +Y = North (loading dock side)
- -Y = South (client entrance)
- +X = East (support wing side)
- -X = West
- Units: Meters
- Tolerances: Abs 0.001, Rel 0.001, Angle 1.0°

## Building Layout Coordinates

### Stage House Envelope
| Element | X Range | Y Range | Z Range | Layer |
|---------|---------|---------|---------|-------|
| Stage slab | -18.5 to +18.5 | -26 to +26 | 0 to 1.2 | Stage_House::Slab |
| North wall | -18.5 to +18.5 | +25.6 to +26 | 1.2 to 18 | Stage_House::Walls_North |
| South wall | -18.5 to +18.5 | -26 to -25.6 | 1.2 to 18 | Stage_House::Walls_South |
| East wall | +18.1 to +18.5 | -26 to +26 | 1.2 to 18 | Stage_House::Walls_East |
| West wall | -18.5 to -18.1 | -26 to +26 | 1.2 to 18 | Stage_House::Walls_West |
| Roof | -18.5 to +18.5 | -26 to +26 | 18 to 18.4 | Stage_House::Roof |
| Parapets (4) | perimeter | perimeter | 18.4 to 19 | Stage_House::Parapet |

Wall thickness: 0.4m (stage house), 0.3m (support wing)

### Support Wing (east side, 2 stories)
| Element | X Range | Y Range | Z Range | Layer |
|---------|---------|---------|---------|-------|
| East wall | +32.2 to +32.5 | -26 to +26 | 0 to 8.5 | Support_Wing::Walls_Exterior |
| South wall | +18.5 to +32.5 | -26 to -25.7 | 0 to 8.5 | Support_Wing::Walls_Exterior |
| North wall | +18.5 to +32.5 | +25.7 to +26 | 0 to 8.5 | Support_Wing::Walls_Exterior |
| GF slab | +18.5 to +32.5 | -26 to +26 | 0 to 0.3 | Support_Wing::Floor_Slab_GF |
| Upper slab | +18.5 to +32.5 | -26 to +26 | 4.0 to 4.3 | Support_Wing::Floor_Slab_Upper |
| Roof | +18.5 to +32.5 | -26 to +26 | 8.5 to 8.8 | Support_Wing::Roof |

### LED Volume (inside stage)
| Element | Shape/Dimensions | Z Range | Layer |
|---------|-----------------|---------|-------|
| Curved wall | 270° elliptical arc, center (0,-8), semi-X=10, semi-Y=6 | 1.35 to 8.35 | LED_Volume::Curved_Wall |
| Ceiling panels | Box: X ±6, Y -12 to -4 | 8.15 to 8.35 | LED_Volume::Ceiling_Panels |
| Raised platform | ~matches wall interior | Z=1.35 | LED_Volume::Raised_Platform |

Mouth (open side) faces north (~Y=-2 line). Deepest point ~Y=-14.

### Loading Dock (north)
| Element | X Range | Y Range | Z Range | Layer |
|---------|---------|---------|---------|-------|
| Dock platform | -10 to +10 | +26 to +29 | 0 to 1.2 | Stage_House::Loading_Dock |
| Large roll-up door | -3 to +3 | ~26 | 1.2 to 6.2 | Stage_House::Roll_Up_Doors |
| Standard dock door | +8 to +11.5 | ~26 | 1.2 to 5.2 | Stage_House::Roll_Up_Doors |
| Drive-on ramp | -18.5 to -14.5 | +20 to +26 | 0→1.2 | Stage_House::Ramp_West |

### Rigging Grid
- 7 EW trusses at X = -15, -10, -5, 0, +5, +10, +15
- 6 NS trusses at Y = -20, -12, -4, +4, +12, +20
- Truss cross-section: 0.3m wide × 0.6m deep
- Bottom of truss at Z=15.0

### Glazing
| Element | Location | Z Range | Layer |
|---------|----------|---------|-------|
| South entry glass | X ±4, Y ~-25.5 | 0.3 to 3.5 | Glazing::South_Facade |
| Brain bar window | X ~18.5, Y ±3 | 4.5 to 6.9 | Glazing::Brain_Bar |
| Gallery glass | X ~18.5, Y -12 to -8 | 4.5 to 6.5 | Glazing::Gallery |
| SW south glass (GF) | X 20-30, Y ~-26 | 0.8 to 2.8 | Glazing::Support_Wing |
| SW south glass (Upper) | X 20-30, Y ~-26 | 4.8 to 6.8 | Glazing::Support_Wing |

### Entry / Exterior
| Element | Location | Z Range | Layer |
|---------|----------|---------|-------|
| Entry canopy | X ±5, Y -29 to -26 | 3.5 to 3.8 | Exterior_Detail::Entry_Canopy |
| Backlit signage | X ±4, Y ~-26 | 3.8 to 5.5 | Client::Signage_Panel |

### Site
| Element | Dimensions | Z | Layer |
|---------|-----------|---|-------|
| Asphalt lot | 120m × 120m | -0.05 | Site::Asphalt_Lot |
| Concrete apron | 75m × 87m (-30.5 to +44.5 X, -41 to +46 Y) | 0.0 | Site::Concrete_Apron |

## Layer Structure (62 custom layers)
Parent layers: Site, Stage_House, LED_Volume, Rigging_Grid, Support_Wing, Brain_Bar, Client, Glazing, Exterior_Detail, MEP, Context, Reference

## Phase 2 Objects (+157 = 202 total)

### Exterior Detail
| Element | Count | Layer |
|---------|-------|-------|
| Cement board panels (south facade) | 2 | Exterior_Detail::Cement_Board_Panels |
| Standing-seam panel reveals (all walls) | 65 | Exterior_Detail::Metal_Panels_Vertical |

Reveals: 40mm wide ribs at 2m spacing. West: 25 at X=-18.55, East: 25 at X=18.5, North: skip door zones, South: outer edges only.

### Support Wing Interior Partitions
Wall thickness: 0.15m. GF Z: 0.3-4.0, Upper Z: 4.3-8.5.

**GF rooms (N→S):** Scenic workshop (Y 16-26), Grip storage (Y 8-16), Camera prep (Y 2-8), LED processor (Y -4 to 2), Server room (Y -8 to -4), Hair/makeup (Y -14 to -8), Green rooms x2 (Y -18 to -14), Services (Y -26 to -18). Corridor: X 18.5-21 (west side).

**Upper floor (N→S):** Bullpen (Y 18-26), Conference (Y 13-18), Office 1 (Y 9-13), Office 2 (Y 5-9), Office 3 (Y 1-5), Brain bar (Y -5 to 1, east wall X=30.5), Client gallery (Y -9 to -5), South corridor (Y -26 to -9). Corridor: X 18.5-21.

| Element | Count | Layer |
|---------|-------|-------|
| GF partitions + corridor wall | 9 | Support_Wing::Interior_Walls_GF |
| Upper partitions + corridor wall | 9 | Support_Wing::Interior_Walls_Upper |
| Stair/elevator core (X 26-30, Y -26 to -22) | 1 | Support_Wing::Stairs_Elevator |

### Site & Context
| Element | Count | Layer |
|---------|-------|-------|
| Dock leveler (X 8-11.5, Y 26-27.5) | 1 | Stage_House::Loading_Dock |
| Bollards (corners + dock protection) | 9 | Site::Bollards |
| Crew entrance door (X 32.45-32.55) | 1 | Glazing::Support_Wing |
| Break area (pad + shade + 4 posts) | 6 | Site::Break_Area |
| String lights (catenary pipes) | 4 | Context::String_Lights |
| Pole lights (14 poles + 14 heads) | 28 | Context::Pole_Lights |
| Production trucks (3 trucks, 5 boxes) | 5 | Context::Production_Trucks |
| Base camp trailers (east of building) | 3 | Context::Base_Camp_Trailers |

### MEP
| Element | Count | Layer |
|---------|-------|-------|
| HVAC units (6 stage roof + 3 SW roof) | 9 | MEP::Rooftop_HVAC |
| Parapet screens (west + east) | 2 | MEP::Parapet_Screen |

### Drives & Service
| Element | Count | Layer |
|---------|-------|-------|
| North drive | 1 | Site::Drive_North |
| South drive | 1 | Site::Drive_South |
| Service corridor floor | 1 | LED_Volume::Service_Corridor |

## Phase 3-5 Objects (+72 = 274 total)

### Glazing Mullions
Mullion dimensions: 50mm wide x 80mm deep. Layer: Glazing::Mullions.

| Location | Verticals | Horizontals | Total |
|----------|-----------|-------------|-------|
| South facade entry (X -4 to 4) | 6 | 2 (Z 1.8, 3.5) | 8 |
| Brain bar window (Y -3 to 3) | 5 | 1 (Z 6.2) | 6 |
| Gallery glass (Y -7 to -5) | 3 | 1 (Z 6.0) | 4 |
| SW strip GF (X 19-25, Z 1-3) | 5 | 1 (Z 2.0) | 6 |
| SW strip upper (X 19-25, Z 5-7) | 5 | 1 (Z 6.0) | 6 |
| **Total** | | | **30** |

### Architectural Detail
| Element | Count | Layer |
|---------|-------|-------|
| Interior doors (8 GF + 7 upper) | 15 | Support_Wing::Doors |
| Acoustic shell walls (box-in-box) | 5 | Stage_House::Acoustic_Shell |
| Cable trays (4 EW + 3 NS at Z=14.2) | 7 | Rigging_Grid::Cable_Trays |
| LED frame columns (10 @ 30° intervals) | 10 | LED_Volume::Steel_Frame |
| Entry steps (3) + ADA ramp | 4 | Client::South_Entrance |
| Reception desk | 1 | Client::Reception_Lobby |

Acoustic shell: 0.2m thick, 0.3m air gap from outer walls, Z 1.2-17.0m. East wall split at Y=-7.5 and Y=3.5 to clear brain bar and gallery windows.

## Furnishing Phase Objects (+177 = 451 total)

### Stage Production Equipment (41 objects)
| Element | Count | Location | Layer |
|---------|-------|----------|-------|
| Camera pedestals (base+col+head) | 9 | (0,-4), (-5,-2), (5,-2) on LED platform Z=1.35 | Stage_Production::Cameras |
| Jib arm (base+arm) | 2 | (0, 9) north side | Stage_Production::Cameras |
| Video village table | 1 | (0, 3) behind cameras | Stage_Production::Video_Village |
| VV monitors | 4 | on table | Stage_Production::Video_Village |
| VV director chairs | 3 | behind table | Stage_Production::Video_Village |
| C-stands (base+pole) | 16 | 8 positions around LED volume | Stage_Production::Grip_Equipment |
| Apple boxes | 4 | near service corridor | Stage_Production::Grip_Equipment |
| Hero vehicle (body+roof) | 2 | (0, -8.75) on LED platform | Stage_Production::Set_Pieces |

### Support Wing GF Furniture (32 objects)
| Room | Elements | Count | Layer |
|------|----------|-------|-------|
| Scenic workshop (Y 16-26) | 3 tables + wall shelving | 4 | Support_Wing::Furniture_GF |
| Grip storage (Y 8-16) | 2 carts + shelving | 3 | Support_Wing::Furniture_GF |
| Camera prep (Y 2-8) | workbench + 3 Pelican cases | 4 | Support_Wing::Furniture_GF |
| LED processor (Y -4 to 2) | 4 equipment racks + desk | 5 | Support_Wing::Furniture_GF |
| Server room (Y -8 to -4) | 6 server racks (2x3) | 6 | Support_Wing::Furniture_GF |
| Hair/makeup (Y -14 to -8) | 3 vanity+mirror + styling chair | 7 | Support_Wing::Furniture_GF |
| Green rooms (Y -18 to -14) | 2 couches | 2 | Support_Wing::Furniture_GF |
| Services (Y -26 to -18) | kitchenette counter | 1 | Support_Wing::Furniture_GF |

### Support Wing Upper Furniture (44 objects)
| Room | Elements | Count | Layer |
|------|----------|-------|-------|
| Brain bar (Y -5 to 1) | console desk + 8 monitors + ref monitor + 4 chairs | 14 | Support_Wing::Furniture_Upper |
| Gallery (Y -9 to -5) | 4 seats + coffee table | 5 | Support_Wing::Furniture_Upper |
| Offices x3 (Y 1-13) | desk + monitor + chair each | 9 | Support_Wing::Furniture_Upper |
| Conference (Y 13-18) | table + 8 chairs + display | 10 | Support_Wing::Furniture_Upper |
| Bullpen (Y 18-26) | 6 workstation desks | 6 | Support_Wing::Furniture_Upper |

### Electrical/MEP (12 objects)
| Element | Count | Location | Layer |
|---------|-------|----------|-------|
| Main switchgear (2MW) | 1 | GF services area | MEP::Electrical |
| PDU panels | 4 | GF north wall | MEP::Electrical |
| Transformer pad | 1 | exterior east (X 34-37) | MEP::Electrical |
| Generator pad | 1 | north (X -16 to -12, Y 28-31) | MEP::Electrical |
| Cam-lok panel | 1 | on generator pad | MEP::Electrical |
| Stage power distro boxes | 4 | stage house walls | MEP::Electrical |

### Production Lighting (20 objects)
| Element | Count | Z Range | Layer |
|---------|-------|---------|-------|
| Key/fill LED panels (yoke+head) | 8 | 13.0-15.0 | Stage_Production::Studio_Lights |
| Backlight fixtures (yoke+head) | 8 | 13.2-15.0 | Stage_Production::Studio_Lights |
| Practical accent lights | 4 | 3.0-3.5 | Stage_Production::Studio_Lights |

### Landscaping and Signage (28 objects)
| Element | Count | Layer |
|---------|-------|-------|
| Trees (trunk+canopy) | 24 | Site::Landscaping |
| Entry planters | 2 | Site::Landscaping |
| Monument sign (base+face) | 2 | Client::Signage_Panel |

## Phase Notes
- Phase 1 (Site Prep) is N/A — flat production lot, no terrain/retaining walls needed
- Phase 0 baseline: 45 objects — Checkpoint: base_model_checkpoint_20260629_1143.3dm
- Phase 2 total: 202 objects — Checkpoint: base_model_checkpoint_20260629_1154.3dm
- Phase 3-5 total: 274 objects — Checkpoint: base_model_checkpoint_20260629_1200.3dm
- Furnishing total: 451 objects — Checkpoint: base_model_checkpoint_20260629_1208.3dm
- Next: Phase 6 (Export to Blender) — requires BlenderMCP on port 9876
