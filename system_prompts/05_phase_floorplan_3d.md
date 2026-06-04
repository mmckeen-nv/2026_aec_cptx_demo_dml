# Phase — 3D Floor Plan Generation in Rhino
### Execution Prompt
*Part of the Hermes AEC Demo prompt suite*
*Reads: `04_phase_floorplan_2d.md` (layer hierarchy must exist first)*
*Reads: project_prompt.md for all design-specific values*
*Version 2.0 — May 2026*
*Tool chain: Rhino 3D + RhinoMCP (C# scripting)*

---

## Purpose

Extrude the 2D floor plan into a full 3D room-by-room wall model — solid wall
boxes on room-specific sublayers, with door openings, correct wall heights,
and a clean separation between the detailed 3D floor plan and the simplified
massing model volumes.

**All design-specific values — room names, floor heights, roof style, footprint
dimensions, and material assignments — come from project_prompt.md and the user
interview. Nothing in this prompt is hardcoded to a specific project.**

The 3D floor plan lives on `3D_floorplan` sublayers.
The simplified building shells live on `massing_model::WALLS`.
Both exist simultaneously and serve different purposes:
- `3D_floorplan` — interior design study, room-accurate wall segments, door gaps
- `massing_model::WALLS` — exterior massing shells, clean single solid per building volume

---

## Inputs

- Rhino document with `3D_floorplan` and `massing_model` layer hierarchy (from Phase 4)
- `project_prompt.md` — room programme, floor count, floor heights, roof style,
  building footprint, and all design-specific values
- Any reference images supplied by the user (see `00c_references_protocol.md`)

## Outputs

- `3D_floorplan::*` sublayers — solid wall segments for all rooms on all floors
- `massing_model::WALLS` — one solid box per building volume
- `massing_model::ROOF` — roof geometry appropriate to the specified roof style

---

## Pre-Phase Audit Checklist

- [ ] `04_phase_floorplan_2d.md` complete — layer hierarchy exists in Rhino
- [ ] `project_prompt.md` read — room programme, floor count, floor heights confirmed
- [ ] Roof style confirmed from project brief (flat, gable, hip, shed, mono-pitch, etc.)
- [ ] Layer Panel confirms nested structure before adding any geometry
- [ ] Delta notes read for wall heights, door positions, ceiling heights
- [ ] Previous geometry cleared if rebuilding (see Clean Rebuild procedure)

---

## Layer Assignments

Layer names are generated dynamically from the room programme in project_prompt.md.
The following are universal structural layers — always present regardless of project:

| Content | Layer |
|---|---|
| Exterior perimeter walls | `3D_floorplan::exterior_walls` |
| Massing shells (one per building volume) | `massing_model::WALLS` |
| Roof geometry | `massing_model::ROOF` |

Room-specific layers are created on demand, one per room or room group, using
the room names from the project programme. Examples:

| Room type | Layer pattern |
|---|---|
| Any bedroom | `3D_floorplan::[room_name]_walls` |
| Any bathroom | `3D_floorplan::[room_name]_walls` |
| Any service space | `3D_floorplan::[room_name]_walls` |
| Garage / ADU / barn / outbuilding | `3D_floorplan::[building_name]_walls` |

**Rule:** If the user specifies a room, it gets a layer. If a room is not in the
programme, do not create a layer for it. Never assume rooms beyond what is in
project_prompt.md.

Standard rooms that can be assumed present unless the brief says otherwise:
foundation, exterior walls, roof, kitchen, living area, dining area or room,
bedrooms (number from brief), bathrooms (number from brief), closets,
entry/foyer. All others — garage, home office, yoga studio, guest quarters,
ADU, mother-in-law unit, garden shed, horse barn, workshop, media room, etc. —
only if specified by the user.

---

## Core Geometry Constants

Establish these at the top of every wall script. All values come from
project_prompt.md — never hardcode inline:

```csharp
// From project brief — replace with actual values at runtime
double wt = {{wall_thickness}};    // wall thickness (typical 0.15–0.30m)
double dw = {{door_width}};        // standard door width (typical 0.9–1.0m)
double dh = {{door_height}};       // door height (typical 2.1m)

// Floor elevations — one per floor, from project brief
// Example for a 3-floor building:
double z_f1 = {{floor_1_z}};      // ground floor slab Z
double z_f2 = {{floor_2_z}};      // first upper floor slab Z
double z_f3 = {{floor_3_z}};      // second upper floor slab Z (if present)
// Add more as needed. Single-storey: only z_f1.

// Derived floor-to-floor heights
double h_f1 = z_f2 - z_f1;        // ground to first upper
// double h_f2 = z_f3 - z_f2;     // first upper to second upper (if present)

// Roof geometry constants — set based on roof style from project brief:
// Flat/parapet:  double z_par = {{parapet_z}};
// Pitched (gable/hip): double pitch = {{pitch_ratio}}; double eave_ov = {{eave_overhang}};
// Shed/mono-pitch: double z_high = {{high_wall_z}}; double z_low = {{low_wall_z}};
// All roof constants are variables — never hardcode to a specific style.
```

---

## Core C# Helpers

### WS — Solid wall box

```csharp
Action<double,double,double,double,double,double,int> WS =
    (x0,y0,x1,y1,z0,z1,li) => {
        var b = new Box(Plane.WorldXY,
            new Interval(x0,x1), new Interval(y0,y1), new Interval(z0,z1));
        var a = new ObjectAttributes(); a.LayerIndex = li;
        doc.Objects.AddBrep(b.ToBrep(), a);
    };
```

### XW — East–west wall, one door

Creates a wall panel running east–west (constant Y), with an optional door gap.
`xd = 0` means no door (solid wall).

```csharp
Action<double,double,double,double,int> XW =
    (yc, xa, xb, xd, li) => {
        double h = wt/2;
        if (xd <= 0) { WS(xa,yc-h,xb,yc+h,0,wh,li); return; }
        double ds = xd-dw/2, de = xd+dw/2;
        if (ds > xa) WS(xa,yc-h,ds,yc+h,0,wh,li);
        WS(ds,yc-h,de,yc+h,dh,wh,li);
        if (de < xb) WS(de,yc-h,xb,yc+h,0,wh,li);
    };
```

### YW — North–south wall, one door

```csharp
Action<double,double,double,double,int> YW =
    (xc, ya, yb, yd, li) => {
        double h = wt/2;
        if (yd <= 0) { WS(xc-h,ya,xc+h,yb,0,wh,li); return; }
        double ds = yd-dw/2, de = yd+dw/2;
        if (ds > ya) WS(xc-h,ya,xc+h,ds,0,wh,li);
        WS(xc-h,ds,xc+h,de,dh,wh,li);
        if (de < yb) WS(xc-h,de,xc+h,yb,0,wh,li);
    };
```

### XW2 / YW2 — Two-door variants

```csharp
Action<double,double,double,double,double,int> XW2 =
    (yc, xa, xb, xd1, xd2, li) => {
        double h=wt/2;
        double s1=xd1-dw/2,e1=xd1+dw/2,s2=xd2-dw/2,e2=xd2+dw/2;
        if (s1>xa) WS(xa,yc-h,s1,yc+h,0,wh,li);
        WS(s1,yc-h,e1,yc+h,dh,wh,li);
        if (e1<s2) WS(e1,yc-h,s2,yc+h,0,wh,li);
        WS(s2,yc-h,e2,yc+h,dh,wh,li);
        if (e2<xb) WS(e2,yc-h,xb,yc+h,0,wh,li);
    };

Action<double,double,double,double,double,int> YW2 =
    (xc, ya, yb, yd1, yd2, li) => {
        double h=wt/2;
        double s1=yd1-dw/2,e1=yd1+dw/2,s2=yd2-dw/2,e2=yd2+dw/2;
        if (s1>ya) WS(xc-h,ya,xc+h,s1,0,wh,li);
        WS(xc-h,s1,xc+h,e1,dh,wh,li);
        if (e1<s2) WS(xc-h,e1,xc+h,s2,0,wh,li);
        WS(xc-h,s2,xc+h,e2,dh,wh,li);
        if (e2<yb) WS(xc-h,e2,xc+h,yb,0,wh,li);
    };
```

### EX — Extrusion helper (for custom profile geometry)

Used for non-rectangular cross-sections: angled walls, roof prisms,
gable fills on pitched roofs, mono-pitch raking walls, etc.

```csharp
Action<PolylineCurve,double,int> EX = (prof,h,li) => {
    var e = Extrusion.Create(prof, h, true);
    if (e != null) {
        var a = new ObjectAttributes(); a.LayerIndex = li;
        doc.Objects.AddBrep(e.ToBrep(), a);
    }
};
```

---

## Execution Steps

### Step 1 — Exterior walls

Draw the building perimeter walls first on `3D_floorplan::exterior_walls`.
Use coordinates from project_prompt.md. Include door openings for entry,
garage, and any other specified exterior access points.

```csharp
int lExt = GL("3D_floorplan::exterior_walls");
// Coordinates from project_prompt.md — example structure only:
// XW({{south_y}}, {{west_x}}, {{east_x}}, 0, lExt);   // south wall
// YW({{west_x}}, {{south_y}}, {{north_y}}, 0, lExt);   // west wall
// XW({{north_y}}, {{west_x}}, {{east_x}}, {{entry_x}}, lExt); // north wall, entry door
// YW({{east_x}}, {{south_y}}, {{north_y}}, 0, lExt);   // east wall
// Add more walls for L-shapes, T-shapes, courtyards, outbuildings as required
```

### Step 2 — Room walls by programme

Add interior walls room by room, working through the room programme from
project_prompt.md. Create one layer per room. Build walls floor by floor,
using the correct Z base and Z top for each floor.

```csharp
// For each floor:
//   double z0 = z_f[n];       // floor base Z for this floor
//   double z1 = z_f[n+1];     // floor top Z (next floor slab, or parapet)
//   int lRoom = GL("3D_floorplan::{{room_name}}_walls");
//   // Draw walls bounding this room at (z0, z1)
//   WS(..., z0, z1, lRoom);
//
// Repeat for every room in the programme, every floor.
// Open-plan zones: define the zone boundary but do not place walls
//   where the brief says rooms are open to each other.
```

### Step 3 — Additional structures

For any structures beyond the main house volume (garage, ADU, guest cottage,
barn, shed, pool house, etc.) — create dedicated layers and wall geometry
at the correct floor elevations and footprints from the project brief.

```csharp
// Example pattern for any outbuilding:
// int lOut = GL("3D_floorplan::{{outbuilding_name}}_walls");
// WS({{x0}}, {{y0}}, {{x1}}, {{y1}}, {{z0}}, {{z1}}, lOut);
// Roof for outbuilding follows the same roof style rules as the main house
// unless the brief specifies a different roof style for that structure.
```

---

## Massing Model (massing_model::WALLS)

One solid box per building volume — not room-by-room. Volumes are derived
from the building footprint and floor count in project_prompt.md.

```csharp
int lMW = GL("massing_model::WALLS");
// One WS call per building volume, per floor where the footprint changes:
// WS({{x0}}, {{y0}}, {{x1}}, {{y1}}, {{z_base}}, {{z_top}}, lMW);
//
// Multi-storey buildings where upper floors cantilever or step:
//   add one box per floor with the correct footprint for that floor.
// Outbuildings: add one box per outbuilding volume.
```

---

## Roof Geometry (massing_model::ROOF)

Roof style and geometry are determined entirely by the project brief.
The following patterns cover the most common roof types. Apply the one
that matches the specified style — or combine as needed for complex roofs.

```csharp
int lRof = GL("massing_model::ROOF");
double slabT = 0.30;  // roof slab / cap thickness [adjustable]

// ── FLAT / PARAPET ────────────────────────────────────────────────
// Use for: contemporary, modernist, commercial, green roof
// WS({{x0}}, {{y0}}, {{x1}}, {{y1}}, {{z_par}}, {{z_par}} + slabT, lRof);

// ── GABLE (symmetric pitched) ────────────────────────────────────
// Use for: traditional, craftsman, farmhouse, colonial
// double pitch = {{pitch_ratio}};   // rise/run (e.g. 0.5 = 6:12)
// double eave  = {{eave_overhang}}; // eave overhang depth
// double ridge = {{wall_top_z}} + ({{span_y}} / 2) * pitch;
// EX triangle profile in YZ plane, extrude full X span + 2*gable_overhang

// ── HIP ──────────────────────────────────────────────────────────
// Use for: traditional, bungalow, Mediterranean
// Build 4 triangular/trapezoidal faces — N, S, E, W hip panels
// Ridge runs parallel to long axis at centre

// ── SHED / MONO-PITCH ────────────────────────────────────────────
// Use for: contemporary, agricultural, additions
// double z_high = {{high_wall_z}};
// double z_low  = {{low_wall_z}};
// EX right triangle profile, extrude full span

// ── BUTTERFLY / INVERTED ─────────────────────────────────────────
// Use for: mid-century modern, contemporary
// Two shed faces sloping inward to a central valley

// ── COMPLEX / MIXED ──────────────────────────────────────────────
// Combine above patterns for L-shaped buildings, dormers, clerestory,
// covered porches, porte-cochères, etc.
```

**Universal roof rules (apply regardless of style):**
- Roof must cover all habitable rooms with appropriate overhang
- Roof base sits at or above the wall plate height — never below
- Outbuildings use their own roof geometry at their own Z heights
- Open-air zones (patios, courtyards) explicitly have NO roof geometry
- Roof thickness is always a named variable — never hardcoded

---

## Moving Geometry After Creation

```csharp
// Hide layers that should NOT move (e.g. site outline)
int siteIdx = doc.Layers.FindByFullPath("FLOORPLAN::SITE", -1);
if (siteIdx >= 0) doc.Layers[siteIdx].IsVisible = false;
doc.Views.Redraw();
RhinoApp.RunScript("-_SelAll", false);
RhinoApp.RunScript("-_Move 0,0,0 {{delta_x}},{{delta_y}},0", false);
if (siteIdx >= 0) doc.Layers[siteIdx].IsVisible = true;
doc.Views.Redraw();
```

---

## Clean Rebuild Procedure

```csharp
var doc = RhinoDoc.ActiveDoc;
var ids = new List<Guid>();
foreach (var o in doc.Objects) ids.Add(o.Id);
foreach (var id in ids) doc.Objects.Delete(id, true);
doc.Views.Redraw();
```

Never put delete + rebuild in the same script — confirm deletion before rebuilding.

---

## Material Index Assignment

Every object created in this phase must have a User Text attribute assigning
it a material index name. This name carries through from Rhino → Blender →
ComfyUI and any components added to the workflow. It is the single source of
truth for material assignment across the entire pipeline.

```csharp
// Set material index on every object at creation time:
attrs.UserDictionary.Set("material_index", "{{material_name}}");
// e.g.: "wall_primary", "wall_secondary", "roof", "glazing", "frame",
//        "floor_slab", "foundation", "garage_door", "entry_door",
//        "patio", "railing", "terrain", etc.
// Material names are defined in project_prompt.md Section 8.
// New material names can be added at any time — update Section 8 and
// APPENDIX_materials.md accordingly.
```

The name-driven assignment pattern in APPENDIX_materials.md uses these
index names to apply Blender materials. The same index names are used in
ComfyUI segmentation masks. **Never assign a material by object colour or
layer alone** — the material_index User Text is the authoritative tag.

---

## Post-Phase Cleanup Checklist

- [ ] All room walls on correct `3D_floorplan::*` sublayers
- [ ] No objects on the Default layer or flat parent layers
- [ ] Door openings present at correct positions per project brief
- [ ] All floors at correct Z base heights from project_prompt.md
- [ ] `massing_model::WALLS` has one box shell per building volume
- [ ] `massing_model::ROOF` covers all habitable rooms
- [ ] No roof geometry over explicitly open-air zones
- [ ] Roof base Z at or above wall plate height at every wall face
- [ ] All objects have `material_index` User Text set
- [ ] No pitched roof geometry where brief specifies flat, and vice versa

---

## ▶ REVIEW GATE — 3D Floor Plan

Present:
1. Perspective viewport screenshot showing the full building complex
2. Section cut (Front view) through the main house confirming wall height
3. Layer Panel showing the complete nested hierarchy

Confirm:
- All walls solid and on correct layers
- Door openings visible in exterior walls
- Roof style matches project brief
- Roof covers all habitable rooms, overhangs correct
- Massing model shells visible and distinct from room walls
- All objects have material index tags

---

## Known Failure Modes

| Symptom | Root cause | Fix |
|---|---|---|
| All objects on "Unknown layer" | MCP tool bug with nested layers | Ignore — check Rhino Layer Panel; objects are correctly placed |
| Wall appears as open surface | Brep.JoinBreps failed | Use `Extrusion.Create` — always reliable for prismatic walls |
| Roof penetrates wall tops | Roof base Z below plate height | Set roof base Z at or above wall plate Z |
| Roof extrudes in wrong direction | Profile winding gives wrong normal | Reverse point order in PolylineCurve, or use negative height |
| Upper floor at wrong Z | Relative offset used instead of absolute Z | Always use absolute Z values from floor elevation constants |
| Missing room in layer panel | Room in programme but no layer created | Add layer and rebuild walls for that room |
| Material index missing | UserDictionary.Set not called | Add material_index to attrs before every doc.Objects.Add call |
| Object move times out | C# foreach loop too slow | Use RunScript("-_SelAll") + RunScript("-_Move ...") instead |
| Move also moves site outline | Site layer not hidden before SelAll | Hide FLOORPLAN::SITE layer before SelAll, restore after |
| Layer lookup returns Default | GL fallback set Default as current | Pre-store all layer indices at start; re-run GL if any returns 0 |
| Extrusion.Create returns null | Profile not planar | Ensure all profile points share the same X, Y, or Z value |

---

## Checkpoint Save

```csharp
string stamp = System.DateTime.Now.ToString("yyyyMMdd_HHmm");
doc.WriteFile(
    @"[project_path]\rhino_assets\base_model_checkpoint_" + stamp + ".3dm",
    new Rhino.FileIO.FileWriteOptions());
```

→ **TRAY:** Announce: "Phase complete — stop recording in the tray."

Proceed to `06_phase_detailing.md` for surface detailing and material tagging.
