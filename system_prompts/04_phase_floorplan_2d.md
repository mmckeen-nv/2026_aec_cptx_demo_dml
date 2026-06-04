# Phase — 2D Floor Plan Generation in Rhino
### Execution Prompt
*Part of the Hermes AEC Demo prompt suite*
*Reads: `01_user_prompt.md` § site program, `[project]/prompts/` deltas*
*Version 1.0 — May 2026*
*Tool chain: Rhino 3D + RhinoMCP (C# scripting)*

---

## Purpose

Generate a fully annotated 2D floor plan in Rhino — room outlines, site
features, labels — organised into a clean nested layer hierarchy.
This plan serves as the drawing-board reference and camera-visible annotation
layer for the project. It is drawn flat at Z = 0.

This phase is optional and project-specific. Run it when the project calls
for visible floor plan documentation or when the 3D floor plan (prompt 19)
will be derived from explicit room geometry.

---

## Inputs

- Project brief / delta notes — site dimensions, room programme, orientation
- `[project]/rhino_assets/` — working Rhino file (open in Rhino)

## Outputs

- Floor plan curves and labels added to Rhino document
- All geometry on correct FLOORPLAN sublayers (see Layer Hierarchy below)

---

## Pre-Phase Audit Checklist

- [ ] Rhino document is open and units are set to metres
- [ ] RhinoMCP server running on port 3001
- [ ] Node.js runner template ready (see Script Runner Pattern below)
- [ ] Delta notes read for site dimensions and room programme
- [ ] Coordinate origin confirmed (typically building SW corner or plan centre)

---

## OBS Recording Protocol

→ **TRAY:** Update `current_stage.json` with current phase. Announce: "Starting phase — click Record in the tray when ready."

→ **TRAY:** Announce: "Switching to Rhino — click Record Rhino in the tray when ready."

→ **TRAY:** Announce: "Switching back to Hermes."

---

## Layer Hierarchy

All floor plan geometry lives under the `FLOORPLAN` parent layer.
Create the full hierarchy before adding any geometry.

```
FLOORPLAN                ← parent (root)
  FLOORPLAN::SITE        ← site outline, lot lines, driveway curves
  FLOORPLAN::MASTER      ← master bedroom and ensuite curves
  FLOORPLAN::LIVING      ← great room, dining, lounge curves
  FLOORPLAN::BEDROOM     ← secondary bedrooms
  FLOORPLAN::BATH        ← bathrooms and powder rooms
  FLOORPLAN::UTIL        ← laundry, mudroom, hall, utility
  FLOORPLAN::GARAGE      ← garage and motor court curves
  FLOORPLAN::OUTDOOR     ← terrace, pool, patio, paddock, cottage
  FLOORPLAN::LABELS      ← all text annotation (room names + areas)
```

**Additional parent layers for 3D work (create at same time if planning 3D floor plan):**
```
3D_floorplan             ← parent for all 3D wall geometry
massing_model            ← parent for massing volumes, roofs, site features
```

### Layer creation rule **[CRITICAL]**

Always use `RhinoApp.RunScript` with the `::` separator to create nested layers.
**Never** use `doc.Layers.Add(l)` with `l.ParentLayerId` — this approach silently
fails to create the hierarchy in this RhinoMCP scripting environment.

```csharp
// CORRECT — creates properly nested sublayer
RhinoApp.RunScript("-_Layer _New FLOORPLAN::SITE _Enter", false);
RhinoApp.RunScript("-_Layer _New FLOORPLAN::MASTER _Enter", false);
// ... one RunScript call per sublayer
```

### Layer lookup (3-method fallback)

After creation, always find layers with this fallback chain:

```csharp
Func<string,int> GL = (path) => {
    // Method 1: full path lookup
    int i = doc.Layers.FindByFullPath(path, -1);
    if (i >= 0) return i;
    // Method 2: find parent then iterate children by name + ParentLayerId
    int sep = path.LastIndexOf("::");
    if (sep > 0) {
        int pIdx = doc.Layers.FindByFullPath(path.Substring(0, sep), -1);
        if (pIdx >= 0) {
            System.Guid pId = doc.Layers[pIdx].Id;
            for (int j = 0; j < doc.Layers.Count; j++)
                if (!doc.Layers[j].IsDeleted
                    && doc.Layers[j].Name == path.Substring(sep + 2)
                    && doc.Layers[j].ParentLayerId == pId)
                    return j;
        }
    }
    // Method 3: set as current via RunScript, read CurrentLayerIndex
    RhinoApp.RunScript("-_Layer _Current \"" + path + "\" _Enter", false);
    return doc.Layers.CurrentLayerIndex;
};
```

### The `get_scene` "Unknown layer" artefact

The RhinoMCP `get_scene` tool reports nested layers as "Unknown layer" — this is
a known bug in the MCP tool, not an error in the layer structure. Verify the
hierarchy visually in Rhino's Layer Panel, not via `get_scene`.

---

## Execution Steps

### Step 1 — Create layer hierarchy

Run layer creation in a single script before any geometry is added.
Create all FLOORPLAN sublayers, then 3D_floorplan and massing_model parents
and their sublayers if the 3D floor plan phase will follow.

```csharp
// FLOORPLAN sublayers
string[] fpSubs = {"SITE","MASTER","LIVING","BEDROOM","BATH","UTIL","GARAGE","OUTDOOR","LABELS"};
foreach (string s in fpSubs)
    RhinoApp.RunScript("-_Layer _New FLOORPLAN::" + s + " _Enter", false);

// 3D_floorplan sublayers
string[] walls = {"exterior_walls","garage_walls","master_bedroom_walls",
    "master_bath_walls","master_suite_walls","great_room_walls","den_walls",
    "kitchen_walls","powder_room_walls","foyer_walls","bedroom_walls",
    "bedroom_2_walls","bedroom_3_walls","bathroom_walls","hall_walls",
    "laundry_walls","mudroom_walls","guest_cottage_walls"};
foreach (string w in walls)
    RhinoApp.RunScript("-_Layer _New 3D_floorplan::" + w + " _Enter", false);

// massing_model sublayers
string[] ms = {"ROOF","BARN","SLAB","WATER","DRIVE","FENCE","WALLS"};
foreach (string m in ms)
    RhinoApp.RunScript("-_Layer _New massing_model::" + m + " _Enter", false);
```

**Verify in Rhino's Layer Panel** that the hierarchy is nested (indented)
before continuing. The panel is the source of truth — not `get_scene`.

### Step 2 — Core drawing helpers

Define these helpers at the top of every floor plan drawing script.
They encode the conventions for adding curves and labels.

```csharp
var doc = RhinoDoc.ActiveDoc;

// Rectangle curve on a specified layer
Action<double,double,double,double,int> R = (x0,y0,x1,y1,li) => {
    var pts = new List<Point3d> {
        new Point3d(x0,y0,0), new Point3d(x1,y0,0),
        new Point3d(x1,y1,0), new Point3d(x0,y1,0),
        new Point3d(x0,y0,0) };
    var a = new ObjectAttributes(); a.LayerIndex = li;
    doc.Objects.AddCurve(new Polyline(pts).ToNurbsCurve(), a);
};

// Room with rectangle + centred label (name + area in m²)
Action<double,double,double,double,string,int> DR = (x0,y0,x1,y1,name,li) => {
    R(x0,y0,x1,y1,li);
    double cx=(x0+x1)/2, cy=(y0+y1)/2;
    double w=Math.Abs(x1-x0), h=Math.Abs(y1-y0);
    double th = Math.Max(0.22, Math.Min(Math.Min(w*0.10, h*0.13), 0.65));
    var te = new TextEntity();
    te.Plane = new Plane(new Point3d(cx,cy,0), Vector3d.XAxis, Vector3d.YAxis);
    te.PlainText = name + " " + (int)(w*h) + "m2";
    te.TextHeight = th;
    te.Justification = TextJustification.MiddleCenter;
    var ta = new ObjectAttributes();
    ta.LayerIndex = GL("FLOORPLAN::LABELS");   // always label layer
    doc.Objects.Add(te, ta);
};

// Site feature: rectangle on SITE layer with a text label
Action<double,double,double,double,string> DS = (x0,y0,x1,y1,nm) => {
    R(x0,y0,x1,y1,GL("FLOORPLAN::SITE"));
    var te = new TextEntity();
    te.Plane = new Plane(new Point3d((x0+x1)/2,(y0+y1)/2,0),
                         Vector3d.XAxis, Vector3d.YAxis);
    te.PlainText = nm;
    te.TextHeight = 0.8;
    te.Justification = TextJustification.MiddleCenter;
    var ta = new ObjectAttributes();
    ta.LayerIndex = GL("FLOORPLAN::LABELS");
    doc.Objects.Add(te, ta);
};
```

### Step 3 — Site outline and features

Draw the site boundary and all site-level features (driveways, paddock,
outbuilding footprints) on `FLOORPLAN::SITE` and `FLOORPLAN::OUTDOOR`.

```csharp
int lSite = GL("FLOORPLAN::SITE");
// Site rectangle — adapt coordinates to project
R(-15,-48,98,32, lSite);

// Site features (adapt to project programme)
DS(18,21.5,35,28, "Motor Court");
DS(24,28,34,40, "Driveway");
```

### Step 4 — Room outlines

Draw each room as a rectangle on its programme layer with `DR`.
Use project delta notes for dimensions.

Typical programme categories:
- `lMstr = GL("FLOORPLAN::MASTER")` — master wing
- `lLiv = GL("FLOORPLAN::LIVING")` — main living areas
- `lBed = GL("FLOORPLAN::BEDROOM")` — secondary bedrooms
- `lBth = GL("FLOORPLAN::BATH")` — bathrooms
- `lUtl = GL("FLOORPLAN::UTIL")` — service rooms
- `lGar = GL("FLOORPLAN::GARAGE")` — garage
- `lOut = GL("FLOORPLAN::OUTDOOR")` — outdoor features

```csharp
// Example — adapt all dimensions to project
DR(0,0,8.5,8,    "Master Bedroom",  lMstr);
DR(0,8,4,11.5,   "His Walk-In",     lMstr);
DR(4,8,8.5,11.5, "Her Walk-In",     lMstr);
DR(0,11.5,8.5,14,"Master Bath",     lBth);
DR(11,0,24,9.5,  "Great Room",      lLiv);
// ... continue for all rooms in programme
```

### Step 5 — Outdoor features and site annotation

Draw pool, terrace, patio, cottage footprint, paddock boundary, barn.
Complex shapes (L-shaped paddock, irregular boundaries) use a Polyline
added directly rather than the DR rectangle helper.

```csharp
int lOut = GL("FLOORPLAN::OUTDOOR");

// Paddock — example L-shape using PolylineCurve
var paddock = new List<Point3d> {
    new Point3d(38,29,0), new Point3d(90,29,0),
    new Point3d(90,-19,0), new Point3d(66,-19,0),
    new Point3d(66,-43,0), new Point3d(38,-43,0),
    new Point3d(38,29,0) };
var pa = new ObjectAttributes(); pa.LayerIndex = lOut;
doc.Objects.AddCurve(new Polyline(paddock).ToNurbsCurve(), pa);
```

### Step 6 — Zoom and view

After all geometry is added, zoom to extents so the plan is visible.

```csharp
doc.Views.Redraw();
RhinoApp.RunScript("_ZoomExtents", false);
RhinoApp.RunScript("_Plan _World", false);  // top-down view
```

---

## Script Runner Pattern

Scripts are written to disk and executed via a Node.js runner.
This avoids MCP connection timeouts on long-running scripts.

```javascript
// runner.mjs
import { readFileSync } from "fs";
const B = "http://localhost:3001/mcp";
const H = { "Content-Type": "application/json",
             "Accept": "application/json, text/event-stream" };
let id = 1;
async function mcp(m, p = {}) {
    const r = await fetch(B, { method:"POST", headers:H,
        body: JSON.stringify({ jsonrpc:"2.0", id:id++, method:m, params:p }) });
    const t = await r.text();
    const a = [];
    for (const l of t.split("\n"))
        if (l.startsWith("data:")) try { a.push(JSON.parse(l.slice(5))); } catch {}
    return a[a.length-1] || {};
}
await mcp("initialize", { protocolVersion:"2024-11-05",
    capabilities:{}, clientInfo:{ name:"hermes", version:"1.0" } });
await fetch(B, { method:"POST", headers:H,
    body: JSON.stringify({ jsonrpc:"2.0", method:"notifications/initialized" }) });

const script = readFileSync("C:/path/to/script.cs", "utf8");
const r = await mcp("tools/call",
    { name:"rhinoceros_operator", arguments:{ script } });
console.log(r?.result?.isError ? "FAIL" : "OK",
    r?.result?.content?.[0]?.text?.substring(0,120) || "");
```

Run from terminal: `node runner.mjs`

**Chunk scripts that exceed ~60 lines of C# content.**
The RhinoMCP C# engine handles long scripts but splitting by logical step
(layers, rooms, site features) makes debugging much easier.

---

## Output to File (for debugging)

`RhinoApp.WriteLine` output does NOT return through MCP.
Use `System.IO.File.WriteAllText` to inspect values:

```csharp
System.IO.File.WriteAllText(
    @"C:\Users\swags\Documents\AEC_demo_v2\debug.txt",
    "Layer count: " + doc.Layers.Count + "\nObjects: " + doc.Objects.Count);
```

---

## Post-Phase Cleanup Checklist

- [ ] Layer Panel shows nested hierarchy (FLOORPLAN with indented sublayers)
- [ ] All room outlines present and dimensionally correct
- [ ] Labels showing correct room names and m² areas
- [ ] Site outline on FLOORPLAN::SITE
- [ ] Outdoor features (pool, paddock, barn, driveway) on correct sublayers
- [ ] No objects on the Default or root-level layers
- [ ] Plan readable in top-down (Plan) view

---

## ▶ REVIEW GATE — 2D Floor Plan

Present a screenshot of the Rhino top-down plan view showing:
- Full site outline with the building footprint inside it
- All rooms labelled with names and areas
- Outdoor features (pool, paddock, etc.) visible

Confirm room programme completeness and dimensional accuracy before
proceeding to 3D floor plan generation or massing.

---

## Known Failure Modes

| Symptom | Root cause | Fix |
|---|---|---|
| Layers appear flat in panel (not nested) | Used `doc.Layers.Add` with `ParentLayerId` | Use `RunScript("-_Layer _New A::B _Enter")` exclusively |
| `get_scene` reports "Unknown layer" for all objects | MCP tool bug with nested layers | Ignore — check Rhino Layer Panel directly |
| Text labels appear in wrong position | TextEntity plane not set to room centre | Set `te.Plane` with correct centroid Point3d |
| DR helper produces 0m² label | Integer cast of float product rounds to 0 | Use `(int)(w*h)` after confirming w,h > 1 |
| Script times out | Too many objects created in one call | Split into chunks of ~30-40 objects per RunScript |
| Layer lookup returns wrong index | GL method fell back to RunScript which changed current layer | Pre-warm all layer indices at script start, store in variables |

---

## Checkpoint Save

Save Rhino file to `[project]/rhino_assets/` with timestamp.

```csharp
string stamp = System.DateTime.Now.ToString("yyyyMMdd_HHmm");
doc.WriteFile(
    @"[project_path]\rhino_assets\base_model_checkpoint_" + stamp + ".3dm",
    new Rhino.FileIO.FileWriteOptions());
```

→ **TRAY:** Announce: "Phase complete — stop recording in the tray."

Proceed to `05_phase_floorplan_3d.md` if 3D floor plan is in scope,
or to `05_massing_prompt.md` for pure massing work.
