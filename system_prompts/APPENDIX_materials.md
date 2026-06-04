# Appendix — Sample Material Palette
# system_prompts/APPENDIX_materials.md
# Single source of truth for material index names and default values.
# Last updated: May 2026

---

## How This Works

Every object in the pipeline carries a `material_index` User Text tag set in
Rhino. This tag is the authoritative name for that object's material — it
carries through from Rhino → Blender → ComfyUI and any other pipeline
components. Material appearance (colour, roughness, metallic, transmission)
is defined here and in project_prompt.md Section 8.

**Rule:** project_prompt.md Section 8 always overrides this appendix.
References supplied by the user always override project_prompt.md.
This appendix provides sensible defaults when no override is specified.

---

## Sample Palette

These are example starting values — they will be updated during the user
interview and by any reference materials supplied. They represent a
contemporary residential building. Adapt freely to the specified project.

| Material index name  | Typical use                                  | Base colour (linear)    | R    | M    |
|----------------------|----------------------------------------------|-------------------------|------|------|
| wall_primary         | primary exterior wall surface                | 0.75, 0.75, 0.73        | 0.88 | 0.0  |
| wall_secondary       | secondary or accent wall surface             | 0.15, 0.15, 0.16        | 0.75 | 0.0  |
| roof                 | roof surface (style-dependent — see below)   | 0.12, 0.12, 0.14        | 0.65 | 0.0  |
| glazing              | windows, glazed doors, curtain wall panels   | 0.80, 0.85, 0.80        | 0.0  | 0.0  |
| frame                | window/door frames, mullions                 | 0.18, 0.18, 0.18        | 0.40 | 0.60 |
| floor_slab           | exposed floor slab edges, soffits            | 0.40, 0.40, 0.40        | 0.80 | 0.0  |
| foundation           | foundation, plinth, retaining walls          | 0.08, 0.08, 0.09        | 0.70 | 0.0  |
| entry_door           | front door                                   | 0.10, 0.07, 0.03        | 0.65 | 0.0  |
| garage_door          | garage door panels                           | 0.55, 0.55, 0.55        | 0.50 | 0.10 |
| driveway             | driveway, paths, steps                       | 0.25, 0.25, 0.25        | 0.90 | 0.0  |
| patio                | outdoor paving, terrace, deck                | 0.50, 0.50, 0.48        | 0.88 | 0.0  |
| railing              | balcony and stair railings, cable, glass     | 0.12, 0.12, 0.12        | 0.35 | 0.85 |
| terrain              | ground surface, lawn, planted areas          | 0.00375, 0.010, 0.00375 | 0.92 | 0.0  |
| water                | pool, pond, water feature                    | 0.05, 0.12, 0.18        | 0.05 | 0.0  |
| outdoor_furniture    | chairs, tables, planters                     | 0.05, 0.05, 0.05        | 0.60 | 0.80 |

R = Roughness, M = Metallic

Additional material index names should be added to project_prompt.md Section 8
as the design develops. Any name used on an object must appear in the index.

---

## Glass Setup (Blender 5.x)

```python
b.inputs["Transmission Weight"].default_value = 0.90  # adjust per brief
b.inputs["Roughness"].default_value = 0.0
```

For lightly tinted glass: Transmission ~0.92–0.97, subtle base colour tint.
For heavily tinted or privacy glass: Transmission ~0.40–0.60.
Note: input name may differ by Blender version. Check with:
`[i.name for i in b.inputs]`

---

## Roof Material by Style

The `roof` material index applies to the roof surface regardless of style.
Adjust base colour and roughness to match the specified roofing material:

| Roof style / material | Base colour (linear) | R    | M    |
|-----------------------|----------------------|------|------|
| Flat white parapet    | 0.85, 0.85, 0.83     | 0.90 | 0.0  |
| Dark metal standing seam | 0.06, 0.08, 0.10  | 0.55 | 0.55 |
| Clay/terracotta tile  | 0.35, 0.14, 0.06     | 0.85 | 0.0  |
| Slate grey            | 0.12, 0.12, 0.13     | 0.75 | 0.0  |
| Weathered cedar shingle | 0.28, 0.22, 0.14  | 0.88 | 0.0  |
| Green / living roof   | 0.04, 0.09, 0.02     | 0.92 | 0.0  |
| Concrete flat         | 0.40, 0.40, 0.40     | 0.80 | 0.0  |

---

## Name-Driven Assignment Pattern

This pattern is universal — it applies in Rhino (User Text tags), Blender
(material assignment), and ComfyUI (segmentation masks). The material_index
name is the single shared key across all pipeline stages.

```python
# Blender — assign materials by material_index custom property
for obj in bpy.data.objects:
    idx = obj.get("material_index", "")
    if not idx:
        # Fall back to name-based inference if tag is missing
        n = obj.name.lower()
        if   "wall" in n:                          idx = "wall_primary"
        elif "roof" in n or "parapet" in n:        idx = "roof"
        elif "glass" in n or "glaz" in n:          idx = "glazing"
        elif "mullion" in n or "frame" in n:       idx = "frame"
        elif "door" in n and "garage" in n:        idx = "garage_door"
        elif "door" in n:                          idx = "entry_door"
        elif "slab" in n or "soffit" in n:         idx = "floor_slab"
        elif "found" in n or "plinth" in n:        idx = "foundation"
        elif "drive" in n or "path" in n:          idx = "driveway"
        elif "patio" in n or "deck" in n:          idx = "patio"
        elif "rail" in n or "cable" in n:          idx = "railing"
        elif "terrain" in n or "grass" in n:       idx = "terrain"
        elif "pool" in n or "water" in n:          idx = "water"
        elif "chair" in n or "table" in n:         idx = "outdoor_furniture"
        else:                                      idx = "wall_primary"
    assign(obj, palette[idx])
```

```python
# ComfyUI segmentation — same index names map to fixed palette colours
# Defined in APPENDIX_segmentation.md — index names must match exactly.
```

**Pitfall:** If an object has no `material_index` tag and its name doesn't
match any pattern, it falls through to `wall_primary`. Always set the tag
at object creation time in Rhino to avoid silent mis-assignment.

---

## Render Quality Tiers

| Level       | Resolution  | Samples | Use                     |
|-------------|-------------|---------|-------------------------|
| Quick check | 640x360     | 64      | Single frame spot check |
| Test        | 960x540     | 128     | Full animation review   |
| Final       | 1920x1080   | 384     | Delivery                |
