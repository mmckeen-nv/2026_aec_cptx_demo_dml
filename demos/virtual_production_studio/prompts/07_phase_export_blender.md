# Phase 5 - Deterministic Rhino-to-Blender Handoff

## Purpose

Transfer the accepted VP Studio from Rhino to Blender through one tested path:
Rhino mesh companions inside a metadata-bearing `.3dm`, followed by the shared
`rhino3dm` importer. There is no OBJ, FBX, Blender import add-on, or improvised
file parser fallback.

## Fixed paths and tools

Hermes runs from `demos/virtual_production_studio`.

- accepted Rhino output: `rhino/vp_studio_01.3dm`
- importer: `../../skills/import_with_metadata.py`
- validator: `../../skills/validate_blender_scene.py`
- Blender tool: `mcp_blender_execute_blender_code(code=...)`

No tool named `run` exists. Use only the registered Blender MCP tool above.
Never use OBJ, FBX, an import add-on, or a handwritten geometry parser.
Do not probe Blender add-ons or import operators. Do not call `run`,
`bpy.ops.import_scene.*`, `bpy.ops.wm.obj_import`, or parse an OBJ manually.
Never write, patch, regenerate, or replace either importer. The demo-local
`skills/import_with_metadata.py` is only a compatibility shim to the shared
tested implementation. Importer failure is a hard stop, not permission to
invent another parser or probe `rhino3dm` APIs.

## Step 1 - Bake joined Rhino mesh companions

Run this exact code once through `mcp_rhino_run_csharp(script=...)`. It keeps the
accepted Breps, creates one joined mesh companion for each exportable Brep,
copies name/layer/User Text, and rejects any per-axis bounding-box mismatch.
`Mesh.CreateFromBrep` returns an array: never use only `parts[0]`; append every
nonempty part into the joined mesh as shown.

