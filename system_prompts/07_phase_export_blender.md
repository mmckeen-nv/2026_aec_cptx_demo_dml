# Phase 6 — Export to Blender
### Export Execution Prompt
*Part of the Hermes AEC Demo prompt suite*
*Reads: `06_detailing_prompt.md` (Phase 5 complete), `[project]/user_prompts/project_prompt.md` § Section 8*
*Version 2.0 — May 2026*

---

## Purpose

Transfer all Rhino geometry to Blender with full material metadata intact.
This is the critical handoff phase. The material tags set here flow through
every subsequent phase — Cycles assignment, render passes, and ComfyUI prompts.
There has been significant trial and error establishing this procedure.
Follow every step exactly.

---

## Inputs

- `[project]/rhino_assets/base_model.3dm` — Phase 5 complete, display materials assigned
- `[project]/user_prompts/project_prompt.md` § Section 8 — approved material tag list
- `skills/pre_export_validate.py` — Rhino-side pre-export gate
- `skills/import_with_metadata.py` — Blender-side import script
- `skills/validate_blender_scene.py` — Blender-side post-import gate

## Outputs

- `[project]/rhino_assets/base_model_phase6_snapshot_YYYYMMDD_HHmm.3dm` — tagged snapshot
- `[project]/blender_assets/base_model.blend` — imported scene, custom properties set
- `[project]/blender_assets/base_model_checkpoint_YYYYMMDD_HHMM.blend`

---

## Pre-Phase Audit Checklist

- [ ] Phase 5 gate approved — detailing complete and display materials assigned
- [ ] Section 8 of `project_prompt.md` has the approved material tag list
- [ ] Rhino document is open with Phase 5 geometry
- [ ] Blender is open (empty or existing base scene)
- [ ] BlenderMCP running on port 9876 (Scripting tab → `bpy.ops.blendermcp.start_server()`)
- [ ] `skills/import_with_metadata.py` exists at `C:\Users\swags\Documents\the project root\skills\`
- [ ] `skills/pre_export_validate.py` exists at same location

---

## OBS Recording Protocol

→ **TRAY:** Update `current_stage.json` with current phase. Announce: "Starting phase — click Record in the tray when ready."
Confirm: "Recording started — `06-export_blender-hermes`."

Hermes explains the export sequence and material tag strategy on screen.

→ **TRAY:** Announce: "Switching to Rhino — click Record Rhino in the tray when ready."

→ **TRAY:** Announce: "Switching to Blender — click Record Blender in the tray when ready."

→ **TRAY:** Announce: "Switching back to Hermes."

---

## Execution Steps

### Step 1 — Confirm material tag list from Section 8

Read `[project]/user_prompts/project_prompt.md` Section 8 and extract the
approved material tag names. These are the canonical tag strings that will be
written to every object in Rhino and read back in Blender.

Example tag names (adapt from Section 8 for each project):
```
M_Concrete_WarmBone        ← exterior walls, roof slab, terrace pad
M_Glass_TintedBronze       ← all glazing panels
M_Aluminum_Bronze          ← mullions, window frames
M_Stone_Fieldstone         ← retaining walls
M_Wood_DarkCedar           ← entry recess lining
M_Concrete_Pool            ← pool lining / coping
M_Steel_EdgeTrim           ← slab edge blade detail
M_Terrain_DesertCoastal    ← terrain surface
M_Granite_DG               ← decomposed granite driveway / ground
```

Confirm with user if any tag name is ambiguous before tagging.

### Step 2 — Run pre_export_validate.py in Rhino

Run `skills/pre_export_validate.py` via RhinoMCP. This script checks:
- All Breps are solid (IsSolid = True)
- No coplanar faces (z-fighting)
- All objects on correct named layers
- Units are metres, scale is correct
- No stray geometry at world origin

**Do NOT proceed if this script reports critical failures.**
Fix all reported issues first, then re-run until clean.

### Step 3 — Tag all objects with material User Text

Run the following in Rhino via RhinoMCP. This is the bridge between
Rhino display materials and Blender Cycles materials.

```csharp
var rdoc = Rhino.RhinoDoc.ActiveDoc;
var sb = new System.Text.StringBuilder();
int tagged = 0, skipped = 0;

// Layer-to-material-tag mapping (adapt from Section 8)
// Key = layer full path (or keyword), Value = canonical tag name
var layerMaterials = new System.Collections.Generic.Dictionary<string,string> {
    { "walls",          "M_Concrete_WarmBone" },
    { "roof",           "M_Concrete_WarmBone" },
    { "floor",          "M_Concrete_WarmBone" },
    { "glass",          "M_Glass_TintedBronze" },
    { "mullion",        "M_Aluminum_Bronze" },
    { "retaining",      "M_Stone_Fieldstone" },
    { "terrain",        "M_Terrain_DesertCoastal" },
    { "driveway",       "M_Granite_DG" },
    { "pool",           "M_Concrete_Pool" },
    { "entry",          "M_Wood_DarkCedar" },
    // add all Section 8 tags here
};

