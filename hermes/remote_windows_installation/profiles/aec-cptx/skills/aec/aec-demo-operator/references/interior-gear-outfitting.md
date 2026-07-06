# Interior Gear Outfitting — Building Equipment as Primitives

Pattern for furnishing architectural models with industry-specific equipment using simple Rhino C# primitives (boxes, cylinders, spheres). Proven June 30 2026 on VP studio (252 gear objects, 342 total scene objects).

## When to use

After Phase 06 (detailing) is complete and the building shell exists. Gear outfitting adds:
- Production equipment (cameras, cranes, C-stands, lighting)
- Interior furniture (desks, chairs, server racks, workbenches)
- Vehicles (production trucks, equipment carts)
- Cable runs and infrastructure details

This makes the building read as a working facility rather than empty architecture.

## Layer structure

Create dedicated gear layers BEFORE building any equipment:

```csharp
doc.Layers.Add("Gear", System.Drawing.Color.Orange);
doc.Layers.Add("Gear::Camera", System.Drawing.Color.OrangeRed);
doc.Layers.Add("Gear::Grip", System.Drawing.Color.Chocolate);
doc.Layers.Add("Gear::Lighting", System.Drawing.Color.Gold);
doc.Layers.Add("Gear::Brain_Bar", System.Drawing.Color.MediumSlateBlue);
doc.Layers.Add("Gear::Workshop", System.Drawing.Color.Sienna);
doc.Layers.Add("Gear::Vehicles", System.Drawing.Color.DarkRed);
doc.Layers.Add("Gear::Cables", System.Drawing.Color.DarkOliveGreen);
```

## Construction patterns

All gear is built from three primitives. See `references/rhino-csharp-scripting-pitfalls.md` items 6, 14, 15 for API details.

### Box (bodies, desks, crates, racks)
```csharp
var box = new Rhino.Geometry.Box(new Rhino.Geometry.BoundingBox(
    new Rhino.Geometry.Point3d(x1, y1, z1),
    new Rhino.Geometry.Point3d(x2, y2, z2)));
doc.Objects.AddBrep(box.ToBrep(), attr);
```

### Cylinder (legs, posts, lenses, wheels)
```csharp
var mid = (start + end) / 2;
var dir = end - start;
var plane = new Rhino.Geometry.Plane(mid, dir);
var cyl = new Rhino.Geometry.Cylinder(
    new Rhino.Geometry.Circle(plane, radius), dir.Length);
doc.Objects.AddBrep(cyl.ToBrep(true, true), attr);
```

### Sphere (light bulbs, joints)
```csharp
var sphere = new Rhino.Geometry.Sphere(center, radius);
doc.Objects.AddBrep(sphere.ToBrep(), attr);
```

## Equipment categories and scale guide

### Camera equipment (Gear::Camera)
| Item | Primitives | Scale | Key dimensions |
|------|-----------|-------|----------------|
| Camera crane | 3 cyl legs + cyl post + 2 box arms + box counterweight + box body + cyl lens | Real | Jib 4-6m, post 1.5m, legs 1m splay |
| Film camera on tripod | 3 cyl legs + cyl post + box body + cyl lens | Real | Post 1.2m, legs 0.6m splay |
| Camera body | Box | Real | 0.3x0.24x0.2m |
| Camera lens | Cylinder | Real | Radius 0.06-0.1m, length 0.15-0.3m |

### Grip equipment (Gear::Grip)
| Item | Primitives | Scale | Key dimensions |
|------|-----------|-------|----------------|
| C-stand | 3 cyl legs + cyl riser + box flag | Real | Riser 2m, legs 0.4m splay |
| Apple box | Box | Real | 0.5x0.8x0.15m |
| Sandbag | Box (flat) | Real | 0.3x0.4x0.08m |

### Lighting (Gear::Lighting)
| Item | Primitives | Scale | Key dimensions |
|------|-----------|-------|----------------|
| Space light | cyl housing + cyl cable + sphere bulb | Real | Housing 0.6m dia x 0.7m, hangs 1.5m below grid |
| Speaker | Box + box bracket | Real | 0.6x0.4x0.5m |
| Cable bundle | Box (flat, long) | Real | 0.1m thick, spans truss length |

