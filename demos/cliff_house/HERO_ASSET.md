# Verified Cliff House HERO asset

Hermes default asset key: `cliff-house-hero`

The operator-approved fast-demo master captured from the live Blender scene is:

`$AEC_DEMO_ROOT/demos/cliff_house/hero/cliff_house_QUICK_MASTER.blend`

Its SHA-256 is
`b62312601e6d0b1b448f8089984a7a527235c40f518d6d768ae1103d8716ba35`.

The quick master has 94 materialized meshes and nine verified finish
datablocks, including the coastal-cliff terrain and vertical wood facade
finish. The quick helper rejects the asset if any mesh is unassigned.
It contains 98 objects, 94 meshes, two cameras, two lights, and uses
`ocean_view`. The quick-demo trigger uses
`skills/blender_cliff_quick.py`, which makes and opens the disposable
`work/cliff_house_QUICK_working.blend`.

The operator-approved Rhino HERO model is:

`$AEC_DEMO_ROOT/demos/cliff_house/hero/cliff_house_HERO_RHINO_MODEL.3dm`

Its SHA-256 is
`029a9b8e338a12c3babef2a7a2c95f385475c0ffe09da8700fa8ade8ab2ea637`.
This is the current architectural Rhino HERO for later inspection and repair
demonstrations. It supersedes disposable Rhino working copies but does not
replace the verified Blender QUICK master used by the quick-render lane.
It contains 559 active Rhino objects and the operator-approved coordination
corrections: six front-balcony footings, the Level 3 roof slab, four roof
perimeter guards, the Level 3 terrace-edge closure, and nine tightened cable
rails on each front balcony. These are conceptual demonstration elements, not
a substitute for licensed structural or code review.

Any unqualified request for the "HERO model", "hero house", "prebuilt cliff
model", or "quick model" resolves to this QUICK master.

The older immutable seven-camera HERO master remains available for the
separate legacy HERO lane:

Hermes legacy asset key: `cliff-house-legacy-hero`. Use it only when the
operator explicitly asks for the legacy or seven-camera HERO.

The immutable, verified Blender master is:

`$AEC_DEMO_ROOT/demos/cliff_house/hero/cliff_house_02_HERO.blend`

Do not search archived runs for another model and do not overwrite this file.
Its SHA-256 is:

`d0756bfa299b89d51642bf5688eba875f68cf99a9a72978bc24fac1f23d4413a`

The verified scene contract is 183 objects, 174 meshes, seven cameras, two
lights, and a camera named `HeroCamera`.

For an editable copy, use the checked-in helper. It verifies the master,
creates `demos/cliff_house/hero/work/cliff_house_02_HERO_working.blend`, opens
that disposable copy, and audits the scene:

```python
import importlib.util
import os

root = os.environ["AEC_DEMO_ROOT"]
path = os.path.join(
    root, "demos", "cliff_house", "hero", "skills", "blender_cliff_hero.py"
)
spec = importlib.util.spec_from_file_location("cliff_hero", path)
hero = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hero)
print(hero.open_verified_hero(root))
```

Use `hero.list_cameras()` to inspect the seven verified cameras and
`hero.render_hero(root, camera_name="HeroCamera")` for the canonical source
render. This HERO asset is a fast Blender/ComfyUI reference lane; do not
silently substitute it for the fresh Rhino construction workflow.