var es = new Rhino.DocObjects.ObjectEnumeratorSettings {
    NormalObjects = true, HiddenObjects = false };

foreach (var o in rdoc.Objects.GetObjectList(es)) {
    if (!(o.Geometry is Rhino.Geometry.Brep ||
          o.Geometry is Rhino.Geometry.Mesh)) { skipped++; continue; }

    string matName = "";

    // Priority 1: explicit Rhino display material name
    if (o.Attributes.MaterialSource ==
        Rhino.DocObjects.ObjectMaterialSource.MaterialFromObject) {
        int mi = o.Attributes.MaterialIndex;
        if (mi >= 0 && mi < rdoc.Materials.Count)
            matName = rdoc.Materials[mi].Name ?? "";
    }

    // Priority 2: infer from layer path keywords
    if (string.IsNullOrEmpty(matName)) {
        string fp = rdoc.Layers[o.Attributes.LayerIndex]?.FullPath ?? "";
        string fpLo = fp.ToLower();
        foreach (var kv in layerMaterials)
            if (fpLo.Contains(kv.Key.ToLower())) { matName = kv.Value; break; }
    }

    // Priority 3: infer from object name keywords
    if (string.IsNullOrEmpty(matName)) {
        string n = (o.Attributes.Name ?? "").ToLower();
        if      (n.Contains("glass") || n.Contains("glazing"))
            matName = "M_Glass_TintedBronze";
        else if (n.Contains("mull") || n.Contains("frame"))
            matName = "M_Aluminum_Bronze";
        else if (n.Contains("terrain") || n.Contains("ground"))
            matName = "M_Terrain_DesertCoastal";
        else if (n.Contains("pool"))
            matName = "M_Concrete_Pool";
        else if (n.Contains("entry") || n.Contains("cedar"))
            matName = "M_Wood_DarkCedar";
        else
            matName = "M_Concrete_WarmBone";  // safe default
    }

    // Write User Text tags — these survive the .3dm save and Blender import
    o.Attributes.SetUserString("material", matName);
    string layerPath = rdoc.Layers[o.Attributes.LayerIndex].FullPath;
    o.Attributes.SetUserString("layer", layerPath);
    o.CommitChanges();
    tagged++;
}

sb.Append("Tagged=" + tagged + " skipped=" + skipped);
System.IO.File.WriteAllText(
    @"[project_path]\logs\export_tag_report.txt", sb.ToString());
throw new Exception(sb.ToString());
```

Confirm: all Breps/meshes tagged, skipped count is only curves/points/annotations.
Report any untagged objects and resolve before proceeding.

### Step 4 — Save Rhino snapshot with UserData

**CRITICAL:** `WriteUserData = true` is mandatory. Without it the material tags
are stripped from the file and the Blender import will have no metadata.

```csharp
var rdoc = Rhino.RhinoDoc.ActiveDoc;
string ts = System.DateTime.UtcNow.ToString("yyyyMMdd_HHmm");
string snapPath = $@"[project_path]\rhino_assets\base_model_phase6_snapshot_{ts}.3dm";

var opts = new Rhino.FileIO.FileWriteOptions();
opts.WriteGeometryOnly = false;
opts.WriteUserData = true;    // CRITICAL — preserves material tag User Text
bool ok = rdoc.WriteFile(snapPath, opts);
throw new Exception("Snapshot saved=" + ok + " path=" + snapPath);
```

Confirm the snapshot file exists and is non-zero size before continuing.

### Step 5 — Import into Blender via import_with_metadata.py

Switch to Blender. Run `skills/import_with_metadata.py` via BlenderMCP,
pointing it at the snapshot path from Step 4.

This script:
- Uses the `rhino3dm` Python library to read the `.3dm` directly (no FBX/OBJ)
- Preserves the full Rhino layer hierarchy as Blender collections
- Reads the `material` User Text from each object
- Sets `obj["material"]` (custom property) on every imported Blender mesh
- Sets `obj["rhino_layer"]` custom property for segmentation pass use
- Organises the scene hierarchy — each Rhino layer becomes a collection

**Do NOT attempt to import via File → Import FBX/OBJ.**
The `rhino3dm` approach is the only method that preserves metadata.

After import, confirm in the Blender outliner:
- All expected objects are present
- Objects are organised into collections matching Rhino layer names
- No objects at world origin that should be elsewhere

### Step 6 — Set rotation_mode = 'XYZ' on all imports

**CRITICAL — do not skip this step.**

```python
import bpy
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        obj.rotation_mode = 'XYZ'
```

Rhino exports arrive with `rotation_mode = 'QUATERNION'`. Setting
`rotation_euler` on a Quaternion-mode object is silently ignored.
This must be run before any transform work.

### Step 7 — Run validate_blender_scene.py

Run `skills/validate_blender_scene.py` via BlenderMCP.
This script checks:
- Every mesh has the `material` custom property set
- No objects at world origin (un-imported stubs)
- No z-fighting coplanar faces
- Render camera exists (or create a placeholder)
- All objects have `rotation_mode = 'XYZ'`

**Do NOT proceed to Phase 7 if this script reports critical failures.**
Fix all reported issues and re-run until clean.

### Step 8 — Load HDRI (basic setup for Phase 7)

Set up the world shader node chain now so it's ready for Phase 7 tuning.
Do not tune rotation or strength yet — just establish the chain.

```python
import bpy, os

