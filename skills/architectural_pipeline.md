# Architectural Pipeline — Operating Manual

This is Claude's reference for working an architectural project from Rhino source
through Blender render. Read this FIRST when picking up an aec_demo_master-style project.

---

## Operating principles (non-negotiable)

1. **I do the work.** When I find a problem, I fix it. I don't report it and wait
   for permission for each fix. Permission is at the *direction* level (what to
   build, what style); execution is mine.

2. **Derive, don't redraw.** Every vertex of new geometry must come from snapping
   to existing curves, edges, or points of the prototype. Eyeballed positions
   are how coplanar bugs get baked in. If I can't derive it, I haven't earned
   the right to place it.

3. **Prototype first, then rebuild clean.** The .3dm import is the *prototype* —
   it captures the design intent but has construction artifacts (duplicates,
   coplanar faces, misaligned edges). I treat it as reference geometry, build
   clean replacements derived from its edges/curves, then replace the prototype.

4. **Validate at every stage.** Coplanar detector runs after import and after
   every batch of geometry edits. Refuse to proceed to materials/lighting/render
   if validation fails.

5. **Metadata propagates.** Rhino object names and User Text encode material
   and architectural role. These survive import as Blender custom properties
   and drive material decisions. Don't guess what an object should look like
   if the metadata tells me.

---

## The pipeline

```
.3dm source
    |
    v
[1] Read with rhino3dm, extract per-object metadata (name, User Text, layer)
    |
    v
[2] Audit: coplanar pairs in source mesh tessellation, duplicate Breps,
    open polysurfaces. Output: prioritized issue list.
    |
    v
[3] Decide per issue: fix in Rhino (need user) or fix in Blender (I do it).
    Heuristic: layout/intent changes -> Rhino. Coplanar offsets,
    duplicate removal, geometry derivation from edges -> Blender.
    |
    v
[4] Import to Blender:
    - Layer hierarchy -> collections
    - Per-object Rhino visibility -> hide_viewport (rendered visibility
      synced via persistent handler)
    - Per-object User Text -> Blender custom properties
    - No materials baked yet (assigned in step 6)
    |
    v
[5] Validate import: re-run coplanar detector, check duplicates.
    Apply fixes (delete duplicates, shrink/offset coplanar geometry).
    Re-validate until clean.
    |
    v
[6] Materials by collection, driven by metadata:
    - read custom prop 'material' or fall back to name parsing
    - read custom prop 'tile_scale_m', 'finish', 'color_hint'
    - generate Blender material with procedural or PolyHaven texture
    |
    v
[7] Lighting (HDRI), camera animation, render
```

---

## Metadata conventions (Rhino User Text -> Blender custom properties)

| Key | Type | Example | Used for |
|---|---|---|---|
| `material` | string | `gray_slate_flagstone` | primary material identifier |
| `material_description` | string | `Gray slate, 15% gloss, weathered` | human-readable, guides texture choice |
| `tile_scale_m` | float | `1.0` | meters per texture tile/repeat |
| `finish` | string | `polished` / `matte` / `weathered` | drives roughness |
| `color_hint` | string | `warm_gray` / `dark_charcoal` | drives tint |
| `architectural_role` | string | `patio_floor` / `wall_finish` / `structural_slab` | semantic class |
| `is_finish` | bool | `true` | finish layer (decorative), should be offset 5-25mm from substrate |
| `is_glazing` | bool | `true` | glass, must not be coplanar with frame |

When metadata is missing, fall back to parsing the object name. E.g.,
`wall_L1_north_stone` -> material=stone, architectural_role=wall,
floor=L1, orientation=north.

---

## Decision tree: where does a fix happen?

| Issue | Where to fix | Why |
|---|---|---|
| Duplicate Brep / mesh | Blender (delete one) | Trivial, no design impact |
| Coplanar faces from "double-modeled" element (ceiling_L1 + slab_L2) | Blender (hide one, prefer the structural one) | Cosmetic only — both objects exist for material reasons |
| Coplanar wall corner outer faces | Blender (shrink one's vertex coords inward 5mm) | Sub-pixel at any render distance |
| Finish flush with substrate (stone facing on concrete) | Blender (offset finish by 25mm) | Stays architecturally correct |
| Edge misalignment ("lump" in parapet) | Identify which piece, re-derive from neighboring clean edges | Geometry-derivation fix |
| Wrong topology / design change needed | Flag for Rhino fix (user) | Out of scope for post-import |

---

## Files in skills/

| File | Purpose |
|---|---|
|| `architectural_pipeline.md` | This doc |
|| `rhino_modeling.md` | Modeling discipline (for the human modeler) |
|| `rhino_prep.md` | Pre-export checklist |
| `audit_active_document.py` | In-Rhino audit; coplanar/duplicates/metadata/open-solids |
| `pre_export_validate.py` | In-Rhino final gate; refuses export if critical issues remain |
| `coplanar_detector.py` | Scene-level z-fight finder (Blender) |
| `import_with_metadata.py` | Validated importer that extracts User Text |
| `validate_blender_scene.py` | Post-import gate |
| `derive_geometry.py` | Helpers for deriving new geometry from existing curves/edges |
