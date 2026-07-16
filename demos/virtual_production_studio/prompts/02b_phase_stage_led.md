# Phase 2 - Stage and LED Volume

## Purpose

Build the principal shooting environment: stage floor, smooth LED wall, shallow
support depth, service clearance, required LED floor proxy, and LED ceiling.

## Inputs

- accepted Phase 1 shell checkpoint
- `prompts/01a_locked_scene_manifest.md` sections 2 and 5

## Outputs

- smooth LED face and support on `VP04_LED_VOLUME`
- LED ceiling/floor proxies on `VP05_LED_AUX`
- service and shooting-clearance references
- `work/vp_studio_01_checkpoint_02_led.3dm`

## Pre-Phase Audit Checklist

- [ ] Phase 1 shell is accepted
- [ ] Stage bounds and 40 ft clear height are confirmed
- [ ] Camera-facing side and service side are identified

## Execution Steps

1. Declare `cx=-120`, `cy=0`, active radius `480`, start angle `0`, end angle
   `180`, and Z `0..288`; do not use an implicit world-origin polar helper.
2. Create the smooth active face and sample its radius numerically.
3. Create the 2 in active thickness and 18 in rear support outward only.
4. Create the 72 in service boundary; total radial envelope must not exceed 572.
5. Create the exact LED floor, ceiling, support, talent-zone, and calibration
   storage geometry from the manifest.
6. Print bounds and radius-error results before requesting a viewport image.

## Required C# implementation

Use one `mcp_rhino_run_csharp(script=...)` call containing the shared `GL`,
`SB`, and attribute helpers from Phase 1 plus this exact LED implementation.
Do not use Python and do not approximate the wall with boxes.

