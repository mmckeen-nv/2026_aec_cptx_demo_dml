# Rhino 8 MCP known-good C# patterns

Use the registered tools exactly:

- `mcp_rhino_run_csharp(script=...)`
- `mcp_rhino_list_objects(...)`
- `mcp_rhino_get_viewport_image(...)`
- `mcp_rhino_save_doc(...)`

Never call slot spawn/close, document close/reopen, or interactive command
macros from the demo.

## Geometry mutation rule

Use C# for every geometry mutation. The current phase prompt contains a complete
phase-local scaffold derived from the original Cliff House prompts. Copy it;
do not translate it into Python and do not probe APIs first.

Every scaffold uses these tested primitives:

```csharp
var rdoc = doc;
System.Func<string,int,double,double,double,double,double,double,System.Guid> SB =
    (name,layerIndex,x0,x1,y0,y1,z0,z1) => {
        var box = new Rhino.Geometry.Box(Rhino.Geometry.Plane.WorldXY,
            new Rhino.Geometry.Interval(x0,x1),
            new Rhino.Geometry.Interval(y0,y1),
            new Rhino.Geometry.Interval(z0,z1));
        var attr = new Rhino.DocObjects.ObjectAttributes();
        attr.Name = name; attr.LayerIndex = layerIndex;
        var id = rdoc.Objects.AddBrep(box.ToBrep(), attr);
        if (id == System.Guid.Empty) throw new System.Exception("add failed: "+name);
        return id;
    };
```

Layer creation always constructs a `Rhino.DocObjects.Layer` and passes that
object to `rdoc.Layers.Add(layer)`. Geometry-add methods return `Guid`; never use
that result as an ObjectTable integer index.

## Python is read-only

The MCP router can report a successful tool transport even when a read-only script
stdout contains a Python traceback. A traceback is a failed script. Correct the
single bad API and retry once; do not count it as completed modeling.

```python
import Rhino
import scriptcontext

doc = scriptcontext.doc
print("units={}".format(doc.ModelUnitSystem))

# ObjectTable is enumerable; do not access it with doc.Objects[i].
objects = [obj for obj in doc.Objects if obj is not None]
print("objects={}".format(len(objects)))
```

Never use `doc.ModelUnits`, `from Rhino import doc`, integer indexing into
`doc.Objects`, or `doc.Layers.FindByName(...)`; none is valid in this Rhino 8
Python environment.

Use this deliberately boring layer helper. It avoids binding-specific lookup
overloads:

```python
def ensure_top_level_layer(doc, name, color):
    for layer in doc.Layers:
        if layer is not None and not layer.IsDeleted and layer.Name == name:
            return layer.Index
    layer = Rhino.DocObjects.Layer()
    layer.Name = name
    layer.Color = color
    index = doc.Layers.Add(layer)
    if index < 0:
        raise RuntimeError("failed to add layer: " + name)
    return index
```

## Locked units and coordinates

Read `../prompts/01a_locked_scene_manifest.md` before geometry. VP Studio 01 is
always modeled in inches at world datum `(0,0,0)`. Use only absolute scheduled
coordinates. Do not create a phase-local origin or convert the manifest to
meters. Print every new object's world bounding box and compare it to the
manifest envelope before vision review.

## Metadata

Use `Rhino.DocObjects.ObjectAttributes`, set `Name` and `LayerIndex`, and call:

```csharp
attr.SetUserString("project", "vp-studio-01");
attr.SetUserString("phase", "SCHEMATIC");
attr.SetUserString("export_to_blender", "yes");
```

There is no writable `Attributes.UserText` property.

## Smooth curved LED face

Create a true `Rhino.Geometry.ArcCurve` and closed annular profile, then create
one vertical extrusion. Do not approximate the finished face with box segments.
The arc points must use the scheduled LED center `(-120,0,0)`, not the world
origin. Copy the current phase's tested C# delegates; the core coordinate rule is:

```csharp
var east  = new Rhino.Geometry.Point3d(cx + radius, cy, 0);
var north = new Rhino.Geometry.Point3d(cx, cy + radius, 0);
var west  = new Rhino.Geometry.Point3d(cx - radius, cy, 0);
var arc = new Rhino.Geometry.ArcCurve(new Rhino.Geometry.Arc(east,north,west));
```

Validate the 480 in radius, 288 in height, and X -692..452 / Y 0..572 maximum
assembly envelope after creation.

## View capture

After `NUMERIC_PASS`, call `mcp_rhino_get_viewport_image` once and route that
fresh image to local Nemotron vision. If a local PNG is required, capture it
with a small inline `mcp_rhino_run_python` script using
`ActiveView.CaptureToBitmap`; never open or replay an external `.py` file. Do
not analyze an older similarly named image.

## Failure rule

If a mutation result contains an exception, change the failing API or arguments
before retrying. Do not rewrite an entire phase script, and do not repeat an
unchanged call.
