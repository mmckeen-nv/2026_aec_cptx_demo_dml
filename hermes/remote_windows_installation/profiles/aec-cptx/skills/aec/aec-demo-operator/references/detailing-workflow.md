# Detailing Workflow — Rhino MCP Python Scripting

Parametric procedure for adding architectural detailing to massing volumes via `mcp_rhino_run_python`.

## Layer structure

Create under a parent layer `Detailing`:

| Sublayer       | Color (RGB)       | Contents                           |
|----------------|-------------------|------------------------------------|
| glazing        | 100, 180, 220     | Glass panels (thin boxes)          |
| mullions       | 140, 100, 60      | Vertical mullions, transoms, frames|
| railings       | 80, 80, 80        | Posts + top rails                  |
| entry          | 60, 60, 60        | Pivot door panel                   |
| garage_doors   | 50, 50, 50        | Sectional door panels              |

## Standard dimensions (cliff_house_02)

- **Mullion width:** 80mm (0.08m)
- **Mullion depth:** 100mm (0.10m)
- **Glass thickness:** 20mm (0.02m)
- **Glass inset from wall face:** 50mm (0.05m)
- **Curtain wall panel module:** ~1.5m
- **Railing height:** 1.05m (code standard)
- **Railing post size:** 50mm square
- **Top rail size:** 50mm square
- **Entry door:** 1.4m wide × 2.8m tall × 80mm thick
- **Garage door:** 2.8m wide × 2.4m tall × 50mm thick

## Curtain wall glazing pattern

Two functions proven in production (June 2026, 177 objects):

- `build_cw_y(prefix, x0, x1, z0, z1, face_y, outward_dir)` — Y-constant faces (south/north)
- `build_cw_x(prefix, y0, y1, z0, z1, face_x, outward_dir)` — X-constant faces (east/west)

`outward_dir`: -1 = face outward in negative direction, +1 = face outward in positive direction.

Algorithm (same for both):

1. Determine face extent and floor-to-ceiling Z range.
2. Divide width into ~1.5m bays → `n_panels = max(int(face_width / 1.5), 1)`.
3. Glass inset from face: `gy = face_y + outward_dir * GLASS_INSET`, thickness = `outward_dir * GLASS_T`.
4. For each bay, create two glass Box objects (upper and lower), inset from face.
5. Create vertical mullion boxes at each bay boundary (n_panels + 1 mullions).
6. Create horizontal sill, transom (mid-height), and head rail spanning the full width.
7. Mullion depth extends from face position: `face_y` to `face_y + outward_dir * MULLION_D`.

**cliff_house_02 face assignments (confirmed working June 12, 2026 — 154 objects):**

Massing coordinates (mm) — June 12 simpler 2-story build:
- L1 walls: X=4500→13500, Y=-15500→4500, Z=300→3500
- L1 slab:  Z=3500→3800
- L2 walls: X=1500→13500, Y=-15500→4500, Z=3800→7000
- L2 slab:  Z=7000→7300
- Roof:     X=500→14500, Y=-16500→5500, Z=7300→7500
- Garage:   X=7000→17000, Y=4500→15000, Z=300→3100

**cliff_house_02 face assignments (June 15, 2026 — 224 CW objects, 3-tier build):**

Massing coordinates (mm) — June 15 three-tier build:
- L1_west: X=5000, Y=-15000→3000, Z=300→4050
- L1_east: X=5000→17000, Y=3000→14000, Z=300→4050
- L2_west: X=3500, Y=-15000→3000, Z=4300→8050
- L2_east: X=5000→17000, Y=3000→14000, Z=4300→8050
- L3_main: X=1500→13500, Y=-10000→3000, Z=8300→12050
- L3_roof: X=-500→15000, Y=-13500→4500, Z=12050→12350

West faces (X-constant, outward -1):
- L1 west: face_x=4500, Y=-15500→4500, Z=300→3500
- L2 west: face_x=1500, Y=-15500→4500, Z=3800→7000

South faces (Y-constant, outward -1):
- L1 south: face_y=-15500, X=4500→13500, Z=300→3500
- L2 south: face_y=-15500, X=1500→13500, Z=3800→7000

Entry door: east face X=13500, centered at Y=-5500
Garage doors: east face X=17000, centered around Y=9750, two 2800mm-wide doors with 500mm gap

## Punched windows pattern

For secondary facades (south, east, north):

1. Define window positions as center points along the face.
2. For each window, create one glass Box panel.
3. Create 4-piece frame: left, right, sill, head — all as mullion-layer boxes.

## Railing pattern

For balcony/deck edges:

1. Define edge as a list of corner points at slab-top Z.
2. Place square posts at each corner point.
3. For each edge segment, create a rectangular top rail box oriented along the edge direction using a plane constructed from the direction vector.

## Entry door

- Single oversized pivot door, inset 150mm from outer face.
- 3-piece frame/reveal: left jamb, right jamb, head — deeper (200mm) to create a shadow reveal.

## Garage doors

- Flat panel boxes, 50mm thick, nearly flush with wall face (50mm inset).
- 3-piece frame per door: left, right, head.
- Typical gap between double doors: 500mm.

## Checkpoint saves

