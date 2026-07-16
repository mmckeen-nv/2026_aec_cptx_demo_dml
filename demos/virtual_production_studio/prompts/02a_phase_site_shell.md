# Phase 1 - Site and Building Shell

## Purpose

Establish the lot, building placement, exterior shell, roof datum, stage floor,
and clear soundstage envelope. This phase is proportion and circulation massing.

## Inputs

- `source/vp_studio_01_template.3dm`
- `user_prompts/project_prompt.md`
- `prompts/01a_locked_scene_manifest.md` sections 1-3
- locked `VP00_TEMPLATE_*` references

## Outputs

- lot/access references on `VP01_SITE`
- floor, exterior walls, and roof on `VP02_BUILDING_SHELL`
- clear stage envelope on `VP03_STAGE_ENVELOPE`
- `work/vp_studio_01_checkpoint_01_shell.3dm`

## Pre-Phase Audit Checklist

- [ ] Launcher-owned Rhino slot is connected; do not spawn or replace it
- [ ] Document units are inches and tolerance is 0.01 in
- [ ] Template property/building/stage references have been inspected
- [ ] No finished design geometry is being reused

## Execution Steps

1. Confirm inches, datum (0,0,0), and the manifest shell/stage envelopes.
2. Create the lot/access reference assembly from manifest-derived coordinates.
3. Create the slab and four exterior walls at their exact listed bounds; subtract
   the two exact south loading-door voids rather than covering them with walls.
4. Create the roof slab at X -1080..1080, Y -900..900, Z 576..588.
5. Create the stage envelope at X -720..720, Y -600..600, Z 0..576.
6. Print and validate bounds before requesting a viewport image.

## Required C# implementation

Send the following as one `mcp_rhino_run_csharp(script=...)` call. Do not
translate it to Python, probe alternatives, or reinterpret returned GUIDs.

```csharp
var rdoc = doc;
System.Func<string,System.Drawing.Color,int> GL = (name,color) => {
    for (int i=0; i<rdoc.Layers.Count; i++) {
        var old = rdoc.Layers[i];
        if (old != null && !old.IsDeleted && old.Name == name) return i;
    }
    var layer = new Rhino.DocObjects.Layer();
    layer.Name = name; layer.Color = color;
    int index = rdoc.Layers.Add(layer);
    if (index < 0) throw new System.Exception("Layer add failed: " + name);
    return index;
};
System.Func<string,int,double,double,double,double,double,double,System.Guid> SB = (name,li,x0,x1,y0,y1,z0,z1) => {
    var b = new Rhino.Geometry.Box(Rhino.Geometry.Plane.WorldXY,
        new Rhino.Geometry.Interval(x0,x1), new Rhino.Geometry.Interval(y0,y1),
        new Rhino.Geometry.Interval(z0,z1));
    var a = new Rhino.DocObjects.ObjectAttributes();
    a.Name=name; a.LayerIndex=li;
    a.SetUserString("project","vp-studio-01"); a.SetUserString("discipline","ARCHITECTURE");
    a.SetUserString("system","BUILDING_SHELL"); a.SetUserString("agentic_phase","01_shell");
    a.SetUserString("phase","SCHEMATIC"); a.SetUserString("assumption_status","LOCKED_MANIFEST");
    a.SetUserString("source_basis","01a_locked_scene_manifest.md");
    a.SetUserString("export_to_blender","yes");
    var id=rdoc.Objects.AddBrep(b.ToBrep(),a);
    if(id==System.Guid.Empty) throw new System.Exception("Box add failed: "+name);
    return id;
};
System.Func<string,int,Rhino.Geometry.Point3d,Rhino.Geometry.Point3d,System.Guid> LC = (name,li,a0,b0) => {
    var a=new Rhino.DocObjects.ObjectAttributes(); a.Name=name; a.LayerIndex=li;
    a.SetUserString("project","vp-studio-01"); a.SetUserString("agentic_phase","01_shell");
    a.SetUserString("phase","SCHEMATIC"); a.SetUserString("export_to_blender","false");
    return rdoc.Objects.AddCurve(new Rhino.Geometry.LineCurve(a0,b0),a);
};
int site=GL("VP01_SITE",System.Drawing.Color.SandyBrown);
int shell=GL("VP02_BUILDING_SHELL",System.Drawing.Color.SlateGray);
int stage=GL("VP03_STAGE_ENVELOPE",System.Drawing.Color.DodgerBlue);
SB("SLAB_FLOOR",shell,-1080,1080,-900,900,-8,0);
SB("WALL_SOUTH_UPPER",shell,-1080,1080,-900,-888,192,576);
SB("WALL_SOUTH_LOW_W",shell,-1080,-600,-900,-888,0,192);
SB("WALL_SOUTH_LOW_M",shell,-432,-360,-900,-888,0,192);
SB("WALL_SOUTH_LOW_E",shell,-192,1080,-900,-888,0,192);
SB("WALL_NORTH_EXT",shell,-1080,1080,888,900,0,576);
SB("WALL_WEST_EXT",shell,-1080,-1068,-888,888,0,576);
SB("WALL_EAST_EXT",shell,1068,1080,-888,888,0,576);
SB("ROOF_SLAB",shell,-1080,1080,-900,900,576,588);
var p=new[]{new Rhino.Geometry.Point3d(-720,-600,0),new Rhino.Geometry.Point3d(720,-600,0),new Rhino.Geometry.Point3d(720,600,0),new Rhino.Geometry.Point3d(-720,600,0),new Rhino.Geometry.Point3d(-720,-600,576),new Rhino.Geometry.Point3d(720,-600,576),new Rhino.Geometry.Point3d(720,600,576),new Rhino.Geometry.Point3d(-720,600,576)};
int[,] e={{0,1},{1,2},{2,3},{3,0},{4,5},{5,6},{6,7},{7,4},{0,4},{1,5},{2,6},{3,7}};
for(int i=0;i<12;i++) LC("STAGE_EDGE_"+(i+1).ToString("00"),stage,p[e[i,0]],p[e[i,1]]);
rdoc.Views.Redraw();
System.Console.WriteLine("PHASE01_CREATED shell=9 stage_edges=12");
```

Build the shell as coherent assemblies, then use focused correction calls only
for defects supported by numeric or viewport evidence. Do not split its
wall/slab/roof pieces into accidental one-object retry churn.

## Hard Scope Boundary

Do not create the LED wall, LED ceiling, rooms, interior partitions, doors,
loading doors, rigging, cameras, chairs, workstations, lights, or equipment in
Phase 1. Those belong to later phases.

## Post-Phase Cleanup Checklist

- [ ] Lot, building, and stage are visually distinct
- [ ] Building exterior is exactly 180 ft x 150 ft
- [ ] Stage planning zone is exactly 120 ft x 100 ft; clear below Z 480
- [ ] Floor/walls/roof align without accidental stacking or duplicate objects
- [ ] Names, layers, bounds, and metadata are correct

## REVIEW GATE 1 - Shell

Present a plan view and exterior perspective. Ask vision whether placement,
scale, entrances, truck approach, clear height, and obvious collisions read
correctly only after the validator prints `NUMERIC_PASS`. Correct only the named
defects and revalidate.

## Checkpoint Save

Save `work/vp_studio_01_checkpoint_01_shell.3dm` with
`mcp_rhino_save_doc`. Then proceed to `02b_phase_stage_led.md`.
