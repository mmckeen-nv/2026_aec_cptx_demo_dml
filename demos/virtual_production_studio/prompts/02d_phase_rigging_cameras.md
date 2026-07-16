# Phase 4 - Rigging, Cameras, and Production Layout

## Purpose

Add conceptual rigging, tracked-camera envelopes, motivated light positions,
workstations, chairs, and named equipment proxies. Rhino establishes layout;
Blender replaces visible proxies with approved assets.

## Inputs

- accepted Phase 3 checkpoint
- `prompts/01a_locked_scene_manifest.md` sections 6-8

## Outputs

- rigging/tracking datums on `VP09_RIGGING_TRACKING`
- camera bodies/frustums/envelopes on `VP10_CAMERAS`
- furniture/equipment proxies on `VP11_PRODUCTION_LAYOUT`
- `work/vp_studio_01_checkpoint_04_layout.3dm`

## Pre-Phase Audit Checklist

- [ ] Live Rhino contains `CONTROL_VIEW_GLAZING`, `WEST_48IN_CLEAR_AISLE`, and
  `SOUTH_SCENERY_ROUTE`; checkpoint files do not count
- [ ] Live Rhino still contains the four required LED objects with positive-Z
  bounds; if not, repair the earliest incomplete phase first
- [ ] Stage, LED, rooms, loading, and circulation are accepted
- [ ] Camera paths and protected clear zones are visible
- [ ] Asset-replacement metadata convention is understood

## Execution Steps

1. Create the roof-hung rigging grid at the exact five Y centerlines, six X
   centerlines, and Z 480..516. Do not add stage-floor columns.
2. Create the catwalk, hoist points, and twelve scheduled light proxies.
3. Create all six named cameras at the scheduled marks and create their exact
   paths/envelopes as transparent curves or surfaces.
4. Create the six workstations, six operator chairs, and twelve review chairs at
   their listed centers and maximum dimensions.
5. Create the scheduled carts, road cases, dolly, crane base, and calibration
   targets at their listed centers and maximum dimensions.
6. Print centers, bounds, and protected-zone intersection results before vision.

## Required C# implementation

Use one or more `mcp_rhino_run_csharp(script=...)` calls. Each call begins with
the exact shared `GL`, `A`, and `SB` prelude from
`prompts/02_rhino_modeling_contract.md`. The schedules below are literal;
do not convert them to Python or issue one object per model turn.

### Rigging and stage lights

```csharp
int rig=GL("VP09_RIGGING_TRACKING",System.Drawing.Color.Gold);
double[] ys={-480,-240,0,240,480};double[] xs={-600,-360,-120,120,360,600};
foreach(double y in ys)SB("TRUSS_EW_Y_"+y,rig,-600,600,y-12,y+12,480,516);
foreach(double x in xs)SB("TRUSS_NS_X_"+x,rig,x-12,x+12,-480,480,480,516);
foreach(double x in xs)foreach(double y in ys)SB("HOIST_"+x+"_"+y,rig,x-9,x+9,y-9,y+9,456,480);
SB("CATWALK_DECK",rig,-660,660,528,576,414,420);SB("CATWALK_GUARD_S",rig,-660,660,528,530,420,462);SB("CATWALK_GUARD_N",rig,-660,660,574,576,420,462);
double[,] lights={{-360,-240,468},{-120,-240,468},{120,-240,468},{360,-240,468},{-360,0,468},{-120,0,468},{120,0,468},{360,0,468},{-360,240,468},{-120,240,468},{120,240,468},{360,240,468}};
for(int i=0;i<12;i++){double x=lights[i,0],y=lights[i,1],z=lights[i,2];SB("STAGE_LIGHT_"+(i+1).ToString("00"),rig,x-12,x+12,y-6,y+6,z-6,z+6);}
rdoc.Views.Redraw();System.Console.WriteLine("RIGGING_CREATED trusses=11 hoists=30 lights=12");
```

### Cameras and movement envelopes

```csharp
int cams=GL("VP10_CAMERAS",System.Drawing.Color.Red);
System.Action<string,double,double,double,double,double,double> CAM=(n,x,y,z,tx,ty,tz)=>{SB(n+"_BODY",cams,x-12,x+12,y-6,y+6,z-6,z+6);var a=A(n+"_AIM",cams);rdoc.Objects.AddCurve(new Rhino.Geometry.LineCurve(new Rhino.Geometry.Point3d(x,y,z),new Rhino.Geometry.Point3d(tx,ty,tz)),a);double r=24;for(int k=0;k<3;k++){double q=2.0*System.Math.PI*k/3.0;rdoc.Objects.AddCurve(new Rhino.Geometry.LineCurve(new Rhino.Geometry.Point3d(x,y,z-6),new Rhino.Geometry.Point3d(x+r*System.Math.Cos(q),y+r*System.Math.Sin(q),0)),A(n+"_TRIPOD_"+(k+1),cams));}};
CAM("CAM_A_HERO_TRACKED",-120,-420,66,-120,-60,72);CAM("CAM_E_WITNESS",600,-540,120,-120,0,72);CAM("CAM_F_CONTROL_ROOM",750,684,66,-120,0,72);
CAM("CAM_B_DOLLY_TRACKED",-120,-480,66,-120,-60,72);CAM("CAM_C_CRANE_TRACKED",360,-240,66,-120,-60,72);
rdoc.Objects.AddCurve(new Rhino.Geometry.LineCurve(new Rhino.Geometry.Point3d(-360,-480,0),new Rhino.Geometry.Point3d(120,-480,0)),A("CAM_B_DOLLY_PATH",cams));
rdoc.Objects.AddCircle(new Rhino.Geometry.Circle(new Rhino.Geometry.Point3d(360,-240,0),300),A("CAM_C_CRANE_SWEEP",cams));
var hand=new Rhino.Geometry.PolylineCurve(new[]{new Rhino.Geometry.Point3d(-600,-360,0),new Rhino.Geometry.Point3d(-360,-360,0),new Rhino.Geometry.Point3d(-360,-120,0),new Rhino.Geometry.Point3d(-600,-120,0),new Rhino.Geometry.Point3d(-600,-360,0)});rdoc.Objects.AddCurve(hand,A("CAM_D_HANDHELD_TRACKED_OPERATING_ZONE",cams));
rdoc.Views.Redraw();System.Console.WriteLine("CAMERAS_CREATED fixed=5 envelopes=3");
```

