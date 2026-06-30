# Rhino Python Geometry API Pitfalls

Lessons from cliff_house_02 site_prep and massing phases (June 2026).

## Document units vs reference coordinates

The cliff_house_02 base_model.3dm uses **millimeters** as document units.
The DEMO_RULES.md reference geometry bounding boxes are in **meters**.

**Always multiply DEMO_RULES coordinates by 1000** when creating geometry
via `run_python`. Example: reference says `X=1.5→17` → use `1500→17000` in code.

Verify with: `doc.ModelUnitSystem` → should say `Millimeters`.

## NetworkSrf / CreateNetworkSurface does NOT exist

`Brep.CreateNetworkSurface()` is not available in Rhino Python API.
For terrain from u/v curves, use `Brep.CreateFromLoft()` instead:

```python
import Rhino.Geometry as rg

# Sort curves by position for correct loft order
u_sorted = sorted(u_curves, key=lambda c: c.GetBoundingBox(True).Center.X)
breps = rg.Brep.CreateFromLoft(u_sorted, rg.Point3d.Unset, rg.Point3d.Unset,
                                rg.LoftType.Normal, False)
```

## CurveBrep intersection returns Point3d directly

`Intersection.CurveBrep()` returns `(bool, overlap_curves[], points[])`.
The points array contains **Point3d** objects, NOT IntersectionEvent objects.
Access Z directly: `pts[0].Z` — not `pts[0].PointA.Z`.

```python
success, overlaps, pts = rg.Intersect.Intersection.CurveBrep(curve, terrain, tol)
if success and pts and pts.Count > 0:
    z = pts[0].Z  # Direct Point3d attribute
```

## Box creation pattern — ALWAYS SORT COORDINATES

Use `rg.Box` with `Plane.WorldXY` and three `Interval` objects.

**Critical:** `rg.Interval(larger, smaller)` creates a **degenerate interval** and the resulting Box/Brep is silently invalid — `doc.Objects.AddBrep()` may return a GUID but the object doesn't persist or render. This is especially dangerous in curtain wall / detailing scripts where face_dir multipliers can flip coordinate ordering.

**Always sort min/max before creating the Box:**

```python
def add_box(name, p0, p1, layer_index):
    """Create box with sorted coordinates to avoid degenerate geometry."""
    x0, x1 = min(p0[0], p1[0]), max(p0[0], p1[0])
    y0, y1 = min(p0[1], p1[1]), max(p0[1], p1[1])
    z0, z1 = min(p0[2], p1[2]), max(p0[2], p1[2])
    # Skip degenerate (any dimension < 1mm)
    if x1 - x0 < 1 or y1 - y0 < 1 or z1 - z0 < 1:
        return False
    box = rg.Box(rg.Plane.WorldXY,
                 rg.Interval(x0, x1),
                 rg.Interval(y0, y1),
                 rg.Interval(z0, z1))
    brep = box.ToBrep()
    if brep is None:
        return False
    attr = ro.ObjectAttributes()
    attr.Name = name
    attr.LayerIndex = layer_index
    doc.Objects.AddBrep(brep, attr)
    return True
```

**Lesson learned (June 2026 detailing phase):** A curtain wall script reported 177 objects placed but only ~12 persisted because face_dir=-1 caused `face_y + (-1)*MULLION_D` to produce intervals where min > max. The fix was adding coordinate sorting — the rebuilt script with sorting placed all 177 objects correctly.

## Objects.Purge(0) after bulk delete

After deleting all objects via `doc.Objects.Delete(id, True)`, call
`doc.Objects.Purge(0)` to truly remove them from memory. Without this:
- Layers that had objects can't be deleted (they still reference purged-but-not-freed objects)
- Reimporting a file (e.g. base_model.3dm) via `doc.Import()` adds new copies
  alongside the ghost objects, resulting in doubled geometry

```python
# Correct pattern for full document clear + reimport
all_ids = [obj.Id for obj in doc.Objects]
for oid in all_ids:
    doc.Objects.Delete(oid, True)
doc.Objects.Purge(0)  # CRITICAL — free memory
doc.Import(path)      # Now imports cleanly
```

## mcp_rhino_open_doc clearFirst with UNC paths — inconsistent

`mcp_rhino_open_doc(clearFirst=True, path=r"\\wsl.localhost\...")` sometimes throws
`NullReferenceException` when there are existing objects to clear. However, on a
fresh/empty Rhino document it succeeds (confirmed June 12 and June 15, 2026 —
imported 16 objects cleanly both times).

