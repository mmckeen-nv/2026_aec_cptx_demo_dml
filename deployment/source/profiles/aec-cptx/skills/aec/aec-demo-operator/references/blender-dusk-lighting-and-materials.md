# Blender Dusk Lighting & Material Refinement

Techniques discovered during cliff_house_02 Phase 5-6 (June 15 2026).

## Interior Glow Planes (dusk atmosphere)

Section 10 of project briefs often calls for "warm amber glow from inside, suggests the house is occupied and welcoming at dusk." This requires interior emission planes behind each glazed facade.

### Technique

Create flat `bmesh.ops.create_grid` planes with an Emission shader:
- Color: `(1.0, 0.65, 0.25)` — warm amber
- Strength: 8.0 (start at 3.0, usually needs boosting to 8-10)
- One plane per floor per glazed facade (e.g., L1/L2/L3 × west/south = 6 planes)
- Scale to match the glazed area of each facade

### Positioning (critical)

Place planes **at least 1.5m behind the glass line** (measured inward from facade). If positioned too close to the glass:
- They render as bright white bars mounted ON the facade surface
- They look like LED strips rather than ambient interior glow
- The glass doesn't have enough depth between itself and the emitter for realistic light scattering

Example for a west-facing glass wall at X=1.5m:
```python
glow_plane.location.x = 3.5  # 2m behind glass line
```

### Collection organization

Place all glow planes in a dedicated `Interior` collection. They should be separate from the building geometry collections (Site, Building, Glazing, etc.) so they can be toggled independently for test renders.

### Emission material setup

```python
def make_emission(name, color=(1.0, 0.65, 0.25), strength=8.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    output = nodes.new('ShaderNodeOutputMaterial')
    emit = nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = (*color, 1.0)
    emit.inputs['Strength'].default_value = strength
    links.new(emit.outputs['Emission'], output.inputs['Surface'])
    return mat
```

## Material Palette — Read Section 8 First

The skill reference `blender-export-and-setup.md` has a default Cycles palette, but the **actual project brief (Section 8)** may specify different materials. Always read Section 8 before building materials.

### cliff_house_02 Section 8 differences from defaults

| Tag | Default (skill ref) | Actual (Section 8) | Key difference |
|-----|--------------------|--------------------|----------------|
| M_Concrete_WarmBone | (0.88, 0.85, 0.80) warm beige | (0.92, 0.90, 0.87) off-white | Section 8: "white ashlar stone" not warm bone |
| M_Stone_Fieldstone | (0.5, 0.47, 0.42) mid-grey | (0.25, 0.23, 0.20) dark charcoal | Section 8: "dark charcoal" stone platform |
| M_Aluminum_Bronze | (0.65, 0.50, 0.35) R=0.2 | (0.55, 0.40, 0.25) R=0.18 M=1.0 | Fully metallic, more polished |

### Workflow: always rebuild from Section 8

1. Read Section 8 of project_prompt.md (grep for "SECTION 8" + read ~30 lines)
2. Map each brief description to PBR parameters (color, roughness, metallic)
3. Delete all existing materials and rebuild fresh — don't try to patch existing ones
4. Reassign by `obj.get("material")` custom property tag (set in Phase 4 export tagging)
5. Zero fallbacks expected if Phase 4 tagging was done correctly

## OBJ Import → Material Separation Workflow

When importing OBJ with `usemtl` groups, Blender creates one merged mesh with material slots. The full separation workflow:

1. **Replace .001 materials:** OBJ import creates duplicates (e.g., `M_Aluminum_Bronze.001`) when materials of the same name already exist. Iterate `material_slots`, match `base_name = name[:-4]`, replace with the PBR version.
2. **Separate by material:** `bpy.ops.mesh.separate(type='MATERIAL')` — creates one object per material slot.
3. **Rename objects:** Map material name → descriptive name (e.g., `M_Concrete_WarmBone` → `building_concrete`).
4. **Set rotation_mode:** `obj.rotation_mode = 'XYZ'` on all mesh objects immediately.
5. **Set custom properties:** `obj["material"] = mat_name` for downstream phase use.
6. **Organize collections:** Create collection per category, unlink from Scene Collection, link to target collection.

## HDRI-only Lighting (no sun lamp)

Phase 7 prompt requires HDRI-only lighting (sun lamps permanently hidden). When no HDRI file exists in `[project]/hdr/`, use Hosek/Wilkie procedural sky as substitute:

```python
sky = nt.nodes.new('ShaderNodeTexSky')
sky.sky_type = 'HOSEK_WILKIE'
sky.turbidity = 6.0           # 6-8 for golden hour dusty atmosphere
sky.sun_direction = (-0.85, -0.4, 0.12)  # Low SW, just above horizon
```

With sky-only lighting (no sun lamp), boost the fill light:
- Area fill energy: 150 (default 80 is too dim without sun)
- Background strength: 1.8 (default 1.0 underexposes)
- Film exposure: 1.3

The sun lamp should be hidden in a `__hidden__` collection with `exclude=True` on the view layer, not deleted — preserves the option to re-enable if HDRI is added later.