```csharp
var rdoc=doc;
System.Func<string,System.Drawing.Color,int> GL=(name,color)=>{for(int i=0;i<rdoc.Layers.Count;i++){var l=rdoc.Layers[i];if(l!=null&&!l.IsDeleted&&l.Name==name)return i;}var n=new Rhino.DocObjects.Layer();n.Name=name;n.Color=color;int k=rdoc.Layers.Add(n);if(k<0)throw new System.Exception("Layer add failed: "+name);return k;};
System.Func<string,int,Rhino.DocObjects.ObjectAttributes> A=(name,li)=>{var a=new Rhino.DocObjects.ObjectAttributes();a.Name=name;a.LayerIndex=li;a.SetUserString("project","vp-studio-01");a.SetUserString("discipline","ARCHITECTURE");a.SetUserString("system","LED_VOLUME");a.SetUserString("agentic_phase","02_led");a.SetUserString("phase","SCHEMATIC");a.SetUserString("assumption_status","LOCKED_MANIFEST");a.SetUserString("source_basis","01a_locked_scene_manifest.md");a.SetUserString("export_to_blender","yes");return a;};
System.Func<string,int,double,double,double,double,double,double,System.Guid> SB=(name,li,x0,x1,y0,y1,z0,z1)=>{var b=new Rhino.Geometry.Box(Rhino.Geometry.Plane.WorldXY,new Rhino.Geometry.Interval(x0,x1),new Rhino.Geometry.Interval(y0,y1),new Rhino.Geometry.Interval(z0,z1));var id=rdoc.Objects.AddBrep(b.ToBrep(),A(name,li));if(id==System.Guid.Empty)throw new System.Exception("Box add failed: "+name);return id;};
System.Func<double,double,double,bool,Rhino.Geometry.Curve> ARC=(acx,acy,r,reverse)=>{var east=new Rhino.Geometry.Point3d(acx+r,acy,0);var north=new Rhino.Geometry.Point3d(acx,acy+r,0);var west=new Rhino.Geometry.Point3d(acx-r,acy,0);return reverse?new Rhino.Geometry.ArcCurve(new Rhino.Geometry.Arc(west,north,east)):new Rhino.Geometry.ArcCurve(new Rhino.Geometry.Arc(east,north,west));};
System.Func<double,double,double,double,Rhino.Geometry.Curve> RING=(rcx,rcy,r0,r1)=>{var c=new Rhino.Geometry.PolyCurve();c.Append(ARC(rcx,rcy,r0,false));c.Append(new Rhino.Geometry.LineCurve(new Rhino.Geometry.Point3d(rcx-r0,rcy,0),new Rhino.Geometry.Point3d(rcx-r1,rcy,0)));c.Append(ARC(rcx,rcy,r1,true));c.Append(new Rhino.Geometry.LineCurve(new Rhino.Geometry.Point3d(rcx+r1,rcy,0),new Rhino.Geometry.Point3d(rcx+r0,rcy,0)));if(!c.IsClosed)throw new System.Exception("LED ring profile not closed");return c;};
System.Func<string,int,Rhino.Geometry.Curve,double,System.Guid> EX=(name,li,profile,h)=>{var e=Rhino.Geometry.Extrusion.Create(profile,h,true);if(e==null)throw new System.Exception("Extrusion failed: "+name);var bb=e.GetBoundingBox(true);if(bb.Min.Z < -0.001){e=Rhino.Geometry.Extrusion.Create(profile,-h,true);if(e==null)throw new System.Exception("Positive-Z extrusion retry failed: "+name);bb=e.GetBoundingBox(true);}if(System.Math.Abs(bb.Min.Z)>0.001||System.Math.Abs(bb.Max.Z-h)>0.001)throw new System.Exception("LED_Z_FAIL "+name+" minZ="+bb.Min.Z+" maxZ="+bb.Max.Z+" expected=0.."+h);var id=rdoc.Objects.AddBrep(e.ToBrep(),A(name,li));if(id==System.Guid.Empty)throw new System.Exception("Extrusion add failed: "+name);System.Console.WriteLine("LED_Z_PASS "+name+" minZ="+bb.Min.Z+" maxZ="+bb.Max.Z);return id;};
int led=GL("VP04_LED_VOLUME",System.Drawing.Color.MediumPurple);int aux=GL("VP05_LED_AUX",System.Drawing.Color.Cyan);
double cx=-120,cy=0;
EX("LED_ACTIVE_WALL",led,RING(cx,cy,480,482),288);
EX("LED_REAR_SUPPORT",led,RING(cx,cy,482,500),312);
var service=ARC(cx,cy,572,false);rdoc.Objects.AddCurve(service,A("LED_SERVICE_CLEARANCE",led));
SB("LED_FLOOR_PROXY",aux,-360,120,-420,-60,0,2);
SB("LED_CEILING_ACTIVE",aux,-300,60,-240,0,288,290);
SB("LED_CEILING_SUPPORT",aux,-300,60,-240,0,290,306);
var talent=new Rhino.Geometry.PolylineCurve(new[]{new Rhino.Geometry.Point3d(-300,-360,0),new Rhino.Geometry.Point3d(60,-360,0),new Rhino.Geometry.Point3d(60,-120,0),new Rhino.Geometry.Point3d(-300,-120,0),new Rhino.Geometry.Point3d(-300,-360,0)});rdoc.Objects.AddCurve(talent,A("TALENT_ZONE",aux));
SB("CALIBRATION_STORAGE",aux,540,696,360,552,0,96);
rdoc.Views.Redraw();System.Console.WriteLine("PHASE02_CREATED active_radius=480 support_outer=500 service_radius=572 LED_Z_PASS active=0..288 support=0..312");
```

## Hard Scope Boundary

Do not use a faceted ring of boxes, disconnected square panels, or a thick
wall-block substitute. Do not create rooms, doors, rigging, cameras, furniture,
workstations, or equipment in Phase 2.

## Post-Phase Cleanup Checklist

- [ ] LED face is smooth, continuous, thin, and consistently curved
- [ ] Console contains `LED_Z_PASS` for both `LED_ACTIVE_WALL` and `LED_REAR_SUPPORT`; any negative Z is a hard failure
- [ ] Active radius is exactly 480 in and active height exactly 288 in
- [ ] Total LED bounds remain within X -692..452, Y 0..572, Z 0..312
- [ ] Six-foot rear service access is legible
- [ ] Central 50 ft x 40 ft shooting floor remains unobstructed
- [ ] LED ceiling is within its operating envelope

## REVIEW GATE 2 - LED Volume

Present a stage interior perspective and plan view. Ask vision specifically
about curvature, thickness, faceting, scale, shooting clearance, and service
access. Correct only identified defects.

## Checkpoint Save

Save `work/vp_studio_01_checkpoint_02_led.3dm`, then proceed to
`02c_phase_rooms_access.md`.