**Rule of thumb:** `clearFirst=True` is safe on a freshly launched Rhino with no
user-created objects. If the document already has objects, use `mcp_rhino_run_python`
with the manual delete + purge + import pattern instead.

## Sampling terrain Z at a point (ray-cast pattern)

To find the terrain elevation at any (X,Y) position — e.g. to set pad/retaining wall bottom
below terrain — use a vertical LineCurve + CurveBrep intersection:

```python
def get_terrain_z(terrain_brep, x, y):
    """Cast a vertical line to find terrain Z at (x,y)."""
    line = rg.LineCurve(rg.Point3d(x, y, 5000), rg.Point3d(x, y, -10000))
    success, overlaps, pts = rg.Intersect.Intersection.CurveBrep(line, terrain_brep, tol)
    if success and pts and pts.Count > 0:
        return pts[0].Z
    return -3000  # fallback
```

Use this to sample terrain Z at pad corners + midpoints, then set pad bottom at
`min_sampled_z - 200mm` to ensure it extends below terrain everywhere.

## mcp_rhino_open_doc(clearFirst=False) works for import

`mcp_rhino_open_doc(clearFirst=False, path=...)` works reliably as a pure import.
Use it to add base_model geometry into an existing document.

`mcp_rhino_open_doc(clearFirst=True)` works on empty/fresh Rhino documents but
can fail with NullReferenceException when clearing documents that already have
objects. See "clearFirst with UNC paths" section above for the full pattern.

## Boolean difference for hollow walls

For retaining/curtain walls, boolean difference of outer - inner box works:

```python
result = rg.Brep.CreateBooleanDifference(outer_brep, inner_brep, tol)
```

Make the inner box taller than outer on top so the boolean subtraction
fully cuts through.

## SweepOneRail is fragile for angled/rotated geometry

`rg.SweepOneRail().PerformSweep(rail, section)` silently produces no output
when the section curve plane doesn't align well with the rail tangent at the
start point. This was discovered when creating structural ribs along terminal
branches at 60°/-60° angles — ALL 45 terminal branch ribs failed (0/45 success),
and 5/12 hub radial ribs failed.

**Symptoms:** `sweep.PerformSweep()` returns an empty array or a degenerate brep
that can't be capped. No error is raised.

**Root cause:** The section rectangle's plane must be perpendicular to the rail
at the sweep start. When the rail curves through 3D space at non-axis-aligned
angles, a section placed at `rail_pts[0]` with a manually constructed plane
often has the wrong orientation.

**Workaround options (in preference order):**
1. **Extrude an arch NurbsCurve along the branch direction** — 100% success rate.
   Create the arch profile as points in world space (already at the correct angle),
   then `Surface.CreateExtrusion(arch_crv, extr_vec)` where `extr_vec` is along
   the branch direction scaled to rib thickness. Proven June 15 2026: 36/36 terminal
   branch ribs succeeded vs 0/45 with SweepOneRail.
   ```python
   # For a rib perpendicular to a branch at angle_deg:
   arch_pts = []
   for j in range(n_pts):
       frac = j / (n_pts - 1.0)
       perp_pos = -hw + 2 * hw * frac
       z = rh * math.sin(frac * math.pi)
       px = cx + perp_pos * cos_p * M
       py = cy + perp_pos * sin_p * M
       arch_pts.append(rg.Point3d(px, py, z * M))
   arch_crv = rg.NurbsCurve.Create(False, 3, System.Array[rg.Point3d](arch_pts))
   extr_vec = rg.Vector3d(cos_a * thickness * M, sin_a * thickness * M, 0)
   srf = rg.Surface.CreateExtrusion(arch_crv, extr_vec)
   brep = srf.ToBrep()
   ```
2. **Use lofted cross-sections instead of sweep** — define the full cross-section
   at multiple points along the path and loft them. This is more reliable for
   complex 3D paths. (Proven: terminal branch volumes used this successfully.)
3. **Use `rg.Brep.CreatePipe()`** for circular ribs — simpler API, handles 3D paths.
4. **For rectangular ribs along angled paths**, create them as thin boxes oriented
   using `rg.Transform.Rotation()` rather than sweep.

## UV parametric sampling for panel grids on freeform surfaces

To create dense panel arrays (solar panels, cladding, curtain wall diamonds) on a
freeform NURBS surface, sample the surface in UV parameter space:

