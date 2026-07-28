# Rhino 8 MCP geometry contract

status: SUCCESS_VALIDATED
scope: Rhino 8, Rhino-MCP-Platform 0.1.5, agent-authored geometry
retrieval_tags: Rhino 8 MCP geometry creation validated API contract C# run_csharp

For geometry creation or modification, use
`mcp__rhino__run_csharp(script=...)`. Do not translate the operation to Python
and do not probe guessed Python overloads. Python through
`mcp__rhino__run_python` is reserved for read-only inspection and viewport
capture.

The tool argument key must be `script`, not `code`. A `code` argument reaches
the router as an invalid invocation and returns only the generic error
`An error occurred invoking 'run_csharp'`.

Use this known-good solid-box primitive:

```csharp
var rdoc = Rhino.RhinoDoc.ActiveDoc;
if (rdoc == null)
    throw new System.Exception("No active Rhino document");
System.Func<string,int,double,double,double,double,double,double,System.Guid> SB =
    (name,layerIndex,x0,x1,y0,y1,z0,z1) => {
        var box = new Rhino.Geometry.Box(
            Rhino.Geometry.Plane.WorldXY,
            new Rhino.Geometry.Interval(x0,x1),
            new Rhino.Geometry.Interval(y0,y1),
            new Rhino.Geometry.Interval(z0,z1));
        var attr = new Rhino.DocObjects.ObjectAttributes();
        attr.Name = name;
        attr.LayerIndex = layerIndex;
        var id = rdoc.Objects.AddBrep(box.ToBrep(), attr);
        if (id == System.Guid.Empty)
            throw new System.Exception("add failed: " + name);
        return id;
    };
```

Layer creation must construct a `Rhino.DocObjects.Layer`, then pass that object
to `rdoc.Layers.Add(layer)`. The router does not inject a `doc` variable; every
script must resolve and null-check `Rhino.RhinoDoc.ActiveDoc` as shown above:

```csharp
System.Func<string,System.Drawing.Color,int> EnsureLayer = (name,color) => {
    var existing = rdoc.Layers.FindName(name);
    if (existing != null) return existing.Index;
    var layer = new Rhino.DocObjects.Layer();
    layer.Name = name;
    layer.Color = color;
    var index = rdoc.Layers.Add(layer);
    if (index < 0) throw new System.Exception("layer add failed: " + name);
    return index;
};
```

For a child layer, set `ParentLayerId` to the parent layer's `Id` before
calling `rdoc.Layers.Add(layer)`. Prepare `ObjectAttributes` before the
applicable `rdoc.Objects.Add*` call. Geometry-add methods return `Guid`; never
use that result as an ObjectTable integer index.

Every mutation script must:

1. Use absolute WorldXY coordinates and the active document's model units.
2. Create or resolve layers before adding geometry.
3. Test every returned `Guid` against `System.Guid.Empty`.
4. Print a compact creation count and the world bounding-box envelope.
5. Call `rdoc.Views.Redraw()` only after the mutation is complete.

Never call `spawn_slot`, `close_slot`, `close_doc`, or reopen the document.

Failure policy: inspect the returned `payload.error` even when MCP transport
reports success. Any non-empty `payload.error`, exception, or traceback means
the script failed. Correct the single failing API once; do not submit a larger
rewrite or repeat an unchanged call.

Provenance:

- Existing validated repository patterns:
  `demos/virtual_production_studio/skills/rhino_mcp_patterns.md`
- McNeel RhinoCommon guide:
  https://developer.rhino3d.com/guides/rhinocommon/
- McNeel guide to RhinoCommon from Python:
  https://developer.rhino3d.com/guides/rhinopython/using-rhinocommon-from-python/
