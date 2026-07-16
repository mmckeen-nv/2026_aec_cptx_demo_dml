# Phase 3 - Rooms, Access, and Circulation

## Purpose

Lay out the ancillary bar, loading route, public/crew/service circulation, and
required doors without disturbing the accepted stage and LED volume.

## Inputs

- accepted Phase 2 checkpoint
- `prompts/01a_locked_scene_manifest.md` sections 2-4

## Outputs

- partitions on `VP06_ROOMS`
- doors/loading openings on `VP07_ACCESS`
- circulation and scenery-route references on `VP08_CIRCULATION`
- `work/vp_studio_01_checkpoint_03_rooms.3dm`

## Pre-Phase Audit Checklist

- [ ] Live Rhino contains `LED_ACTIVE_WALL`, `LED_REAR_SUPPORT`,
  `LED_FLOOR_PROXY`, and `LED_CEILING_ACTIVE`; checkpoint files do not count
- [ ] `LED_ACTIVE_WALL` is Z `0..288 in` and `LED_REAR_SUPPORT` is Z
  `0..312 in`; otherwise return to Phase 2 before creating any rooms
- [ ] Shell and LED geometry are accepted and preserved
- [ ] Public, crew, service, and loading sides are identified
- [ ] Stage/service clearances remain visible

## Execution Steps

1. Build the east ancillary bar from the ten exact room rectangles. Use 6 in
   partitions, Z 0..144, and 42 x 84 in personnel-door openings.
2. Build the control glazing and control-room door at their scheduled bounds.
3. Build the west equipment and review zones plus the protected 48 in aisle.
4. Confirm the two 168 x 192 in loading openings and clear south scenery route.
5. Print room clear rectangles, wall bounds, and circulation bounds before
   requesting a viewport image.

## Required C# implementation

Use C# only. Begin with the exact shared C# prelude in
`prompts/02_rhino_modeling_contract.md`.
Use these tested wall helpers and literal schedule; do not invent wall APIs.
Send the shared prelude plus this schedule inline through
`mcp_rhino_run_csharp(script=...)`; do not open or execute a local file.

```csharp
System.Action<string,int,double,double,double,double,double,double> XW=(n,li,x0,x1,y,z1,d0,d1)=>{double t=3;if(d1<=d0){SB(n,li,x0,x1,y-t,y+t,0,z1);return;}if(d0>x0)SB(n+"_L",li,x0,d0,y-t,y+t,0,z1);SB(n+"_HEAD",li,d0,d1,y-t,y+t,84,z1);if(d1<x1)SB(n+"_R",li,d1,x1,y-t,y+t,0,z1);};
System.Action<string,int,double,double,double,double> YW=(n,li,x,y0,y1,z1)=>{SB(n,li,x-3,x+3,y0,y1,0,z1);};
int rooms=GL("VP06_ROOMS",System.Drawing.Color.Khaki);int access=GL("VP07_ACCESS",System.Drawing.Color.Orange);int circ=GL("VP08_CIRCULATION",System.Drawing.Color.LimeGreen);
XW("PART_Y_NEG720",rooms,744,1068,-720,144,885,927);
XW("PART_Y_NEG540",rooms,744,1068,-540,144,885,927);
XW("PART_Y_NEG180_A",rooms,744,900,-180,144,801,843);XW("PART_Y_NEG180_B",rooms,900,1068,-180,144,963,1005);
XW("PART_Y_60_A",rooms,744,900,60,144,801,843);XW("PART_Y_60_B",rooms,900,1068,60,144,963,1005);
XW("PART_Y_300_A",rooms,744,900,300,144,801,843);XW("PART_Y_300_B",rooms,900,1068,300,144,963,1005);
XW("PART_Y_480",rooms,744,1068,480,144,885,927);
YW("PART_X_900_GREEN_WARDROBE",rooms,900,-180,60,144);YW("PART_X_900_CAMERA_PROD",rooms,900,60,300,144);YW("PART_X_900_MEDIA_EDIT",rooms,900,300,480,144);
SB("CONTROL_VIEW_GLAZING",access,744,750,570,798,42,126);
SB("ROOM_CEILING_PROXY",rooms,744,1068,-888,888,144,150);
var aisle=new Rhino.Geometry.PolylineCurve(new[]{new Rhino.Geometry.Point3d(-792,-600,0),new Rhino.Geometry.Point3d(-744,-600,0),new Rhino.Geometry.Point3d(-744,888,0),new Rhino.Geometry.Point3d(-792,888,0),new Rhino.Geometry.Point3d(-792,-600,0)});rdoc.Objects.AddCurve(aisle,A("WEST_48IN_CLEAR_AISLE",circ));
var route=new Rhino.Geometry.PolylineCurve(new[]{new Rhino.Geometry.Point3d(-600,-888,0),new Rhino.Geometry.Point3d(-192,-888,0),new Rhino.Geometry.Point3d(-192,-624,0),new Rhino.Geometry.Point3d(-600,-624,0),new Rhino.Geometry.Point3d(-600,-888,0)});rdoc.Objects.AddCurve(route,A("SOUTH_SCENERY_ROUTE",circ));
rdoc.Views.Redraw();System.Console.WriteLine("PHASE03_CREATED scheduled_partitions doors=10 glazing=1");
```

The shared construction-contract helpers must be copied
verbatim into the same inline call before this schedule. No external file replay.

## Hard Scope Boundary

Do not create rigging, cameras, chairs, workstations, lights, furniture, or
equipment in Phase 3. Do not alter the accepted LED curve unless a collision is
objectively demonstrated.

## Post-Phase Cleanup Checklist

- [ ] Control room has a clear view toward the stage
- [ ] Scenery route reaches the stage without crossing office/control space
- [ ] Public, crew, loading, and service approaches remain distinct
- [ ] Doors do not collide and circulation does not cross the LED service zone
- [ ] Room names, layers, bounds, and metadata are correct

## REVIEW GATE 3 - Rooms and Access

Present a readable plan plus an interior perspective. Ask vision about room
legibility, control-room relationship, loading route, circulation conflicts,
and obvious omissions. Correct concrete defects one object at a time.

## Checkpoint Save

Save `work/vp_studio_01_checkpoint_03_rooms.3dm`, then proceed to
`02d_phase_rigging_cameras.md`.
