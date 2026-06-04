# Skill — Retaining Wall with Continuous Concrete Footing (Rhino)
*Status: PENDING — saved for future use, not yet integrated into pipeline*
*Applies to: Phase 1 (Site Prep) — Rhino construction via RhinoMCP*
*Version 1.0 — May 2026*

---

## Purpose

Generate a RhinoCommon script to model a structurally sound concrete retaining
wall with a continuous footing below grade, adapting to compound-curved terrain
and handling both cut zones (wall holds back hillside) and fill zones (wall
retains fill). The footing depth adjusts per zone and respects frost depth.

---

## Input Geometry

| Input | Type | Description |
|---|---|---|
| `existing_grade` | Open BRep surface | Sloping terrain, compound curvature, single-sided, well-formed |
| `building_pad_curve` | Closed flat curve | Arbitrary plan-view profile, partially above/below `existing_grade`, within grade XY extents |

---

## Parameters

| Parameter | Default | Description |
|---|---|---|
| `wall_thickness` | 200–300 mm (8–12 in) | Horizontal wall thickness |
| `freeboard_height` | 150 mm (6 in) | Height above terrain at top of wall — prevents soil spill-over |
| `footing_width` | 600 mm (24 in) | Horizontal width of the footing |
| `footing_depth` | 300 mm (12 in) | Vertical thickness of the footing |
| `frost_depth` | 900 mm (36 in) | Min depth below lowest adjacent grade to prevent frost heave |

---

## Algorithmic Steps

### 1. Establish the Building Pad Surface
- Project `building_pad_curve` along world Z onto `existing_grade` to find the dynamic terrain intersection.
- Extrude `building_pad_curve` vertically to create a cutting volume, or use it to split `existing_grade` and isolate the interior terrain profile.
- Create flat planar surface `pad_surface` from `building_pad_curve` — this is the target finished grade elevation.

### 2. Identify Cut and Fill Zones
- Boolean Split or Intersect `pad_surface` against `existing_grade`.
- Segment the perimeter of `building_pad_curve` into:
  - **Cut Zone** — pad is lower than grade; wall holds back hillside; soil excavated
  - **Fill Zone** — pad is higher than grade; wall retains fill; soil added

### 3. Generate the Retaining Wall Profile
- Extract the outer edge curve of `pad_surface` along the Cut Zone perimeter.
- Extend vertically upward to intersect `existing_grade` — this gives the varying top-of-wall height.
- Add constant `freeboard_height` above the intersection so soil cannot spill over.
- In Fill Zones, project the curve downward to meet `existing_grade`, forming the wall base.

### 4. Construct Solid Wall Geometry
```csharp
// Offset wall profile outward by wall_thickness
Surface wallOuter = wallProfile.Offset(wallThickness, outwardNormal);

// Loft inner and outer profiles
Brep wallSurface = Brep.CreateFromLoft(
    new Curve[] { wallProfileInner, wallProfileOuter },
    Point3d.Unset, Point3d.Unset, LoftType.Straight, false)[0];

// Cap to closed solid
Brep wallSolid = wallSurface.CapPlanarHoles(doc.ModelAbsoluteTolerance);
if (!wallSolid.IsSolid)
    throw new Exception("Wall BRep not closed — check loft seams");
```

### 5. Develop Continuous Concrete Footing

#### 5a. Extract bottom curve
Extract the continuous bottom edge curve of `wallSolid`.

#### 5b. Set footing depth by zone
- **Cut Zone** — drop bottom curve by `footing_depth`
- **Fill Zone** — project curve down to `existing_grade`, then drop further by `frost_depth + footing_depth` to anchor below frost line

#### 5c. Build footing solid
```csharp
// Offset centreline by footing_width/2 each side
// (or heel-and-toe offset for better structural bearing)
double halfW = footing_width / 2.0;
Curve footingLeft  = footingCentreline.Offset(halfW, outwardDir);
Curve footingRight = footingCentreline.Offset(halfW, inwardDir);

// Extrude footing profile upward by footing_depth to meet wall base
Brep footingSolid = Brep.CreateFromSweep(footingProfile, footingPath, true)[0];
footingSolid = footingSolid.CapPlanarHoles(doc.ModelAbsoluteTolerance);
```

#### 5d. Union wall and footing
```csharp
// Monolithic assembly — single pour
Brep[] assembly = Brep.CreateBooleanUnion(
    new Brep[] { wallSolid, footingSolid },
    doc.ModelAbsoluteTolerance);

// Keep distinct if separate pours or specs are required
```

### 6. Clean and Trim Terrain
- Split `existing_grade` using the outer faces of both wall and footing.
- Delete terrain inside the building pad and footing excavation zones.
- Result: terrain reads as undisturbed up to the wall face.

---

## Output Requirements

| Object | Type | Layer |
|---|---|---|
| Wall + footing assembly | Closed watertight solid BRep | `Proposed_Wall_and_Footing` |
| Modified terrain | Trimmed BRep | `Modified_Grade` |

---

## Known Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| `wallSolid.IsSolid = false` | Loft seam gap or uncapped edge | Check naked edges via `Brep.Edges`; re-cap |
| Boolean union fails | Wall or footing not watertight | Verify `IsSolid` on both inputs before union |
| Footing floats in fill zones | Frost depth not applied | Drop to `existing_grade` first, then add `frost_depth + footing_depth` |
| Terrain trim leaves interior fragment | Split not fully separated | Use `Brep.Split`; delete interior fragment by centroid check |
| Wall offset direction inverted | Outward normal computed inward | Check normal direction against pad centroid; flip if needed |
| Footing extrudes wrong direction | Profile winding gives wrong normal | Reverse PolylineCurve point order or use negative height |

---

*Trigger: "retaining wall", "generate wall from terrain", "cut and fill wall", "add footing", "frost depth footing"*
