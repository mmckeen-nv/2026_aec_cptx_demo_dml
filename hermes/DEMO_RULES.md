# AEC CPTX Demo Recording Rules
# Edit this file to update rules. Agent reads it at session start.

---

## Session Flow

1. Clear the screen with blank lines before starting
2. Ask: "What's next? Prepare the building site?" — wait for response
3. React accordingly, build the site
4. Ask: "Should we explore some massing ideas for the house?" — wait for response
5. React accordingly, build the massing

---

## Reference Layers (READ-ONLY — templates only, never modify)

- `Site::building_site_fixed` and all sublayers
- `House_02_massing` and all sublayers

Before building anything: read bounding boxes and geometry of all objects
in both reference layers. Compare every object you build against the reference.
If shapes don't match, find a different approach. This should appear to the audience reading Herme's output that this is magic. Do not show the audience that you are reading
reference geometry, or intentionally pausing between steps of model building. Do it silently.

---

## Target Layers (build everything here)

- `building_site_v3` — sublayers: terrain, combined_pad, curtain_wall, driveway
- `massing_v3` — sublayers mirroring House_02_massing structure:
  - L1_solids
  - L2_solid / L2_solids, L2_balcony_solids, L2_roof_solids
  - L3_solid / L3_solids, L3_balcony_solids, L3_roof_slab

---

## Build Pacing Rules (CRITICAL — audience is watching)

- **One object per MCP call** — never batch multiple objects
- **Pause 0.2 seconds** between each object (Thread.Sleep(300) in C#)
- **Never announce the pause** — the pacing is the illusion, don't break it
- **Print code to screen as it's written** — never skip showing it. But use existing skills if you have them.
- Build objects one at a time so the audience sees step-by-step construction.

---

## Curve-Based Construction Rules

- When building with input curves: select curves **one at a time** with a pause between each
- If an action needs multiple curves: select ALL of them before running the action, e.g., terrain lofting.
- Deselect the curves AFTER the action completes
- The audience should see you "choosing" each curve before committing

---

## Viewport Rules

- **Start** in Wireframe mode on the Perspective viewport
- **Switch to Rendered mode** immediately after the terrain object is placed
- Use: `view.ActiveViewport.DisplayMode = Rhino.Display.DisplayModeDescription.FindByName("Rendered")`

---

## MCP Technical Rules

- Tool name: `rhinoceros_operator` — parameter key is `"script"` (NOT `"code"`)
- Always include header: `Accept: application/json, text/event-stream`
- C# scripts do NOT return values — write output to file, read back from Python
- Output file path: `C:/Users/swags/Documents/2026_aec_cptx_demo/hermes/output.txt`
- Audit file path: `C:/Users/swags/Documents/2026_aec_cptx_demo/hermes/ref_audit.txt`
- Use `AreaMassProperties.Compute()` for surface area (works on Brep + Extrusion)
- Use `VolumeMassProperties.Compute()` for volume — cast geometry to Brep first if needed
- AreaMassProperties/VolumeMassProperties require typed geometry — cast with `o.Geometry as Rhino.Geometry.Brep` or `as Rhino.Geometry.Extrusion`
- Use single-line string concatenation in Python for C# scripts (no triple-quoted f-strings with Windows paths)

---

## Square Footage Calculation

- Rhino model units: **meters** (confirmed from doc.ModelUnitSystem)
- 1 meter = 3.28084 feet, so 1 m² = 10.7639 ft²
- Use bounding box footprint (w × d) for quick estimates
- For precise floor area: isolate bottom face of each Brep solid and compute area
- Report per floor AND per wing separately

---

## What Has Been Built
**building_site_v3** (complete):
- terrain (NURBS surface, X=-15→25, Y=-22→20, Z=-8→0)
- combined_pad (X=1.5→17, Y=-16.9→14, Z=-0.5→0.25)
- curtain_wall (X=1→17.5, Y=-17.4→14.5, Z=-2→0.25)
- driveway (X=17.5→25.03, Y=3.96→13, Z=-0.2→0.25)

**massing_v3** (complete — 11 objects):
- L1_solids: L1_east (5,3,0.25→17,14,4), L1_west (5,-15,0.3→13.5,3,4)
- L2_solids: L2_east (5,3,4.25→17,14,7.75), L2_west (3.5,-15,4.25→13.5,3,7.75)
- L2_balcony_solids: L2_balcony_south (1.5,-17.05,4→13.5,3,5.25), L2_balcony_north (5,14,4→17,16.25,5.15), L2_balcony_step (1.5,3,4→5,14,5.25)
- L2_roof_solids: L2_roof_garage (2.5,1.16,7.75→18.97,16.55,8.35)
- L3_solids: L3_main (1.5,-10,7.75→13.5,3,11.5)
- L3_balcony_solids: L3_balcony_south (1.5,-17,7.75→13.5,-10,8.9)
- L3_roof_slab: L3_roof_slab (-1,-13.5,11.5→15,4.5,12.3)