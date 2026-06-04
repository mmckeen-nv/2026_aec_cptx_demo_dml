# Appendix -- Segmentation Colour Palette
# system_prompts/APPENDIX_segmentation.md
# Single source of truth. Do not duplicate elsewhere.
# Last updated: May 2026

Use this palette consistently across ALL projects.
Changing it breaks compatibility with previously labelled datasets.

---

## Palette

The `material_index` column lists the User Text tag values from Rhino
(set in APPENDIX_materials.md) that map to each segmentation category.
These tags carry through from Rhino → Blender → ComfyUI.

| Category                    | material_index values                              | RGB (0-255)    | Hex     |
|-----------------------------|----------------------------------------------------|----------------|---------|
| Walls / balconies / posts   | wall_primary, wall_secondary                       | 204, 30, 30    | #CC1E1E |
| Glass / windows / doors     | glazing, entry_door                                | 25, 204, 229   | #19CCE5 |
| Roof                        | roof                                               | 25, 25, 217    | #1919D9 |
| Floor slabs / soffits       | floor_slab                                         | 229, 140, 25   | #E58C19 |
| Frames / mullions / rails   | frame, railing                                     | 153, 153, 153  | #999999 |
| Terrain / grass             | terrain                                            | 20, 115, 20    | #147314 |
| Steps / foundation          | foundation                                         | 89, 51, 20     | #593314 |
| Driveway / paths            | driveway                                           | 51, 51, 51     | #333333 |
| Patio / outdoor surfaces    | patio, water, outdoor_furniture                    | 102, 102, 102  | #666666 |
| Garage doors                | garage_door                                        | 204, 30, 30    | #CC1E1E |

Note: garage_door shares the Walls colour — acceptable for training data
purposes. Add a new palette entry if per-project separation is needed.

---

## Render settings for segmentation (critical)

ALL of these must be set before rendering. Missing any one will contaminate the output.

```python
scene.cycles.samples              = 1
scene.cycles.max_bounces          = 0   # must be 0
scene.cycles.diffuse_bounces      = 0   # must be 0
scene.cycles.glossy_bounces       = 0   # must be 0
scene.cycles.transmission_bounces = 0   # must be 0
scene.cycles.volume_bounces       = 0   # must be 0
scene.cycles.use_denoising        = False

bg.inputs["Strength"].default_value = 0.0   # world = pure black
scene.render.film_transparent       = True  # transparent BG = black in PNG
scene.render.image_settings.color_mode  = 'RGB'
scene.render.image_settings.color_depth = '8'
```

---

## Flat emission material

```python
def seg_mat(name, r, g, b):
    m = bpy.data.materials.new(f"_Seg_{name}")
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    emit = nt.nodes.new("ShaderNodeEmission")
    out  = nt.nodes.new("ShaderNodeOutputMaterial")
    emit.inputs["Color"].default_value    = (r/255, g/255, b/255, 1.0)
    emit.inputs["Strength"].default_value = 1.0
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    return m
```

Full implementation: `skills/depth_and_segmentation.md`
