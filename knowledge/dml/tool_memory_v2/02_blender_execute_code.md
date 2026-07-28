# Verified Blender MCP batch call

status: SUCCESS_VALIDATED
memory_class: procedural_tool_call
retrieval_tags: successful Blender MCP execute code import material camera render repair
memory_summary: SUCCESS: call mcp__blender__execute_blender_code with {"code":"<one self-contained Python batch>"}. Import/validate/clean/material/camera/render/save in one call and return compact PASS JSON. Blender 5.2 uses BLENDER_EEVEE and SINGLE_SCATTERING; set shape/size only for AREA lights, never SUN lights.

Use `mcp__blender__execute_blender_code` with exactly:

```json
{"code":"<one self-contained Python batch>"}
```

In one batch: import the validated mesh bridge, assert object count and
transform parity, run checked-in cleanup scripts, assign materials, create
lights/camera, render, save, and print one compact JSON receipt. Use absolute
paths or resolve scripts after setting the repository working directory.

Validated Blender 5.2 constraints:

```python
scene.render.engine = "BLENDER_EEVEE"  # not BLENDER_EEVEE_NEXT
sky.sky_type = "SINGLE_SCATTERING"

def add_light(name, kind, location, energy, color, size=None):
    data = bpy.data.lights.new(name, kind)
    data.energy, data.color = energy, color
    if kind == "AREA" and size is not None:
        data.shape, data.size = "DISK", size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    return obj
```

Do not set `.shape` or `.size` on a SUN light. That exact mistake failed with
`'SunLight' object has no attribute 'shape'`; the conditional AREA-only helper
then succeeded. Do not probe compositor node types or GPU devices during the
run. Success requires the MCP response status `success` plus the batch’s compact
PASS receipt.
