# HERO House transition and ComfyUI lane

When the user says **load/open the HERO house**, do not search for files and do
not inspect the VP Studio demo. The one authoritative scene is:

`{AEC_DEMO_ROOT}/demos/teapot/hero/BAC_TEAPOT_HERO.blend`

The one authoritative helper is:

`{AEC_DEMO_ROOT}/demos/teapot/skills/blender_bac_hero.py`

Run exactly this through `mcp_blender_execute_blender_code(code=...)`:

```python
import os, importlib.util
root=os.environ["AEC_DEMO_ROOT"]
path=os.path.join(root,"demos","teapot","skills","blender_bac_hero.py")
spec=importlib.util.spec_from_file_location("bac_hero",path)
hero=importlib.util.module_from_spec(spec);spec.loader.exec_module(hero)
print(hero.open_verified_hero(root))
print(hero.render_hero(root,camera_name="Camera_day"))
```

Require `BAC_HERO_OPEN_PASS objects=506 meshes=257 cameras=6 lights=1` and
`BAC_HERO_RENDER_PASS`. This call intentionally replaces the current Blender
scene. Do not append the file, rebuild the house, create cameras, or continue
using the teapot helper afterward.

The helper verifies the immutable HERO master and opens
`demos/teapot/hero/work/BAC_TEAPOT_HERO_working.blend`. Never save or
write to `demos/teapot/hero/BAC_TEAPOT_HERO.blend`; edits and saves are
allowed only in the working copy.

For another existing angle, call `hero.list_cameras()` and then
`hero.render_hero(root,camera_name="<exact returned name>")` once.

Only after a valid HERO render should ComfyUI be considered. This prompt is the
authoritative BAC HERO cookbook; do not substitute the Cliff House or VP source.

ComfyUI never runs inside Blender MCP. Do not put HTTP polling, the Comfy graph,
`SystemExit`, `sys.exit`, `quit`, or `bpy.ops.wm.quit_blender` in Blender code.
Blender's responsibility ends after `BAC_HERO_RENDER_PASS`. Run only the
checked-in external wrapper as a terminal subprocess:

```bash
python "$AEC_DEMO_ROOT/demos/teapot/skills/comfyui_bac_hero.py" --dry-run
python "$AEC_DEMO_ROOT/demos/teapot/skills/comfyui_bac_hero.py"
```

The wrapper process may exit normally; Blender must remain running on port 9876.
It uses the approved SDXL depth stage followed by FLUX.2 Klein reference
refinement. Require `COMFY_SDXL_OUTPUT_PASS`, `COMFY_FLUX_OUTPUT_PASS`, and
`COMFY_OUTPUT_PASS stage=sdxl+flux`; the final artifact is
`demos/teapot/hero/comfy_output/bac_teapot_hero_stylized.png`.
