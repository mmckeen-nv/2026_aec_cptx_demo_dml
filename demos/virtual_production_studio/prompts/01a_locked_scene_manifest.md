# VP Studio 01 locked scene manifest

Status: **authoritative geometry schedule for the demo**. Follow these values
verbatim. Do not resize, relocate, mirror, rotate, reinterpret, optimize, or
substitute any scheduled item unless the user explicitly requests a revision.

This is a conceptual demonstration model, not construction documentation.

## 1. Coordinate system and units

- Rhino model units: **inches**.
- Absolute tolerance: **0.01 in**.
- Angle tolerance: **0.1 degrees**.
- World X: west (-) to east (+).
- World Y: south/loading (-) to north (+).
- World Z: finished stage floor (0) upward (+).
- Building center and project datum: **(0, 0, 0)**.
- All coordinates below are absolute world coordinates.
- Never create a phase-local origin. Never use a helper whose origin is implicit.
- Curves and polar helpers must accept explicit `cx` and `cy` arguments.

## 2. Hard containment envelopes

| Envelope | X min | X max | Y min | Y max | Z min | Z max |
|---|---:|---:|---:|---:|---:|---:|
| Entire building exterior | -1080 | 1080 | -900 | 900 | -8 | 588 |
| Interior clear volume | -1068 | 1068 | -888 | 888 | 0 | 576 |
| Main stage planning zone | -720 | 720 | -600 | 600 | 0 | 576 |
| West support zone | -1068 | -744 | -600 | 888 | 0 | 576 |
| East ancillary zone | 744 | 1068 | -888 | 888 | 0 | 576 |
| South loading/scenery route | -720 | 720 | -888 | -624 | 0 | 192 |
| Overhead rigging zone | -600 | 600 | -480 | 480 | 480 | 516 |

No object may extend outside its assigned envelope. Decorative thickness must
grow inward or remain inside the listed envelope.

## 3. Building shell

| Item | Exact geometry |
|---|---|
| Floor slab | X -1080..1080, Y -900..900, Z -8..0 |
| South exterior wall | X -1080..1080, Y -900..-888, Z 0..576 |
| North exterior wall | X -1080..1080, Y 888..900, Z 0..576 |
| West exterior wall | X -1080..-1068, Y -888..888, Z 0..576 |
| East exterior wall | X 1068..1080, Y -888..888, Z 0..576 |
| Roof slab | X -1080..1080, Y -900..900, Z 576..588 |
| Clear stage height | Z 0..480 minimum, unobstructed below grid |

South loading doors are voids in the south wall, not objects overlapping it:

| Door | X opening | Y | Z opening |
|---|---:|---:|---:|
| OH_DOOR_01 | -600..-432 | -900..-888 | 0..192 |
| OH_DOOR_02 | -360..-192 | -900..-888 | 0..192 |

Each overhead door is exactly 14 ft wide x 16 ft high. Model a 6 in deep frame
inside the wall plane. The clear scenery route runs north from both doors through
the south loading zone and must remain free of furniture and equipment.

## 4. Fixed plan zones and rooms

Partition thickness: **6 in**. Room clear height: **144 in**. Ceiling proxy:
Z 144..150. Door clear opening: **42 in wide x 84 in high**, except where noted.

Room rectangles are clear inside faces; walls sit immediately outside the
rectangle while remaining inside the ancillary envelope.

### East ancillary bar

| Room | X min | X max | Y min | Y max | Clear size |
|---|---:|---:|---:|---:|---|
| Lobby / crew entry | 744 | 1068 | -888 | -720 | 27 x 14 ft |
| Toilets | 744 | 1068 | -720 | -540 | 27 x 15 ft |
| Shop / storage | 744 | 1068 | -540 | -180 | 27 x 30 ft |
| Green room | 744 | 900 | -180 | 60 | 13 x 20 ft |
| Wardrobe / makeup | 900 | 1068 | -180 | 60 | 14 x 20 ft |
| Camera prep | 744 | 900 | 60 | 300 | 13 x 20 ft |
| Production office | 900 | 1068 | 60 | 300 | 14 x 20 ft |
| Media server | 744 | 900 | 300 | 480 | 13 x 15 ft |
| Edit / color | 900 | 1068 | 300 | 480 | 14 x 15 ft |
| Control room | 744 | 1068 | 480 | 888 | 27 x 34 ft |

Control-room viewing glazing: X 744..750, Y 570..798, Z 42..126. The glazing
faces west toward the stage.

Every personnel door is a 42 in wide x 84 in high void at the scheduled wall:

