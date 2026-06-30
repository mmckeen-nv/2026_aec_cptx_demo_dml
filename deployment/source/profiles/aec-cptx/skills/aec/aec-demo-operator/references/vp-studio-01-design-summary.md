# VP Studio 01 — Design Summary & Architectural Program

Virtual production stage facility for the entertainment industry demo track.

## Building Program

### Main Stage House
- Interior clear span: 50m long × 35m wide
- Clear height to rigging grid: 15m
- Total roof height: 18m
- Stage floor at dock height: 1.2m above exterior grade
- Acoustic box-in-box construction for sound isolation

### LED Volume (inside stage)
- Configuration: 270° curved wall
- Dimensions: 20m wide (chord) × 12m deep × 7m tall
- Ceiling LED panels: ~12m × 8m (optional)
- Pixel pitch: 2.6mm
- Panel modules: ~500mm × 500mm, ~1,200 total panels
- Self-supporting curved steel frame (independent of building structure)
- Rear-serviceable — 3m service corridor on all sides
- Raised platform floor (150mm) with cable management below
- Gentle inward curve at top to reduce visible edges in camera

### Two-Story Support Wing (east side)
- Per floor: ~700 sq m (total ~1,400 sq m)
- Attached to east side of stage house

#### Ground Floor (north to south):
| Space | Dimensions | Notes |
|-------|-----------|-------|
| Scenic workshop | 8m × 10m | Paint booth, dust collection, direct stage access |
| Grip/electric storage | 6m × 8m | Shelved storage: C-stands, flags, cable, distro |
| Camera prep / lens room | 4m × 6m | Climate-controlled, anti-static, secure |
| LED processor room | 4m × 6m | LED processors, media servers, network, dedicated cooling |
| Server / render room | 4m × 4m | Unreal render nodes (GPU cluster), genlock, UPS |
| Hair/makeup/wardrobe | 6m × 6m | Lighted mirrors, garment racks |
| Green rooms (×2) | 4m × 4m each | Talent holding |
| Restrooms | near south entry | M/F/accessible |
| Kitchenette / craft services | 4m × 6m | Near south break area |
| Main electrical room | 4m × 4m | 2MW service minimum |
| Mechanical room | 4m × 6m | HVAC air handlers for stage cooling |

#### Upper Floor:
| Space | Dimensions | Notes |
|-------|-----------|-------|
| Brain bar / control room | 12m × 6m | 3× Unreal stations, LED controls, DMX, audio, DIT, color science |
| Production offices (×3) | 4m × 4m each | Producer, director, AD/coordinator |
| Open bullpen | 8m × 6m | Hot desks for crew |
| Conference room | 6m × 5m | Large display for playback |
| Client viewing gallery | 6m × 4m | Glass-fronted mezzanine, separate from brain bar |

### Brain Bar Details
- Large window: 6m × 2.4m, triple-glazed for acoustic isolation
- Raised access floor for cable management
- Dedicated HVAC (significant equipment heat)
- UPS-backed power for all critical systems
- Fiber/network patch to LED processor room below

### Loading Dock (north elevation)
- Large roll-up door: 6m × 5m (flatbed truck access)
- Standard dock door: 3.5m × 4m with leveler
- Concrete apron: 20m north of building for truck staging
- 18-wheeler turning radius
- Drive-on ramp on west side
- Bollard protection at corners

### Site & Access
- Flat production lot — level concrete/asphalt
- 8m wide concrete drive (north, truck access)
- 6m wide drive (south/east/west, crew/client)
- Base camp / trailer parking to the east
- Covered outdoor break area on south side

### Entry
- South elevation: double glass doors, reception lobby (6m × 4m)
- Backlit signage panel above entry
- Crew entrance: east side, badge access, direct to support wing

## Materials Palette

| Surface | Material | Color |
|---------|----------|-------|
| Stage house walls (N/E/W) | Standing-seam metal panels (vertical) | Dark charcoal |
| South facade | Metal panels + cement board + glass entry zone | Dark charcoal / dark grey |
| Support wing | Same metal panel system, more glazing on S/W | Dark charcoal |
| Roof | Low-slope TPO membrane | Dark grey |
| Stage floor | Sealed concrete, epoxy in performance area | Dark charcoal |
| LED volume floor | Raised platform, matte surface | Matte black |
| Exposed structure/rigging | Powder-coated steel | Black |
| Window frames | Anodized aluminum | Dark bronze or black |
| Interior acoustic panels | Fabric-wrapped panels | Dark grey |
| LED wall frame | Steel | Matte black |

## Render / Hero Shot

- Camera: Southwest angle, looking northeast
- Time: Late afternoon, California lot atmosphere
- Key visual: LED wall blue/purple glow through open loading dock
- Brain bar windows glow with monitor light
- Production trucks at loading dock for context
- South entrance architectural treatment visible
- String lights at break area for atmosphere

## VP-Specific Demo Callouts (entertainment audience)

1. 270° LED wall layout and service corridor access
2. Brain bar sightline to stage through acoustic glass
3. Box-in-box acoustic isolation construction
4. 2MW electrical service (LED wall + GPU cluster + HVAC + stage power)
5. Rigging grid at 15m for overhead lighting/speakers
6. Rear-serviceable LED panels with tech corridor
7. Dedicated LED processor room and render farm room
8. Genlock/sync distribution infrastructure
9. Loading dock logistics (flatbed + palletized equipment access)
10. Client viewing gallery separate from working control room

## Technical Infrastructure (for demo credibility)

- LED wall processors + media servers in dedicated cooled room
- Unreal Engine render cluster (GPU nodes) in separate server room
- Genlock/timecode sync distribution from server room to brain bar
- Fiber backbone between processor room, server room, and brain bar
- UPS for all critical systems
- Dedicated HVAC: stage (massive — LED panels + studio lights), brain bar (equipment), server/processor rooms
- 2MW minimum electrical service
- Raised access floors in brain bar, processor room, server room
- Fire suppression in processor/server rooms