### Brain bar / control room (Gear::Brain_Bar)
| Item | Primitives | Scale | Key dimensions |
|------|-----------|-------|----------------|
| Operator desk | Box top + 4 box legs | Real | 1.6x1.2m, height 0.75m |
| Monitor | Box screen + box stand | Real | 0.02x0.6x0.4m screen |
| Chair | Box seat + box back | Real | 0.5x0.5m, height 0.45m seat |
| Server rack | Box body + 8 box LED indicators | Real | 0.8x0.6m, 2m tall |
| Audio mixing desk | Box desk + box console | Real | 1x1.6m, console 0.1m raised |

### Workshop (Gear::Workshop)
| Item | Primitives | Scale | Key dimensions |
|------|-----------|-------|----------------|
| Workbench | Box top + 4 box legs | Real | 1.2x6m, height 0.8m |
| Paint table | Box | Real | 0.6x8m, height 0.7m |
| Tool rack | Box (tall, thin) | Real | 0.5x6m, 2m tall |
| Shelf | Box (tall, thin) | Real | 0.4x1m, 2.2m tall |

### Vehicles (Gear::Vehicles)
| Item | Primitives | Scale | Key dimensions |
|------|-----------|-------|----------------|
| Flatbed truck | Box cab + box windshield + box flatbed + 3 box crates + 6 cyl wheels | Real | Cab 4x3x3m, flatbed 14x3m |
| Cargo crate | Box | Real | 1-3m cubes |

## Naming convention

Use descriptive names with position qualifiers for easy selection:
```
Crane_Leg_1, Crane_Leg_2, Crane_Leg_3
Crane_Post, Crane_Jib_Forward, Crane_Jib_Counter_Arm
CStand_1_Riser, CStand_1_Flag
SpaceLight_-12_-18, SpaceLight_-12_-18_Cable, SpaceLight_-12_-18_Bulb
BB_Desk_Unreal_Operator, BB_Monitor_Unreal_Operator_1
Truck_Cab, Truck_Windshield, Truck_Flatbed, Truck_Crate_1
```

## Positioning strategy

1. **Stage floor gear**: Place relative to LED volume center (e.g. (0, -8) for VP studio). Camera crane at volume opening (north side). C-stands around volume perimeter at 3m intervals.

2. **Rigging grid gear**: Space lights at regular grid intervals (e.g. every 8m in both directions), hanging 1.5m below grid Z. Speakers at volume corners.

3. **Brain bar gear**: Desks 1m from window wall, facing the window. 3 stations at 2m intervals along the wall. Server racks along the back wall.

4. **Support room gear**: Racks along walls, workbenches centered. Lens cases and camera stands in camera prep room.

5. **Loading dock**: Truck 2m from building face, centered on dock door. Cargo crates on flatbed.

## Batch building pattern

Build gear in batches by category — one C# script per category. This keeps each script under the compile/run limit and makes debugging easier:

1. Script 1: Create gear layers + camera crane + film camera
2. Script 2: C-stands + apple boxes + sandbags + cable runs
3. Script 3: Space lights + cable bundles + speakers (rigging grid)
4. Script 4: Brain bar operator stations + server racks + client chairs
5. Script 5: LED processor room + server room + workshop + camera prep
6. Script 6: Loading dock truck

Each script typically creates 20-80 objects. Total for VP studio: 252 gear objects in 6 scripts.

## Export to Blender

Gear exports with the building via the same `SelAll` + `-Export` OBJ workflow. In Blender, gear faces are assigned to a dark "Gear" material slot by position-based heuristic (faces at Z 1.2-3.5 within the stage house interior, or Z 0.2-4.5 within the support wing X range). See `references/blender-export-and-setup.md` "Face-center material assignment" section.

**Note:** Gear objects significantly increase OBJ mesh density. The VP studio with 342 objects produced 91,685 faces / 96,965 vertices — vs 10,835 faces without gear. Render time impact is minimal (Cycles handles 100K faces easily) but OBJ file size grows from ~2MB to ~8MB.