### Workstations, chairs, and equipment

```csharp
int lay=GL("VP11_PRODUCTION_LAYOUT",System.Drawing.Color.SteelBlue);
double[,] ws={{804,570},{804,684},{804,798},{960,570},{960,684},{960,798}};for(int i=0;i<6;i++){double x=ws[i,0],y=ws[i,1];SB("WORKSTATION_"+(i+1).ToString("00"),lay,x-15,x+15,y-36,y+36,0,30);}
double[,] op={{852,570},{852,684},{852,798},{1008,570},{1008,684},{1008,798}};for(int i=0;i<6;i++){double x=op[i,0],y=op[i,1];SB("OP_CHAIR_"+(i+1).ToString("00"),lay,x-12,x+12,y-12,y+12,0,42);}
double[,] rev={{-1008,330},{-936,330},{-864,330},{-1008,414},{-936,414},{-864,414},{-1008,498},{-936,498},{-864,498},{-1008,582},{-936,582},{-864,582}};for(int i=0;i<12;i++){double x=rev[i,0],y=rev[i,1];SB("REVIEW_CHAIR_"+(i+1).ToString("00"),lay,x-11,x+11,y-11,y+11,0,36);}
double[,] carts={{-1008,-504},{-936,-504},{-864,-504},{-816,-504}};for(int i=0;i<4;i++){double x=carts[i,0],y=carts[i,1];SB("CART_"+(i+1).ToString("00"),lay,x-24,x+24,y-12,y+12,0,42);}
double[,] cases={{-1008,-408},{-912,-408},{-816,-408},{-1008,-324},{-912,-324},{-816,-324}};for(int i=0;i<6;i++){double x=cases[i,0],y=cases[i,1];SB("ROAD_CASE_"+(i+1).ToString("00"),lay,x-24,x+24,y-12,y+12,0,30);}
SB("STAGE_DIRECTOR_CHAIR_01",lay,-611,-589,-311,-289,0,36);SB("STAGE_DIRECTOR_CHAIR_02",lay,589,611,-311,-289,0,36);
SB("HERO_ROAD_CASE_01",lay,-624,-576,-432,-408,0,30);SB("HERO_ROAD_CASE_02",lay,576,624,-432,-408,0,30);
SB("FLOOR_LIGHT_01",lay,-672,-648,-132,-108,0,72);SB("FLOOR_LIGHT_02",lay,648,672,-132,-108,0,72);
SB("SERVER_RACK_01",lay,774,798,369,411,0,84);SB("SERVER_RACK_02",lay,846,870,369,411,0,84);
SB("DOLLY_BASE",lay,-150,-90,-498,-462,0,12);SB("CRANE_BASE",lay,324,396,-276,-204,0,24);SB("CAL_TARGET_01",lay,564,612,453,459,0,72);SB("CAL_TARGET_02",lay,624,672,453,459,0,72);
rdoc.Views.Redraw();System.Console.WriteLine("LAYOUT_CREATED workstations=6 chairs=20 carts=4 cases=8 floor_lights=2 racks=2 equipment=4");
```

## Hard Scope Boundary

Do not model electrical, HVAC, data, fire protection, conduit, cable tray, or
distribution systems. Do not detail furniture in Rhino. Do not create hundreds
of decorative placeholders merely to increase object count.

## Post-Phase Cleanup Checklist

- [ ] Camera paths, crane envelope, loading route, and circulation do not collide
- [ ] Cameras point toward useful stage compositions
- [ ] Chairs/workstations/equipment read as intentional layouts, not stacked boxes
- [ ] Every visible proxy is named and tagged for Blender replacement
- [ ] Rigging and light positions are plausible planning assumptions
- [ ] Both floor lights are complete soft-panel stands; no bare C-stand appears
- [ ] Required stage-edge chairs and road cases create readable foreground context

## REVIEW GATE 4 - Physical Layout

Present stage-wide and control-room perspectives. Ask vision about recognizable
geometry, LED smoothness, sightlines, collisions, camera composition, furniture
layout, and omissions. Correct concrete defects, then write the planning-only
estimated-load note.

## Checkpoint Save

Save `work/vp_studio_01_checkpoint_04_layout.3dm`, then proceed to
`07_phase_export_blender.md`.
