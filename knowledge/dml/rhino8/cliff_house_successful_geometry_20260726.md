# Cliff House Rhino 8 successful geometry call — 2026-07-26

status: SUCCESS_VALIDATED
memory_class: procedural_tool_history
tool: mcp__rhino__run_csharp
argument_shape: {"slot":"aardvark","script":"<inline C#>"}

Validated scaffold details:
- Resolve `var rdoc = Rhino.RhinoDoc.ActiveDoc;` and null-check.
- Use `LayerTable.FindByFullPath(fullPath, -1)`; the older boolean overload is obsolete and warnings compile as errors on this router.
- Ensure nested layers with `new Rhino.DocObjects.Layer()`, `Name`, `ParentLayerId`, and `rdoc.Layers.Add(layer)`.
- Solid helper signature: `System.Func<string,int,double,double,double,double,double,double,System.Guid> SB` and add with `rdoc.Objects.AddBrep(box.ToBrep(), attr)`.
- Verify every returned Guid against `System.Guid.Empty`.
- Count `GetObjectList(...)` with `foreach`; it returns `IEnumerable<RhinoObject>`, not an array with `.Length`.
- Pause using `System.Threading.Thread.Sleep(200)` inside the one-object call.
- Print created count/name/layer/Guid/bounding box and call `rdoc.Views.Redraw()` only at the end.

Verified result:
`created=1 name=terrain guid=2ead5bbd-2977-4568-95fd-3fd6a3c0eb3c layer=building_site_v3::terrain total=17 bbox=-15,-22,-8 -> 25,20,0`; nested `payload.error=null`. Independent `mcp__rhino__list_objects` verification returned exactly one Brep named `terrain` on `building_site_v3::terrain`.

Excluded failed attempt:
Do not use `FindByFullPath(path, true)` or `.Length` on `GetObjectList(...)` in this environment.

## Connected multi-box assembly as one visible Brep

tool: mcp__rhino__run_csharp
argument_shape: {"slot":"aardvark","script":"<C# string>"}
validated_scaffold: create each connected box as `new Rhino.Geometry.Box(...).ToBrep()`, collect Breps, call `Rhino.Geometry.Brep.CreateBooleanUnion(parts, rdoc.ModelAbsoluteTolerance)`, require `u != null && u.Length == 1`, then add only `u[0]` with `rdoc.Objects.AddBrep`; verify Guid, sleep 200 ms, print bbox/count, redraw once.
verified_result: `Mullions_West_L1` added as exactly one visible Brep on `detail_v3::frames`; UUID `ad3c7ef8-fc16-4a19-8306-1952f0b837ab`; bounds `(5.11,-15.12,0.61)` to `(13.39,-15.06,3.84)`; scene object count increased from 34 to 35; `payload.error=null`; `mcp__rhino__list_objects` independently returned count 1, correct layer and Brep type.