Always save before and after detailing:
```python
import Rhino, System
doc = __rhino_doc__
stamp = System.DateTime.Now.ToString("yyyyMMdd_HHmm")
path = f"C:\\Users\\test\\Documents\\cliff_house_02_checkpoint_{stamp}.3dm"
opts = Rhino.FileIO.FileWriteOptions()
opts.WriteGeometryOnly = False
doc.WriteFile(path, opts)
```

## Pitfalls

### Box coordinate ordering (critical)

`rg.Box(Plane.WorldXY, Interval(a,b), ...)` requires `a < b` for each interval.
When computing glass/mullion positions relative to a face with negative outward direction
(e.g., face_y = -15000, outward = -1), the computed coordinates can have min > max,
producing degenerate boxes that Rhino silently discards — the script reports success
but no geometry appears.

**Always sort coordinates in the add_box helper:**
```python
def add_box(name, p0, p1, li):
    x0, x1 = min(p0[0], p1[0]), max(p0[0], p1[0])
    y0, y1 = min(p0[1], p1[1]), max(p0[1], p1[1])
    z0, z1 = min(p0[2], p1[2]), max(p0[2], p1[2])
    if x1 - x0 < 1 or y1 - y0 < 1 or z1 - z0 < 1:
        return False  # Skip degenerate
    box = rg.Box(rg.Plane.WorldXY,
                 rg.Interval(x0, x1), rg.Interval(y0, y1), rg.Interval(z0, z1))
    brep = box.ToBrep()
    if brep is None:
        return False
    attr = ro.ObjectAttributes()
    attr.Name = name
    attr.LayerIndex = li
    doc.Objects.AddBrep(brep, attr)
    return True
```

This bug caused 177 curtain wall objects to vanish on the first attempt in a live session.
The second pass with sorted coordinates succeeded immediately.

### Scope isolation between scripts

Each `mcp_rhino_run_python` call is a separate script execution — variables (like `MULLION_W`)
defined in one script are NOT available in the next. Always re-define constants in every script,
or consolidate related geometry into a single script call.

## Exterior features (pool, patio, firepit)

Additional layers under `Detailing`:

| Sublayer       | Color (RGB)       | Contents                           |
|----------------|-------------------|-------------------------------------|
| pool           | 50, 130, 180      | Pool walls, floor, water surface    |
| pool_coping    | 160, 120, 70      | Bronze coping caps around pool edge |
| patio          | 200, 190, 170     | Stone deck slabs                    |
| firepit        | 100, 90, 80       | Cylindrical firepit body            |

### Infinity pool (cliff_house_02)

- Sits on patio pad (Z top = -700). 10m long × 3m wide × 1.2m deep.
- Pool walls: 200mm thick boxes for west/east/north. South wall is thinner (100mm) and 30mm lower to suggest infinity overflow edge.
- Water surface: thin box at Z_top - 40 to Z_top - 80, inset from walls.
- Bronze coping: 150mm overhang, 80mm tall caps around perimeter. South coping 30mm lower to match infinity edge.
- Total: ~10 objects.

### Stone patio

- Cover patio pad area excluding pool footprint with 100mm-thick deck slabs.
- Split into 4 non-overlapping rectangles: north, east, west, south of pool.
- Total: 4 objects.

### Firepit

- Use `rg.Cylinder` with `rg.Circle` for round geometry (not boxes).
- Outer cylinder: 1m radius, 400mm tall. Inner bowl: 700mm radius, starts 100mm above base.
- Bronze cap ring: outer+100mm radius, 60mm tall, on pool_coping layer.
- Total: 3 objects.

## Interior elements (floor slabs, partitions, stairs)

Layers under `Interior`:

| Sublayer         | Color (RGB)       | Contents                           |
|------------------|-------------------|-------------------------------------|
| floor_slabs      | 180, 170, 160     | Concrete floor planes               |
| partition_walls  | 230, 225, 215     | Interior room dividers (200mm)      |
| stairs           | 160, 155, 145     | Individual stair treads as boxes    |
| service_core     | 200, 195, 185     | Elevator/stair shaft walls          |

### Floor slabs

- One per wing per level. Slab thickness = 250mm (matches massing gap).
- L1 floor east/west at Z=50-300 (below pad top). L2 floor east/west at Z=4050-4300. L3 floor at Z=8050-8300.
- Total: 5 objects.

### Partition walls

- 200mm thick. Full floor-to-ceiling height per level.
- Place at functional boundaries: garage/living, kitchen/service, entry hall, master bath, study, guest room, corridor, ensuite, closet.
- ~10 walls across 3 levels.

### Service core

- Vertical shaft (elevator + stair) running all 3 levels. 4 walls forming a box.
- Located at building center, e.g., X:10000-12000, Y:0-3000.
- Full height from L1 (Z=300) to L3 roof (Z=12050).
- Total: 4 objects.

### Stairs

- Adjacent to service core. Individual treads as boxes.
- L1→L2: 20 risers at 200mm rise, running north (Y:0→3000).
- L2→L3: 20 risers switchback running south (Y:3000→0).
- Total: 40 objects.

### Interior object count

Typical cliff_house_02 interior: 59 objects (5 slabs + 10 walls + 4 core + 40 treads).

## Object naming convention

Format: `{level}_{face}_{type}_{index}`
Examples: `L1_west_glass_lower_0`, `L2_cant_west_vmullion_3`, `L1_south_frame_1_head`
