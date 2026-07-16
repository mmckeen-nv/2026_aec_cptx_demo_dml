# VP Studio Rhino construction contract

Hermes designs and models the studio in Rhino; there is no checked-in geometry
builder and no fixed target model to replay.

## Execution discipline

- Read the current phase prompt immediately before work.
- Read the locked template references silently before building.
- Read `prompts/01a_locked_scene_manifest.md` before geometry. Treat every
  scheduled coordinate, dimension, name, and envelope as immutable.
- Create one manifest-defined assembly per
  `mcp_rhino_run_csharp(script=...)` call using the exact helper implementation
  embedded in the current phase prompt. Python is read-only inspection/capture
  only; it is never a geometry mutation path.
  A call may create all named components of that assembly, but never geometry
  from a different phase. Use a few coherent assembly mutation calls per phase,
  followed by targeted corrections when inspection finds a real problem. Do
  not enforce a turn count; recover naturally as in the original Cliff House.
- Copy the phase C# scaffold literally. Replace only its scheduled call list
  when the prompt explicitly instructs you to do so. Never probe constructors,
  layer methods, return types, or object-table indexing.
- Never invoke interactive commands, Rhino's script editor, `_New`, `_SaveAs`,
  `_RunPythonScript`, document close/reopen, or slot lifecycle tools.
- Never write a complete phase or studio builder to disk and replay it.
- Never execute Python or C# through terminal, execute_code, Rhino commands,
  editors, or file associations. Once the first mutation of a phase begins,
  compose subsequent scripts inline in MCP calls; do not patch local scripts.
- Add required User Text as the object is created, using
  `Attributes.SetUserString(key, value)`.
- Always treat every `Objects.Add*` result as a `Guid`, never an integer ObjectTable
  index. Do not translate or move geometry after constructing it from absolute
  WorldXY intervals.

## Phase boundaries

The four Rhino phases are:

1. site and shell;
2. stage and smooth LED volume;
3. rooms, doors, loading, and circulation;
4. rigging, camera envelopes, lighting positions, and named equipment proxies.

## Shared C# prelude for Phases 2-4

Copy this block at the start of every Phase 2-4 mutation call. Do not shorten,
translate, or replace it.

```csharp
var rdoc=doc;
System.Func<string,System.Drawing.Color,int> GL=(name,color)=>{for(int i=0;i<rdoc.Layers.Count;i++){var l=rdoc.Layers[i];if(l!=null&&!l.IsDeleted&&l.Name==name)return i;}var n=new Rhino.DocObjects.Layer();n.Name=name;n.Color=color;int k=rdoc.Layers.Add(n);if(k<0)throw new System.Exception("Layer add failed: "+name);return k;};
System.Func<string,int,Rhino.DocObjects.ObjectAttributes> A=(name,li)=>{var a=new Rhino.DocObjects.ObjectAttributes();a.Name=name;a.LayerIndex=li;a.SetUserString("project","vp-studio-01");a.SetUserString("discipline","ARCHITECTURE");a.SetUserString("system","VP_STUDIO_PHYSICAL");a.SetUserString("agentic_phase","CURRENT_RHINO_PHASE");a.SetUserString("phase","SCHEMATIC");a.SetUserString("assumption_status","LOCKED_MANIFEST");a.SetUserString("source_basis","01a_locked_scene_manifest.md");a.SetUserString("export_to_blender","yes");return a;};
System.Func<string,int,double,double,double,double,double,double,System.Guid> SB=(name,li,x0,x1,y0,y1,z0,z1)=>{var b=new Rhino.Geometry.Box(Rhino.Geometry.Plane.WorldXY,new Rhino.Geometry.Interval(x0,x1),new Rhino.Geometry.Interval(y0,y1),new Rhino.Geometry.Interval(z0,z1));var id=rdoc.Objects.AddBrep(b.ToBrep(),A(name,li));if(id==System.Guid.Empty)throw new System.Exception("Box add failed: "+name);return id;};
```

The current phase explicitly excludes all later phases. If an object belongs to
a later phase, do not create it yet.

## Review and checkpoints

Save useful checkpoints only after the current phase passes both numeric and
visual review.

After each phase group, run one read-only MCP validator that prints document
units/tolerances, every new object's bounds, its manifest comparison, and the
literal token `NUMERIC_PASS`. Stop immediately on the first mismatch. Only after
that pass, capture one fresh Rhino viewport PNG and ask local Nemotron vision for
focused feedback. Make targeted corrections, re-run numeric
validation, and save with `mcp_rhino_save_doc`. Every physical object carries
`project=vp-studio-01` and the metadata required by the project prompt.

Do not model electrical, HVAC, data, fire-protection, or utility distribution.
After the physical model passes, write only `work/vp_studio_01_estimated_load.md`.
