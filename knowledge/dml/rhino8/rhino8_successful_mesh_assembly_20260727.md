# Rhino 8 successful single-object mesh assembly

status: SUCCESS_VALIDATED
memory_class: procedural_tool_history
tool: mcp__rhino__run_csharp
argument_shape: {slot: aardvark, script: inline C#}
outcome: one visible Rhino Mesh object assembled from many disconnected box meshes

Validated pattern: resolve `Rhino.RhinoDoc.ActiveDoc`; define the validated `EnsureLayer` and `SB` lambdas; create each box Brep with `Rhino.Geometry.Box(...).ToBrep()`; mesh it with `Rhino.Geometry.Mesh.CreateFromBrep(..., Rhino.Geometry.MeshingParameters.FastRenderMesh)`; append every returned mesh into one `Rhino.Geometry.Mesh`; call `Normals.ComputeNormals()` and `Compact()`; add exactly once via `rdoc.Objects.AddMesh(mesh, attributes)`; reject `System.Guid.Empty`; verify the live object count with `System.Linq.Enumerable.Count(rdoc.Objects.GetObjectList(Rhino.DocObjects.ObjectType.AnyObject))`, object name, and bounding box; redraw only at the end.

Verified result on 2026-07-27: one call created `West_Mullion_Grid` as one visible object; live count changed 18→19; bbox 1.24,-14.535,0.65 to 4.98,2.535,11.20; nested payload.error was null.
