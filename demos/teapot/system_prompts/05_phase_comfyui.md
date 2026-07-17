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
print(hero.open_verified_hero(root, reset=True))
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

After this base render, run the checked-in Comfy wrapper once, report the base
artifact, and **STOP**. Do not add any pool asset until the user asks.

## STOP GATE A - Floaties only

Release this stage only after a new user turn explicitly asks to **add the
floaties**, float ring, or flamingo. Do not interpret the earlier request to
open/render the HERO house as authorization. Reload the helper and run exactly:

```python
import os, importlib.util
root=os.environ["AEC_DEMO_ROOT"]
path=os.path.join(root,"demos","teapot","skills","blender_bac_hero.py")
spec=importlib.util.spec_from_file_location("bac_hero",path)
hero=importlib.util.module_from_spec(spec);spec.loader.exec_module(hero)
print(hero.add_pool_floaties(root, reset=True))
print(hero.render_hero(root,camera_name="Cam_Shot_A",filename="bac_teapot_pool_floaties.png"))
```

Require `BAC_POOL_FLOATIES_PASS floats=2 chairs=0 furniture=0` followed by
`BAC_HERO_RENDER_PASS camera=Cam_Shot_A stage=floaties`. Run the Comfy wrapper;
it automatically selects the floaties-only prompt and unique output names.
Report that artifact and **STOP**. Do not add chairs or furniture in this turn.

The helper locks the float ring and flamingo inside the measured pool water at
numerical X `-0.006503..-0.002648`, Y `-0.011500..0.001001`, Z approximately
`0.00050`. It applies the required 1:1000 conversion and verifies both hashes.

## STOP GATE B - Other pool assets

Release this stage only after a later, separate user turn explicitly asks to
**add the other pool assets**, chairs, loungers, or outdoor furniture. The
validated floaties collection must already exist. Run exactly:

```python
import os, importlib.util
root=os.environ["AEC_DEMO_ROOT"]
path=os.path.join(root,"demos","teapot","skills","blender_bac_hero.py")
spec=importlib.util.spec_from_file_location("bac_hero",path)
hero=importlib.util.module_from_spec(spec);spec.loader.exec_module(hero)
print(hero.add_pool_furniture(root))
print(hero.render_hero(root,camera_name="Cam_Shot_A",filename="bac_teapot_pool_complete.png"))
```

Require `BAC_POOL_FURNITURE_PASS floats=2 chairs=3 furniture=1` followed by
`BAC_HERO_RENDER_PASS camera=Cam_Shot_A stage=complete`. This stage adds only:

- three normal-size beach loungers: east pool deck, facing the water and clear
  of its edge;
- `OutdoorFurniture1`: north patio near the pool, outside both water and the
  lounger lane.

Never call `add_pool_floaties` and `add_pool_furniture` in one turn. Never call
the disabled `add_pool_assets` all-at-once function. Only the helper may apply
source coordinates, hashes, unit conversion, placement, or scale.

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

The wrapper reads the third line of the render-lane marker (`base`, `floaties`,
or `complete`) and selects a stage-specific editable prompt and output filename.
The process may exit normally; Blender must remain running on port 9876.
It uses the approved SDXL depth stage followed by FLUX.2 Klein reference
refinement. Require `COMFY_SDXL_OUTPUT_PASS`, `COMFY_FLUX_OUTPUT_PASS`, and
`COMFY_DESKTOP_OUTPUT_PASS` before `COMFY_OUTPUT_PASS stage=sdxl+flux`. The
shared helper copies accepted outputs to `Desktop/comfyui outputs`. Never reuse a previous stage's image as the
current result.