| Door | Wall / centerline | Opening span |
|---|---|---|
| Lobby exterior entry | south wall Y=-888 | X 885..927 |
| Lobby to toilets | wall Y=-720 | X 885..927 |
| Toilets to shop/storage | wall Y=-540 | X 885..927 |
| Shop to green room | wall Y=-180 | X 801..843 |
| Shop to wardrobe/makeup | wall Y=-180 | X 963..1005 |
| Green room to camera prep | wall Y=60 | X 801..843 |
| Wardrobe to production office | wall Y=60 | X 963..1005 |
| Camera prep to media server | wall Y=300 | X 801..843 |
| Production office to edit/color | wall Y=300 | X 963..1005 |
| Media/edit to control room | wall Y=480 | X 885..927 |

### West support bar

| Zone | X min | X max | Y min | Y max | Use |
|---|---:|---:|---:|---:|---|
| Equipment parking | -1068 | -744 | -600 | 240 | carts and road cases only |
| Crew review / waiting | -1068 | -744 | 240 | 888 | 12 movable chairs |

Maintain a 48 in continuous circulation strip along X -792..-744. No furniture
or equipment may enter that strip.

## 5. LED volume

The LED volume uses one explicit center: **C = (-120, 0, 0)**.

The wall is the northern semicircle and opens toward negative Y:

- Start angle: **0 degrees**.
- End angle: **180 degrees**.
- Active-face radius: **480 in**.
- Active height: **288 in**, Z 0..288.
- Active surface thickness: **2 in**, extending radially outward.
- Rear support depth: **18 in**, extending outward from the active surface.
- Service clearance: **72 in** beyond the rear support.
- Maximum radial envelope: **572 in** from C.
- Permitted total bounds: X -692..452, Y 0..572, Z 0..312.
- The visible face is one smooth NURBS/extrusion surface. Panel seams may not
  alter its radius or silhouette.
- Panel planning module: 19.685 in x 19.685 in (500 mm square).
- Do not approximate the finished wall with boxes or independent flat panels.

Every polar point must use this exact helper relationship:

```text
P(cx, cy, radius, angle) =
  (cx + radius * cos(angle), cy + radius * sin(angle), z)
```

Never use `(radius*cos(angle), radius*sin(angle))` without adding `cx` and `cy`.

Additional LED elements:

| Item | Exact geometry |
|---|---|
| LED floor proxy | X -360..120, Y -420..-60, Z 0..2 (40 x 30 ft) |
| LED ceiling active face | X -300..60, Y -240..0, Z 288..290 (30 x 20 ft) |
| LED ceiling support | same X/Y, Z 290..306 |
| Talent zone | X -300..60, Y -360..-120, Z 0; keep clear |
| Calibration target storage | X 540..696, Y 360..552, Z 0..96 |

The 120 in preferred talent stand-off is measured from the nearest active LED
face. The talent zone, floor proxy, and ceiling must remain centered on the same
LED datum and may not be recentered independently.

## 6. Rigging and lighting datums

No floor-supported rigging columns are permitted inside the main stage zone.
The grid is conceptually roof-hung.

- Grid chord bottom: Z 480.
- Grid chord top: Z 516.
- Truss proxy width: 24 in.
- Truss proxy depth: 36 in.
- Main east-west truss centerlines: Y = -480, -240, 0, 240, 480;
  each spans X -600..600.
- Cross-truss centerlines: X = -600, -360, -120, 120, 360, 600;
  each spans Y -480..480.
- Hoist/drop points occur only at intersections of those centerlines.
- Each hoist proxy: 18 x 18 x 24 in, its top at Z 480.
- Catwalk proxy: X -660..660, Y 528..576, walking surface Z 420, guard top Z 462.

Twelve stage-light proxies are centered at these grid coordinates, all with
fixture body 24 x 12 x 12 in and lens aimed toward the talent zone:

```text
(-360,-240,468), (-120,-240,468), (120,-240,468), (360,-240,468),
(-360,   0,468), (-120,   0,468), (120,   0,468), (360,   0,468),
(-360, 240,468), (-120, 240,468), (120, 240,468), (360, 240,468)
```

## 7. Cameras and movement envelopes

Camera proxies use: body 24 x 12 x 12 in, lens 12 in long x 8 in diameter,
tripod footprint 48 in diameter, nominal lens/eye Z 66 in unless stated.