```csharp
var rdoc=doc;
System.Func<string,Rhino.DocObjects.RhinoObject> REQUIRED=(name)=>{foreach(var o in rdoc.Objects){if(o!=null&&o.Attributes.Name==name&&o.Geometry is Rhino.Geometry.Brep)return o;}throw new System.Exception("HANDOFF_REQUIRED_MISSING "+name);};
var ledActive=REQUIRED("LED_ACTIVE_WALL");var ledRear=REQUIRED("LED_REAR_SUPPORT");
var ledActiveBB=ledActive.Geometry.GetBoundingBox(true);var ledRearBB=ledRear.Geometry.GetBoundingBox(true);
if(System.Math.Abs(ledActiveBB.Min.Z)>0.05||System.Math.Abs(ledActiveBB.Max.Z-288)>0.05)throw new System.Exception("HANDOFF_LED_Z_FAIL LED_ACTIVE_WALL minZ="+ledActiveBB.Min.Z+" maxZ="+ledActiveBB.Max.Z);
if(System.Math.Abs(ledRearBB.Min.Z)>0.05||System.Math.Abs(ledRearBB.Max.Z-312)>0.05)throw new System.Exception("HANDOFF_LED_Z_FAIL LED_REAR_SUPPORT minZ="+ledRearBB.Min.Z+" maxZ="+ledRearBB.Max.Z);
var oldIds=new System.Collections.Generic.List<System.Guid>();
foreach(var o in rdoc.Objects){if(o!=null&&o.Geometry is Rhino.Geometry.Mesh&&o.Attributes.GetUserString("handoff_geometry")=="joined_mesh")oldIds.Add(o.Id);}
foreach(var id in oldIds)rdoc.Objects.Delete(id,true);
var settings=new Rhino.DocObjects.ObjectEnumeratorSettings();settings.NormalObjects=true;settings.HiddenObjects=false;
var sources=new System.Collections.Generic.List<Rhino.DocObjects.RhinoObject>();
foreach(var o in rdoc.Objects.GetObjectList(settings)){if(o.Geometry is Rhino.Geometry.Brep&&o.Attributes.GetUserString("export_to_blender")!="false")sources.Add(o);}
int made=0,failed=0;
foreach(var o in sources){
    var brep=(Rhino.Geometry.Brep)o.Geometry;
    var parts=Rhino.Geometry.Mesh.CreateFromBrep(brep,Rhino.Geometry.MeshingParameters.QualityRenderMesh);
    if(parts==null||parts.Length==0){System.Console.WriteLine("MESH_FAIL no_parts "+o.Attributes.Name);failed++;continue;}
    var joined=new Rhino.Geometry.Mesh();
    foreach(var part in parts){if(part!=null&&part.Vertices.Count>0&&part.Faces.Count>0)joined.Append(part);}
    if(joined.Vertices.Count==0||joined.Faces.Count==0){System.Console.WriteLine("MESH_FAIL empty "+o.Attributes.Name);failed++;continue;}
    joined.Normals.ComputeNormals();joined.Compact();
    var a=o.Attributes.Duplicate();a.Name=o.Attributes.Name;a.SetUserString("source_rhino_id",o.Id.ToString());a.SetUserString("handoff_geometry","joined_mesh");
    var bb=brep.GetBoundingBox(true);var mb=joined.GetBoundingBox(true);double tol=0.05;
    bool boundsOk=System.Math.Abs(bb.Min.X-mb.Min.X)<=tol&&System.Math.Abs(bb.Min.Y-mb.Min.Y)<=tol&&System.Math.Abs(bb.Min.Z-mb.Min.Z)<=tol&&System.Math.Abs(bb.Max.X-mb.Max.X)<=tol&&System.Math.Abs(bb.Max.Y-mb.Max.Y)<=tol&&System.Math.Abs(bb.Max.Z-mb.Max.Z)<=tol;
    if(!boundsOk){System.Console.WriteLine("MESH_FAIL bounds "+o.Attributes.Name);failed++;continue;}
    var id=rdoc.Objects.AddMesh(joined,a);if(id==System.Guid.Empty){System.Console.WriteLine("MESH_FAIL add "+o.Attributes.Name);failed++;continue;}made++;
}
rdoc.Views.Redraw();
if(failed>0||made!=sources.Count)throw new System.Exception("HANDOFF_MESH_FAIL sources="+sources.Count+" made="+made+" failed="+failed);
System.Console.WriteLine("HANDOFF_MESH_PASS sources="+sources.Count+" made="+made+" failed=0 LED_Z_PASS");
```

Only `HANDOFF_MESH_PASS` advances. Save noninteractively with
`mcp_rhino_save_doc` to the exact `rhino/vp_studio_01.3dm` path.

## Step 2 - Run the checked-in importer exactly

Remain in the launcher-owned generic Blender scene. Existing `.blend` files are
outputs or legacy debris, never inputs. Do not call `bpy.ops.wm.open_mainfile`,
append/link another `.blend`, or inspect multiple scene files to choose one.

First call `mcp_blender_get_scene_info`. Then send this exact bootstrap through
`mcp_blender_execute_blender_code(code=...)`:

```python
import os, importlib.util
root = os.environ["AEC_DEMO_ROOT"]
skill = os.path.join(root, "skills", "blender_vp_production.py")
if not os.path.isfile(skill): raise RuntimeError("missing production helper: " + skill)
spec = importlib.util.spec_from_file_location("vp_production", skill)
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)
result = vp.import_current_handoff(root, reset_scene=True)
print("VP_HANDOFF_READY " + repr(result))
```

`import_current_handoff` deliberately clears the generic or stale scene before
importing. Do not preserve default cubes, previous cameras, materials, lights,
assets, or any old `VP_STUDIO_RHINO` collection. Do not reuse an existing `VP_STUDIO_RHINO` collection, even if it appears
populated. The importer stamps the exact path, size, modification time, and
SHA-256 of this run's `rhino/vp_studio_01.3dm`; production helpers reject any
collection whose stamp differs. Internally the helper calls
`import_3dm(..., root_name="VP_STUDIO_RHINO", replace_existing=True)`, then
`assert_import_matches_source(...)`, and emits `VP_HANDOFF_PASS`. Do not rewrite the importer. The tested importer replaces only the named
`VP_STUDIO_RHINO` collection, so a partial earlier attempt cannot poison retry.