```python
srf = brep.Faces[0]
u_domain = srf.Domain(0)
v_domain = srf.Domain(1)

for i in range(nu):
    for j in range(nv):
        # Diamond pattern — offset every other row
        u_mid = u_domain.Min + (u_domain.Max - u_domain.Min) * ((i + 0.5) / nu)
        v0 = v_domain.Min + (v_domain.Max - v_domain.Min) * (j / nv)
        v1 = v_domain.Min + (v_domain.Max - v_domain.Min) * ((j + 0.5) / nv)
        v2 = v_domain.Min + (v_domain.Max - v_domain.Min) * ((j + 1) / nv)
        u0 = u_domain.Min + (u_domain.Max - u_domain.Min) * (i / nu)
        u2 = u_domain.Min + (u_domain.Max - u_domain.Min) * ((i + 1) / nu)

        pt_top = srf.PointAt(u_mid, v0)
        pt_right = srf.PointAt(u2, v1)
        pt_bottom = srf.PointAt(u_mid, v2)
        pt_left = srf.PointAt(u0, v1)

        # Skip panels at surface edges (low Z)
        if pt_top.Z < threshold and pt_right.Z < threshold:
            continue

        panel = rg.NurbsSurface.CreateFromCorners(pt_top, pt_right, pt_bottom, pt_left)
```

Proven June 15 2026: 784 diamond solar panels + 524 mullion edges on a flowing
mountain-ridge roof surface. Grid density of 28×28 gives ~4m panels at 200m scale.

## Organic flowing mountain-ridge rooflines

For non-symmetric organic roofs (not cones/domes), do NOT use `RevSurface.Create()`
(produces UFO/cone shapes). Instead, define multiple profile curves running
across the form, each with hand-crafted peak/valley Z values to create an
asymmetric mountain-ridge silhouette, then loft:

```python
# 7 N-S profiles at different X positions, each with unique ridge shape
profiles_data = [
    (-100, [(-105,2),(-80,8),(-50,14),(0,18),(50,12),(105,2)]),   # west edge: low
    (0,    [(-105,2),(-70,18),(-35,35),(10,50),(35,42),(105,2)]),  # center: main summit
    (100,  [(-105,2),(-80,7),(-50,12),(0,16),(50,10),(105,2)]),    # east edge: low
]
curves = []
for x_m, profile in profiles_data:
    pts = [rg.Point3d(x_m*M, y*M, z*M) for y, z in profile]
    crv = rg.NurbsCurve.Create(False, 3, System.Array[rg.Point3d](pts))
    curves.append(crv)

breps = rg.Brep.CreateFromLoft(System.Array[rg.Curve](curves), ...)
```

Key design principles for mountain-ode rooflines:
- Asymmetric peaks — main summit NOT at center, secondary ridges at different heights
- Valleys between peaks (dips to 60-70% of surrounding peak heights)
- Edge profiles much lower than center (2-3m at edges vs 50m at summit)
- More profile curves = smoother surface (7+ recommended for 200m+ spans)

## Brep.CreateFromLoft — NOT CreateLoftBreps (Rhino 8)

`Brep.CreateLoftBreps()` does NOT exist in Rhino 8 Python API. Use `Brep.CreateFromLoft()` instead. It takes a `List[Curve]` (or `System.Collections.Generic.List[Curve]`) and returns an array of Breps.

```python
from System.Collections.Generic import List

curves = List[Rhino.Geometry.Curve]()
for c in my_curves:
    curves.Add(c)

loft = Rhino.Geometry.Brep.CreateFromLoft(
    curves,
    Rhino.Geometry.Point3d.Unset,  # start point (unused for closed loft)
    Rhino.Geometry.Point3d.Unset,  # end point
    Rhino.Geometry.LoftType.Normal,
    False,  # closed
    False   # reverse normals
)
# loft is an array of Brep[] — iterate and add each
for brep in loft:
    doc.Objects.AddBrep(brep)
```

**Pitfall:** Passing a Python list directly does NOT work — it must be a `System.Collections.Generic.List[Curve]`. Also, the `Rhino.Geometry.LoftType` enum is accessed directly (not as a string).

## RevSurface.Create for surfaces of revolution

`RevSurface.Create(curve, axis_line, start_angle, end_angle)` creates a surface of revolution around an axis defined by a `Line`. For a full 360-degree revolution:

