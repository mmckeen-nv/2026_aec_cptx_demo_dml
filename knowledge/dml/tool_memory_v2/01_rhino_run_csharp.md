# Verified Rhino MCP mutation call

status: SUCCESS_VALIDATED
memory_class: procedural_tool_call
retrieval_tags: successful Rhino geometry tool call exact tool argument scaffold
memory_summary: SUCCESS: call mcp__rhino__run_csharp with {"slot":"aardvark","script":"<inline C#>"}. Use argument `script`, never `code`; resolve and null-check Rhino.RhinoDoc.ActiveDoc. Batch a complete phase per call, reject empty GUIDs/nested payload.error, return compact names/counts/bounds PASS JSON, redraw once; one QA and at most one repair.

Use `mcp__rhino__run_csharp` with:

```json
{"slot":"aardvark","script":"<inline C#>"}
```

The argument is `script`, never `code`. The script must resolve
`Rhino.RhinoDoc.ActiveDoc`; no `doc` variable is injected.

```csharp
var doc = Rhino.RhinoDoc.ActiveDoc;
if (doc == null) throw new System.Exception("No active Rhino document");
System.Func<string,int,double,double,double,double,double,double,System.Guid> AddBox =
 (name,layer,x0,x1,y0,y1,z0,z1) => {
   var box = new Rhino.Geometry.Box(
     Rhino.Geometry.Plane.WorldXY,
     new Rhino.Geometry.Interval(x0,x1),
     new Rhino.Geometry.Interval(y0,y1),
     new Rhino.Geometry.Interval(z0,z1));
   var a = new Rhino.DocObjects.ObjectAttributes {
     Name = name, LayerIndex = layer
   };
   var id = doc.Objects.AddBrep(box.ToBrep(), a);
   if (id == System.Guid.Empty) throw new System.Exception("add failed: "+name);
   return id;
 };
// Create the complete phase batch, validate names/counts/bounds, then:
doc.Views.Redraw();
System.Console.WriteLine("{\"status\":\"PASS\"}");
```

Success means transport `IsError=False`, nested `payload.error` is empty, every
GUID is non-empty, and the returned compact manifest proves expected
names/counts/bounds. Batch a complete phase per call; do not call once per
object. Perform one consolidated read-only QA call and at most one repair call.
