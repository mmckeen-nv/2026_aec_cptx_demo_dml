# Rhino C# Scripting Pitfalls (mcp_rhino_run_csharp)

Compile-time errors encountered when using `mcp_rhino_run_csharp` for geometry creation. Each was discovered through trial-and-error during VP studio construction (June 30, 2026). All confirmed on Rhino 8 with the Rhino MCP router.

## 1. `return` with value fails — use Console.WriteLine

The Rhino MCP C# script runner expects `void` return type. Using `return someString;` produces:

```
Error CS0127: Since '__RunScript__' returns void, a return keyword must not be followed by an object expression
```

**Fix:** Replace all `return result;` with `Console.WriteLine(result);`. The stdout is captured in the `stdout` field of the response JSON.

## 2. `PlaneSurface.CreateThroughPlane` does not exist

```csharp
// FAILS: Compile Error CS0117
var surf = Rhino.Geometry.PlaneSurface.CreateThroughPlane(plane, xDim, yDim);
```

**Fix:** Use `NurbsSurface.CreateFromCorners` for flat quad surfaces:
```csharp
var surf = Rhino.Geometry.NurbsSurface.CreateFromCorners(p1, p2, p3, p4);
```

## 3. Bare `Math` is not available — use `System.Math`

The C# script context does not import `System` statically. Bare `Math.Cos()`, `Math.PI`, etc. produce:

```
Error CS0103: The name 'Math' does not exist in the current context
```

**Fix:** Always use `System.Math.Cos()`, `System.Math.PI`, `System.Math.Sin()`, etc.

## 4. `Rhino.Geometry.Arc` has no 7-argument constructor

The Arc struct in Rhino 8 does not accept `(plane, interval, rx, ry, startAngle, endAngle, orientation)`.

**Fix:** Don't use the Arc constructor for curved geometry. Instead, compute points along the arc manually and use `Curve.CreateInterpolatedCurve`:

```csharp
var arcPoints = new List<Rhino.Geometry.Point3d>();
for (int i = 0; i <= numPts; i++)
{
    double angle = startAngle - (double)i / numPts * sweepAngle;
    double x = cx + rx * System.Math.Cos(angle);
    double y = cy + ry * System.Math.Sin(angle);
    arcPoints.Add(new Rhino.Geometry.Point3d(x, y, zBot));
}
var arcCurve = Rhino.Geometry.Curve.CreateInterpolatedCurve(arcPoints, 3);
```

Then extrude with `Surface.CreateExtrusion(curve, direction)`.

## 5. `AnnotationBase.Text` is obsolete — use AddText overload

Setting `TextEntity.Text` directly triggers a deprecation warning that blocks compilation:

```
Warning CS0618: 'AnnotationBase.Text' is obsolete: 'Use RichText or PlainText'
```

**Fix:** Use `doc.Objects.AddText` with the string-based overload:
```csharp
var plane = new Rhino.Geometry.Plane(center, Vector3d.XAxis, Vector3d.YAxis);
doc.Objects.AddText(labelText, plane, textHeight, "Arial", false, false, attributes);
```

## 6. Box.ToBrep() for solid geometry

For wall/slab/roof volumes, `Rhino.Geometry.Box` + `.ToBrep()` is the most reliable pattern:
```csharp
var box = new Rhino.Geometry.Box(new Rhino.Geometry.BoundingBox(minPt, maxPt));
doc.Objects.AddBrep(box.ToBrep(), attr);
```

## 7. Surface.CreateExtrusion for curved walls

For extruding a curve along a direction (e.g., curved LED wall extruded upward):
```csharp
var wall = Rhino.Geometry.Surface.CreateExtrusion(curve, new Rhino.Geometry.Vector3d(0, 0, height));
doc.Objects.AddBrep(wall.ToBrep(), attr);
```

## 8. Layer lookup pattern

Layers don't have stable indices across sessions. Always look up by name:
```csharp
int layerIdx = -1;
for (int i = 0; i < doc.Layers.Count; i++)
    if (doc.Layers[i].FullPath == "Stage::Walls") { layerIdx = i; break; }
```

## 9. C# tuple syntax with `for` loops

