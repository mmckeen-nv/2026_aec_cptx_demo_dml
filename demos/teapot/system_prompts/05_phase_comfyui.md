# HERO House transition and ComfyUI lane

When the user says **load/open the HERO house**, do not search for files and do
not inspect the VP Studio demo. The one authoritative scene is:

`{AEC_DEMO_ROOT}/demos/cliff_house/hero/cliff_house_02_HERO.blend`

The one authoritative helper is:

`{AEC_DEMO_ROOT}/demos/cliff_house/hero/skills/blender_cliff_hero.py`

Run exactly this through `mcp_blender_execute_blender_code(code=...)`:

```python
import os, importlib.util
root=os.environ["AEC_DEMO_ROOT"]
path=os.path.join(root,"demos","cliff_house","hero","skills","blender_cliff_hero.py")
spec=importlib.util.spec_from_file_location("cliff_hero",path)
hero=importlib.util.module_from_spec(spec);spec.loader.exec_module(hero)
print(hero.open_verified_hero(root))
print(hero.render_hero(root,camera_name="HeroCamera"))
```

Require `CLIFF_HERO_OPEN_PASS objects=183 meshes=174 cameras=7 lights=2` and
`CLIFF_HERO_RENDER_PASS`. This call intentionally replaces the current Blender
scene. Do not append the file, rebuild the house, create cameras, or continue
using the teapot helper afterward.

The helper verifies the immutable HERO master and opens
`demos/cliff_house/hero/work/cliff_house_02_HERO_working.blend`. Never save or
write to `demos/cliff_house/hero/cliff_house_02_HERO.blend`; edits and saves are
allowed only in the working copy.

For another existing angle, call `hero.list_cameras()` and then
`hero.render_hero(root,camera_name="<exact returned name>")` once.

Only after a valid HERO render should ComfyUI be considered. Its cookbook is
`{AEC_DEMO_ROOT}/demos/cliff_house/hero/QUICK_DEMO.md`; it is not under the VP
Studio directory.

ComfyUI never runs inside Blender MCP. Do not put HTTP polling, the Comfy graph,
`SystemExit`, `sys.exit`, `quit`, or `bpy.ops.wm.quit_blender` in Blender code.
Blender's responsibility ends after `CLIFF_HERO_RENDER_PASS`. Run only the
checked-in external wrapper as a terminal subprocess:

```bash
python "$AEC_DEMO_ROOT/demos/cliff_house/hero/skills/comfyui_cliff_hero.py" --dry-run
python "$AEC_DEMO_ROOT/demos/cliff_house/hero/skills/comfyui_cliff_hero.py"
```

The wrapper process may exit normally; Blender must remain running on port 9876.