world = bpy.context.scene.world
world.use_nodes = True
nt = world.node_tree

# Build: Environment Texture → Mapping → Gamma → Background → World Output
env   = nt.nodes.new("ShaderNodeTexEnvironment")
mapp  = nt.nodes.new("ShaderNodeMapping")
gamma = nt.nodes.new("ShaderNodeGamma")
bg    = next(n for n in nt.nodes if n.type == 'BACKGROUND')
out   = next(n for n in nt.nodes if n.type == 'OUTPUT_WORLD')

nt.links.new(env.outputs["Color"],    mapp.inputs["Vector"])
nt.links.new(mapp.outputs["Vector"],  gamma.inputs["Color"])
nt.links.new(gamma.outputs["Color"],  bg.inputs["Color"])
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

gamma.inputs["Value"].default_value = 4.0    # compress sky DR — tune in Phase 7
bg.inputs["Strength"].default_value = 1.0    # neutral starting value

# Load HDRI from project hdr/ folder if present
hdr_dir = r"[project_path]\hdr"
hdrs = [f for f in os.listdir(hdr_dir) if f.lower().endswith(('.hdr','.exr'))]
if hdrs:
    env.image = bpy.data.images.load(os.path.join(hdr_dir, hdrs[0]))
    print("HDRI loaded:", hdrs[0])
else:
    print("No HDRI found in hdr/ — add one before Phase 7")
```

### Step 9 — Save base_model.blend

```python
import bpy, datetime
stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
bpy.ops.wm.save_as_mainfile(
    filepath=fr"[project_path]\blender_assets\base_model_checkpoint_{stamp}.blend",
    copy=True)
bpy.ops.wm.save_as_mainfile(
    filepath=fr"[project_path]\blender_assets\base_model.blend")
print("Saved base_model.blend and checkpoint")
```

---

## Post-Phase Cleanup Checklist

- [ ] All Breps/meshes tagged in Rhino — zero untagged mesh/brep objects
- [ ] Snapshot `.3dm` saved with `WriteUserData = true`, file exists and non-zero
- [ ] All objects in Blender have `material` custom property set
- [ ] All objects have `rotation_mode = 'XYZ'` applied
- [ ] `validate_blender_scene.py` reports no critical failures
- [ ] HDRI loaded (or noted as missing with instruction for user)
- [ ] `base_model.blend` saved with checkpoint
- [ ] Tag report written to `[project]/logs/export_tag_report.txt`
- [ ] No objects at world origin in Blender outliner

---

## Known Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Blender objects have no `material` property | `WriteUserData = false` on snapshot | Re-save snapshot with `WriteUserData = true`, re-import |
| `import_with_metadata.py` fails with rhino3dm error | `rhino3dm` not installed in Blender Python | Run: `bpy.ops.preferences.addon_install()` or pip install rhino3dm |
| Objects at wrong positions after import | `rotation_mode = 'QUATERNION'` not fixed | Run Step 6 rotation_mode fix immediately after import |
| Untagged objects in export report | Objects not on named layers, no Rhino material | Assign to correct layer in Rhino and re-tag |
| Snapshot save reports `WriteFile = false` | File path invalid or drive full | Check path exists, create dirs if needed, check disk space |
| HDRI not loading | Wrong file extension or corrupt file | Check file in hdr/ folder is valid .hdr or .exr |
| BlenderMCP connection timeout | Server not started | Blender Scripting tab → `bpy.ops.blendermcp.start_server()` |

---

## ▶ REVIEW GATE 6 — Export

Present:
1. Blender outliner screenshot showing collection hierarchy
2. One object's Properties → Custom Properties panel showing `material` tag
3. `logs/export_tag_report.txt` content (tagged count, zero untagged)
4. A quick Cycles viewport shading view confirming geometry is present

Wait for written approval.

---

## Checkpoint Save

Blender checkpoint already saved in Step 9.
Save Rhino checkpoint to `[project]/rhino_assets/base_model_checkpoint_YYYYMMDD_HHMM.3dm`.

→ **TRAY:** Announce: "Phase complete — stop recording in the tray."
Rename: `06-export_blender-hermes.mkv`, `06-export_blender-rhino.mkv`,
        `06-export_blender-blender.mkv`. Confirm all clips present.

Proceed to `08_phase_lighting_camera.md`.