## Step 3 - Validate before visual work

Load `../../skills/validate_blender_scene.py` with the same `importlib` pattern,
call `validate(require_material_slots=False, strict_coplanar=False)`, and require
a true result. Coplanar architectural contacts remain reported as diagnostics;
they do not fail the handoff by count alone. Compare
imported object names, metadata, metre-scale per-axis bounds, and object count
against the Rhino handoff mesh companions. Counts alone do not pass.

Capture a Blender viewport screenshot and confirm the building is upright:
Rhino `(X,Y,Z)` maps directly to Blender `(X,Y,Z)`. There is no Y/Z swap and no
90-degree corrective rotation.

## Step 4 - Production scene

After the handoff passes:

1. Read `03_asset_sourcing_contract.md`, `assets/asset_manifest.yaml`, and
   `assets/cache/cache_index.json`.
2. Load `<AEC_DEMO_ROOT>/skills/blender_vp_production.py` and call
   `apply_required_set_dressing(root)` exactly once. Require
   `VP_SET_DRESSING_PASS categories=6 placements=27`. This batch supplies three
   production cameras, eight chairs, six workstation monitors, six road cases,
   two complete LED soft-panel practicals, and two server racks. A standalone
   bare C-stand is prohibited. Do not selectively skip categories or retain
   visible proxy boxes.
3. Call
   `prepare_production_look()` exactly once. Require `VP_MATERIAL_PASS` and
   `VP_LIGHTING_PASS`; its fixed rig supplies LED contribution,
   key, fill, rim/backlight, stage softbox, and restrained world light. Do not invent
   material or lighting scripts.
4. Call `setup_beauty_camera()` and `render_preview()` exactly as specified in
   `03_asset_sourcing_contract.md`. Require verified camera alignment and
   `VP_RENDER_PASS`. The helper uses the unobstructed `stage_wide` presentation
   angle; do not substitute CAM_E/CAM_F or handwritten camera transforms.
5. Capture and inspect the stage-wide hero render. Visible proxy boxes, flat gray
   shading, broken LED curvature, an empty stage, a bare C-stand, or missing
   cameras/furniture/road cases/practical fixtures are defects.
6. Treat the passing hero as the approved
   ComfyUI source render.
7. Run `validate(require_material_slots=True, strict_coplanar=False)` and save
   the `.blend` checkpoint.

## Hard failure rules

- OBJ and FBX are prohibited.
- Blender add-on probing is prohibited.
- Handwritten vertex/face file parsers are prohibited.
- A Blender bridge disconnect is a blocker; do not continue issuing calls until
  the launcher-owned bridge is available again.
- Never return to Rhino to invent a different export format. Repair only the
  mesh-companion step or the shared importer based on concrete evidence.

## Checkpoint

Save only by loading `../../skills/blender_vp_production.py` and calling
`save_production_checkpoint(root)`. It refuses to save unless the
`VP_STUDIO_RHINO` collection contains real mesh objects and always writes
`blender_assets/vp_studio_01.blend`; do not overwrite the legacy
`G:\AEC-CPTX\demos\virtual_production_studio\vp_studio_01_scene.blend` file.
Never open `blender_assets/vp_studio_01.blend` at phase start and never call a
Blender save operator directly. It is output-only and may be replaced only by
`save_production_checkpoint` after validation.
Then proceed to
`04_comfyui_stylization_contract.md` using the approved hero render.

`VP_HANDOFF_PASS` permanently closes Rhino for this run. From that receipt
forward, every `mcp_rhino_*` call is invalid. Do not use Rhino to inspect,
launch, proxy, or operate Blender or ComfyUI.