| Camera | Fixed mark / envelope | Exact requirement |
|---|---|---|
| CAM_A_HERO_TRACKED | lens point (-480,-420,66) | aimed at (-120,60,72); 24-35 mm note |
| CAM_B_DOLLY_TRACKED | path X -120..360 at Y -540, Z 0; home (120,-540,66) | exactly 480 in long; aimed at (-120,60,72); 35-50 mm note |
| CAM_C_CRANE_TRACKED | base (360,-240,0) | 300 in swept radius; boom proxy 240 in |
| CAM_D_HANDHELD_TRACKED | X -600..-360, Y -360..-120 | operating-zone outline only; no fixed tripod |
| CAM_E_WITNESS | lens point (600,-420,66) | aimed at (-120,60,72); fixed wide view |
| CAM_F_CONTROL_ROOM | lens point (750,684,66) | aimed at (-120,0,72); behind control glazing |

Movement envelopes are named curves/surfaces, not opaque solids. Furniture,
carts, cases, lights, and scenery may not intersect any camera envelope.

## 8. Furniture and equipment

Rhino creates named proxies at the exact marks below. Blender may replace them,
but replacements must retain the same center, floor contact, and maximum envelope.

### Control room

Six workstations, each **72 W x 30 D x 30 H in**, face west. Width runs along
Y; depth runs along X. Centers:

```text
(804,570), (804,684), (804,798),
(960,570), (960,684), (960,798)
```

Six operator chairs, each maximum **24 W x 24 D x 42 H in**, centers:

```text
(852,570), (852,684), (852,798),
(1008,570), (1008,684), (1008,798)
```

### Crew review chairs

Twelve movable, human-scale chair proxies, each **24 W x 24 D x 42 H in**. Centers:

```text
(-1008,330), (-936,330), (-864,330),
(-1008,414), (-936,414), (-864,414),
(-1008,498), (-936,498), (-864,498),
(-1008,582), (-936,582), (-864,582)
```

### Equipment parking

- Four carts, each 48 x 24 x 42 in, centers:
  `(-1008,-504)`, `(-936,-504)`, `(-864,-504)`, `(-816,-504)`.
- Six road cases, each 48 x 24 x 30 in, centers:
  `(-1008,-408)`, `(-912,-408)`, `(-816,-408)`,
  `(-1008,-324)`, `(-912,-324)`, `(-816,-324)`.
- Dolly base: 60 x 36 x 12 in, centered on CAM_B at `(120,-540)`.
- Crane base maximum: 72 x 72 x 24 in, centered at `(360,-240)`.
- Two calibration targets: 48 W x 6 D x 72 H in, stored at
  `(588,456)` and `(648,456)` when not deployed.

### Required hero set dressing proxies

These proxies are mandatory because Blender replaces them with the approved
cached assets used in the presentation render. They sit outside the protected
talent zone and fixed camera-movement envelopes.

| Proxy | Center (in) | Maximum size (in) | Blender role |
|---|---:|---:|---|
| STAGE_DIRECTOR_CHAIR_01 | (-420,-60,0) | 24 x 24 x 42 | production seating |
| STAGE_DIRECTOR_CHAIR_02 | (540,60,0) | 24 x 24 x 42 | production seating |
| HERO_ROAD_CASE_01 | (-600,-420,0) | 48 x 24 x 30 | stage-edge road case |
| HERO_ROAD_CASE_02 | (636,-60,0) | 48 x 24 x 30 | stage-edge road case |
| FLOOR_LIGHT_01 | (-660,-120,0) | 24 x 24 x 72 | complete LED soft-panel stand |
| FLOOR_LIGHT_02 | (660,-120,0) | 24 x 24 x 72 | complete LED soft-panel stand |
| SERVER_RACK_01 | (786,390,0) | 24 x 42 x 84 | media-server rack |
| SERVER_RACK_02 | (858,390,0) | 24 x 42 x 84 | media-server rack |

Do not place a bare C-stand in the presentation scene. A floor-light position
must be replaced by the complete `light_led_soft_panel_roy` light-on-stand
asset. The standalone cached C-stand is inventory only and is not part of the
required hero dressing.

## 9. Required numeric validation after every phase

Visual review is necessary but never substitutes for these checks.

1. Report the document units and tolerances.
2. Report each new object's world bounding box.
3. Compare that box to its assigned envelope in this manifest.
4. Report `PASS` only when every min/max coordinate is within tolerance.
5. If any object is outside its envelope, stop the phase and correct that object
   before adding anything else.
6. Confirm the LED wall's sampled points remain 480 in from C=(-120,0) within
   0.01 in, and confirm its total bounds fit X -692..452 and Y 0..572.
7. Confirm room and equipment centers equal the scheduled coordinates within
   0.01 in.
8. Confirm no opaque object intersects the loading route, talent zone, 48 in
   west circulation strip, or camera movement envelopes.

Do not accept "looks correct," "approximately," "roughly," or "close enough" as
a numeric gate result. Any coordinate not listed here must be derived from listed
geometry and printed before it is used.
