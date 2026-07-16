# Phase 3 - Open Material Interactions

## Purpose

Let the audience direct fast, visible Blender changes without disturbing the
validated geometry or restarting the pipeline.

## Interaction Contract

Interpret ordinary requests naturally. For a recognized look, load the helper
and call `apply_material(style)`. Tested styles are:

- `glazed_ceramic`
- `copper`
- `brushed_steel`
- `chrome`
- `glass`
- `matte_black`
- `white_porcelain`

Friendly aliases such as “brass-like,” “shiny metal,” “black,” or “ceramic”
may map to the closest preset. If the user names a color, call
`apply_custom_material(name, rgba, metallic, roughness, transmission)` with
bounded Principled values. Do not claim a preset exists when it does not.

## Required call shape

```python
import os, importlib.util
root=os.environ["AEC_DEMO_ROOT"]
path=os.path.join(root,"demos","teapot","skills","blender_teapot_interactions.py")
spec=importlib.util.spec_from_file_location("teapot_demo",path)
tp=importlib.util.module_from_spec(spec);spec.loader.exec_module(tp)
print(tp.apply_material("copper"))
print(tp.render_preview(root, filename="teapot_copper.png"))
```

## Open-Ended Requests

The user may ask for another material, a small camera orbit, warmer/cooler
lighting, or a fresh preview. Use the helper's bounded functions and preserve
the teapot collection. Ask before changing more than one presentation dimension
at once. A simple material request never triggers Rhino, reimport, DML ceremony,
ComfyUI, or a full pipeline replay.

## Explicit HERO House Transition

If the user explicitly asks to load or open the HERO house, stop the teapot
interaction loop and read `../system_prompts/05_phase_comfyui.md`. Use its exact
checked-in helper call. The HERO scene is not an asset to discover: it is always
`{AEC_DEMO_ROOT}/demos/cliff_house/hero/cliff_house_02_HERO.blend`. Do not search
the VP Studio tree or ask the user where the file is.

## REVIEW GATE 3 - Audience Choice

Show the requested preview, name the applied material, and remain ready for the
next interaction. Save `blender_assets/teapot_interactive.blend` only when the
user asks to keep the current look or ends the demo.