```python
from Rhino.Geometry import Point3d, Curve, Line, RevSurface, Brep
import math

# Profile curve in the XZ plane (X = radius, Z = height)
profile_points = [
    Point3d(0.0, 0, 0.0),    # bottom center (on axis)
    Point3d(4.0, 0, 2.5),    # widest point
    Point3d(0.0, 0, 4.8),    # top center (on axis)
]
curve = Curve.CreateInterpolatedCurve(profile_points, 3)

# Revolve 360 degrees around the Z axis
axis = Line(Point3d(0, 0, 0), Point3d(0, 0, 1))
revolve = RevSurface.Create(curve, axis, 0.0, 2.0 * math.pi)

# Convert to Brep for the document
brep = Brep.CreateFromSurface(revolve)
doc.Objects.AddBrep(brep)
```

**Key points:**
- The axis is a `Line` (not two Point3ds) — use `Line(start, end)`.
- Profile curve points must have Y=0 (in the XZ plane) for revolution around Z.
- Start/end points on the axis (X=0) produce a closed surface.
- `Brep.CreateFromSurface(revolve)` converts the surface to a Brep for `doc.Objects.AddBrep()`.

Proven June 30 2026: Used for the Utah Teapot body and lid (2 surfaces of revolution).

## Always `import System` for typed arrays

`System.Array[rg.Point3d](points_list)` requires `import System` at the top of the script.
Without it, you get `NameError: name 'System' is not defined`. This is easy to forget
since `Rhino` and `Rhino.Geometry` work without it.

**Standard import block for Rhino Python geometry scripts:**
```python
import Rhino
import Rhino.Geometry as rg
import Rhino.DocObjects as rdo
import System
import System.Drawing as sd
import math
doc = __rhino_doc__
```

## LayerTable API pitfalls

- `doc.Layers.LayerCount` does NOT exist — use `doc.Layers.Count` instead.
- `doc.Layers.Purge(0)` does NOT accept arguments — use `doc.Layers.Purge()` or wrap in try/except.
- To count active (non-deleted) layers, iterate and check `not layer.IsDeleted`.

## Clearing all objects — use ObjectEnumeratorSettings

`for obj in doc.Objects` does NOT reliably iterate all objects (may skip hidden/locked).
Use `ObjectEnumeratorSettings` for a complete clear:

```python
settings = rdo.ObjectEnumeratorSettings()
settings.HiddenObjects = True
settings.LockedObjects = True
settings.IncludeLights = True
settings.NormalObjects = True
obj_list = list(doc.Objects.GetObjectList(settings))
for obj in obj_list:
    doc.Objects.Delete(obj.Id, True)
doc.Objects.Purge(0)
```

## Angled/tapered geometry — extrude closed polylines

For non-axis-aligned shapes (e.g. Y-shaped terminal branches at 60° angles),
axis-aligned boxes are a poor approximation. Use trapezoid extrusions:

```python
import math
angle = math.radians(60)
cos_a, sin_a = math.cos(angle), math.sin(angle)
cos_p, sin_p = math.cos(angle + math.pi/2), math.sin(angle + math.pi/2)

# Create trapezoid corner points
p1 = rg.Point3d((r_start*cos_a - w_start*cos_p)*M, (r_start*sin_a - w_start*sin_p)*M, z_top)
p2 = rg.Point3d((r_start*cos_a + w_start*cos_p)*M, (r_start*sin_a + w_start*sin_p)*M, z_top)
p3 = rg.Point3d((r_end*cos_a + w_end*cos_p)*M, (r_end*sin_a + w_end*sin_p)*M, z_top)
p4 = rg.Point3d((r_end*cos_a - w_end*cos_p)*M, (r_end*sin_a - w_end*sin_p)*M, z_top)

# Create closed polyline → extrude → cap
pts = [p1, p2, p3, p4, p1]
crv = rg.Polyline(pts).ToPolylineCurve()
srf = rg.Surface.CreateExtrusion(crv, rg.Vector3d(0, 0, z_bot - z_top))
brep = srf.ToBrep().CapPlanarHoles(1.0)
```

## Layer lookup by full path

`doc.Layers.FindByFullPath()` can return inconsistent results. Prefer
iterating and matching:

```python
def find_layer(full_path):
    for i in range(doc.Layers.Count):
        if doc.Layers[i].FullPath == full_path and not doc.Layers[i].IsDeleted:
            return i
    return -1
```
