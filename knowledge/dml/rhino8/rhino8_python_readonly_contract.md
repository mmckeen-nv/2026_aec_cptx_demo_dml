# Rhino 8 MCP Python read-only contract

status: SUCCESS_VALIDATED
scope: Rhino 8, Rhino-MCP-Platform 0.1.5, inspection and viewport capture
retrieval_tags: Rhino Python MCP read only inspection payload error traceback

Use `mcp__rhino__run_python` only for inspection and capture. Geometry
mutation belongs in the validated C# scaffold from the Rhino 8 MCP geometry
contract.

Known-good inspection:

```python
import Rhino

doc = __rhino_doc__
objects = [obj for obj in doc.Objects if obj is not None]
print("units={}".format(doc.ModelUnitSystem))
print("objects={}".format(len(objects)))
for obj in objects[:20]:
    bbox = obj.Geometry.GetBoundingBox(True)
    print("{} {} {} -> {}".format(
        obj.Id, obj.Attributes.Name, bbox.Min, bbox.Max))
```

Known-good layer lookup is iteration, or
`doc.Layers.FindByFullPath(path, True)`. `FindByFullPath` returns an integer
index; `-1` means absent. Do not access `.Index` on its result.

Avoid these invalid patterns:

- `rhinoscriptsyntax.LayerIndex`
- `rhinoscriptsyntax.ObjectAttributes`
- `doc.ModelUnits`
- `from Rhino import doc`
- integer indexing such as `doc.Objects[i]`
- guessed `LayerTable.Add` overloads
- `rs.AddBox(center, width, depth, height)`

RhinoScriptSyntax `AddBox` accepts eight corner points, not a center and three
dimensions. `AddCylinder` accepts `(base, height, radius, cap=True)`. For
reliable agent-authored solids, prefer the validated RhinoCommon C# scaffold
instead of these convenience functions.

Known-good active-view capture:

```python
import System

doc = __rhino_doc__
view = doc.Views.ActiveView
bitmap = view.CaptureToBitmap(System.Drawing.Size(960, 540))
image_path = r"C:\absolute\path\rhino_view.png"
bitmap.Save(image_path)
print(image_path)
```

Transport success does not prove script success. Parse the nested result and
treat any non-empty `payload.error`, Python exception, or traceback as a
failed tool call.

Provenance:

- McNeel Rhino.Python documentation:
  https://developer.rhino3d.com/guides/rhinopython/
- McNeel RhinoScriptSyntax API:
  https://developer.rhino3d.com/api/rhinoscriptsyntax/
- Existing live-validated repository recipe:
  `demos/virtual_production_studio/knowledge/dml/rhino8_mcp_015_call_recipe.md`