Tuples in `foreach` work fine, but be careful with `break` placement inside `for` loops when using tuples — a stray `break` in a lookup `for` loop will exit prematurely. This is standard C# but easy to fat-finger when writing long scripts.

## 10. `FindByFilter` does not take 2 arguments

```csharp
// FAILS: Error CS1501 — No overload takes 2 arguments
var allObjects = doc.Objects.FindByFilter(Rhino.DocObjects.ObjectType.AnyObject, null);
```

**Fix:** Use `doc.Objects.FindByFilter(ObjectType.AnyObject)` (1 arg, no null) or iterate `doc.Objects.GetObjectList(ObjectType.AnyObject)`.

## 11. `MeshingParameters` has no 4-argument constructor

```csharp
// FAILS: Error CS1729
var mp = new Rhino.Geometry.MeshingParameters(0.01, 0.01, 0.1, 0.1);
```

**Fix:** Use `MeshingParameters.Default` or the parameterless constructor, then set properties individually:
```csharp
var mp = new Rhino.Geometry.MeshingParameters();
mp.MinimumEdgeLength = 0.01;
mp.MaximumEdgeLength = 0.1;
```
Or simply use `Rhino.Geometry.MeshingParameters.Default` for most cases.

## 12. `Mesh.ComputeNormals()` does not exist as a method

The method is `mesh.Normals.ComputeNormals()` (on the `MeshNgonList`/`MeshNormalsList`), not `mesh.ComputeNormals()`.

**Fix:** Use `mesh.Normals.ComputeNormals()` or skip normals entirely — the OBJ exporter and viewport can compute normals automatically.

## 13. `Rhino.Geometry.Pipe` does not exist

```csharp
// FAILS: Error CS0234 — 'Pipe' does not exist in 'Rhino.Geometry'
var pipeSegs = Rhino.Geometry.Pipe.Create(curve, 0.04, 0.04, true);
```

**Fix:** Use `Cylinder` + `Circle` + `ToBrep(true, true)` for cylindrical geometry (tripod legs, posts, pipes, lenses). See item 14 below.

## 14. Cylinder construction pattern (proven June 30 2026)

The reliable way to create capped cylindrical geometry. Used for tripod legs, vertical posts, camera lenses, wheel axles, and any tubular structure:

```csharp
// Create a cylinder from point A to point B with given radius
var start = new Rhino.Geometry.Point3d(x1, y1, z1);
var end = new Rhino.Geometry.Point3d(x2, y2, z2);
var mid = (start + end) / 2;
var dir = end - start;
var plane = new Rhino.Geometry.Plane(mid, dir);  // plane normal = direction
var cyl = new Rhino.Geometry.Cylinder(
    new Rhino.Geometry.Circle(plane, radius),
    dir.Length  // full length
);
doc.Objects.AddBrep(cyl.ToBrep(true, true), attr);  // true, true = cap both ends
```

**Key details:**
- The `Plane` constructor takes `(centerPoint, normalVector)` — the normal defines the cylinder axis
- `Circle(plane, radius)` creates the base circle on that plane
- `Cylinder(circle, length)` creates the cylinder — `length` is the FULL height, not half
- `ToBrep(true, true)` caps both ends — without caps, you get an open tube
- For vertical cylinders, use `new Rhino.Geometry.Plane(center, Rhino.Geometry.Vector3d.ZAxis)`

## 15. Sphere construction pattern (proven June 30 2026)

```csharp
var sphere = new Rhino.Geometry.Sphere(
    new Rhino.Geometry.Point3d(x, y, z), radius);
doc.Objects.AddBrep(sphere.ToBrep(), attr);
```

Used for light bulbs, ball joints, and other spherical details. Simpler than cylinder — just center + radius.

## 16. `Rhino.Geometry.Line` constructor does not take 3 arguments

```csharp
// FAILS: Error CS1729 — No constructor takes 3 arguments
var line = new Rhino.Geometry.Line(p1, p2, 0.06);  // trying to specify thickness
```

**Fix:** `Line` is just a geometric line (two points). For a thick line/pipe, use the `Cylinder` pattern (item 14) or `Box` pattern (item 6) instead.
