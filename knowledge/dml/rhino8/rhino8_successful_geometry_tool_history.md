# Prior successful Rhino geometry tool call

status: SUCCESS_VALIDATED
memory_class: procedural_tool_history
tool: mcp__rhino__run_csharp
outcome: geometry_created_and_verified
retrieval_tags: have I made geometry tool calls before how did I do that exact successful call

Question this memory answers:

`Have I made successful Rhino geometry tool calls before? How exactly did I do
that? Return the tool name, argument shape, validated script scaffold, and
success evidence. Exclude failed attempts.`

Yes. The successful mutation path used
`mcp__rhino__run_csharp` with one argument named `script`. It did not use
`mcp__rhino__run_python`.

Canonical successful argument shape:

```text
tool: mcp__rhino__run_csharp
arguments:
  slot: aardvark
  script: <inline C# that resolves `Rhino.RhinoDoc.ActiveDoc` itself>
```

The argument key is literally `script`. Do not substitute `code`. On this
router, sending the C# body under `code` returns the generic failure
`An error occurred invoking 'run_csharp'` before the script can run.

Canonical validated solid creation scaffold:

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

Success evidence required after the call:

- no nested `payload.error`, exception, or traceback;
- returned `Guid` is not `System.Guid.Empty`;
- object count increases by the expected amount;
- created object names and world bounding boxes match the requested manifest;
- the active document remains open and the adopted Rhino slot is unchanged.

Known failed paths to exclude from recall:

- sending the C# body under an argument named `code` instead of `script`;
- assuming that `doc` or `rdoc` is injected into the C# script;
- Python geometry mutation through `mcp__rhino__run_python`;
- `rs.AddBox(center, width, depth, height)`;
- guessed `LayerTable.Add` overloads;
- `Rhino.DocObjects.ConcreteObject`;
- constructing `Rhino.Geometry.Box` with another `Box` as an interval;
- retrying a call whose nested `payload.error` is non-empty.

Source provenance: live-validated repository scaffolds in
`demos/virtual_production_studio/skills/rhino_mcp_patterns.md` and the current
AEC numbered phase prompts.
