# VP Studio Rhino starting template

`vp_studio_01_template.3dm` is the required starting document for an agent run.
It is modeled in inches with 0.01-inch absolute tolerance and contains only
locked reference curves and text dots:

- 400 ft x 300 ft property boundary;
- movable 180 ft x 150 ft building and 120 ft x 100 ft stage scale envelopes;
- origin, north, ground, 40 ft clear-height, and 52.5 ft expected-maximum datums;
- 1 ft, 10 ft, and 100 ft scale bars.

It contains no Breps, Extrusions, Meshes, architectural massing, rooms, LED
geometry, rigging, equipment, or accepted design solution. Objects on
`VP00_TEMPLATE_*` layers have `export_to_blender=false` and are reference-only.

The older `../vp_studio_01_base_model.3dm` is a completed reference artifact in
meters. It is not the agent starting document and must never be used as evidence
of agent-authored work.

Regenerate the datum template with:

```powershell
py -3.12 tools/create_vp_studio_template.py
```
