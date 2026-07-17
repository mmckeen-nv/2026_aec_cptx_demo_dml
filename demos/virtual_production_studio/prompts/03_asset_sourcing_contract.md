# Blender asset pass

Rhino owns architecture, clearances, camera envelopes, and named equipment
proxies. Blender replaces the visible proxies with approved detailed assets.

## Use the local cache first

Read `assets/asset_manifest.yaml` and `assets/cache/cache_index.json`. The
checked-in index is authoritative, but payloads may live in either of these
locations, in this order:

1. `<AEC_DEMO_ROOT>/demos/virtual_production_studio/assets/cache`
2. `G:\AEC-CPTX\demos\virtual_production_studio\assets\cache`

Load `<AEC_DEMO_ROOT>/skills/blender_vp_production.py` through Blender MCP and
call `place_cached_asset(root, asset_key, proxy_name)`. Do not hand-build cache
paths, call a download prompt, use network asset tools, or create procedural
stand-ins when an approved cached payload resolves. Do not rewrite the helper.
The stage-wide beauty must read as an active production environment, not an
empty architectural shell. Required set dressing is deterministic and must be
placed as one checked-in batch before materials, lighting, or camera work.

Start with these known cached keys and named Rhino proxies:

- three `camera_tripod_silver_key` camera/tripod assemblies
- eight `chair_director_creativejenna` production and review chairs
- six `control_monitor_datsketch` workstation monitors
- six `roadcase_thomas_kole` road cases, including two stage hero cases
- two complete `light_led_soft_panel_roy` practical floor-light assemblies
- two `control_server_rack_anais` control-room racks

The three physical camera assets are deliberately separated across the south
side of the stage at `(-480,-420)`, `(120,-540)`, and `(600,-420)` inches. The
placement helper ignores stale clustered camera proxy coordinates, uses these
locked marks, and rotates each cached camera around Z so its lens points toward
the LED performance target `(-120,60,72)`. None may sit on the beauty-camera
sightline at `(0,-840)`.

All eight required chairs must remain present: six review chairs and two stage
director chairs. A passing set-dressing receipt also requires six workstation
monitors, six road cases, two practical lights, and two server racks; camera
placement alone never satisfies the scene-dressing gate.

Run exactly `vp.apply_required_set_dressing(root)`. It replaces the 27 locked
Rhino proxies and must print:

```text
VP_SET_DRESSING_CLEARANCE_PASS overlaps=0 protected_zones=4
VP_SET_DRESSING_PASS categories=6 placements=27 cameras=3 chairs=8 monitors=6 roadcases=6 practical_lights=2 racks=2
```

Each repeated asset is imported once into an unlinked source collection; the
27 visible placements are lightweight collection instances. A full GLB import
per chair, camera, monitor, or case is a failure because it needlessly expands
the scene and can destabilize Blender.

This is one bounded deployment attempt. If it reports a missing cache payload,
fixed-placement size failure, or `VP_SET_DRESSING_FAIL`, stop the asset phase and
report that concrete blocker. Do not retry the same call, monkey-patch the
helper, rewrite files, hand-scale assets, or substitute a different importer.

The standalone `grip_c_stand_kilianpohl` asset is prohibited in the beauty
scene. A visible stand must carry a fixture; the two required floor practicals
use the complete LED soft-panel assembly. Do not leave a bare C-stand visible.

The helper owns scale and grounding. Never calculate scale from proxy bounds,
call `fit_to_proxy`, rotate axes, or guess an asset's native units. These fixed
post-import dimensions are mandatory (X x Y x Z, inches):

- cinema tripod: `48 x 48 x 72`, grounded at world floor
- director chair: `24 x 24 x 42`, grounded at proxy floor
- workstation monitor: `6 x 24 x 18`, placed on proxy top
- road case: `48 x 24 x 30`, grounded at proxy floor
- C-stand: `36 x 36 x 84`, grounded at proxy floor
- LED soft-panel stand: `24 x 24 x 72`, grounded at proxy floor
- server rack: `24 x 42 x 84`, grounded at proxy floor

`apply_required_set_dressing` first restores any omitted locked proxy as an
internal, deterministic recovery anchor at the exact manifest coordinate and
size, then calls the tested fixed-scale placement helper for all 27 positions.
This is the only approved missing-proxy recovery; do not create primitives or
reopen Rhino just to recover anchors. Preserve asset scale, orientation, anchor,
materials, naming, and license metadata. A missing cached payload, wrong final
dimension, or visible bare C-stand remains a hard failure.

Prefer CC0/public domain, then CC BY 4.0 with attribution. Reject unclear,
editorial-only, NoDerivatives, NonCommercial, or NoAI assets for this workflow.
The cache is an availability list, not proof that every asset must appear in
every shot.

Use collection instances for repeated objects and keep hero equipment detailed
enough to read without overwhelming scene performance. Query DML if a prior
asset import lesson is useful; record a compact lesson only after a meaningful
success or failure.

## Bounded hero camera and preview

Never invent camera matrix math, Track-To constraints, test cubes, or repeated
`CAMERA FIX vN` scripts. Use the checked-in helper exactly:

```python
import bpy, os, importlib.util
root = os.environ["AEC_DEMO_ROOT"]
helper_path = os.path.join(root, "skills", "blender_vp_production.py")
spec = importlib.util.spec_from_file_location("vp_production", helper_path)
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)
removed = vp.remove_legacy_scene_debris()
dressing = vp.apply_required_set_dressing(root)
receipt = vp.render_beauty_preview(root)
print("VP_HERO_PREVIEW_PASS " + repr(receipt))
```

`VP_SET_DRESSING_PASS` is mandatory before `prepare_production_look()`, camera
setup, or rendering. All categories must remain present in the production
scene. The beauty must visibly include at least two physical cameras, a stage
chair, a hero road case, and a complete practical light while preserving the
clear stage floor and circulation; control-room monitors and racks may remain
visible through their room composition rather than dominating the stage shot.

`render_beauty_preview(root)` is the mandatory atomic beauty operation. Do not
unpack `setup_beauty_camera()` or call `render_preview()` separately. The atomic
helper refuses to render unless its newly created beauty camera is active and
writes only to the canonical absolute render path.

`prepare_production_look()` is owned by that helper and applies the fixed Blender material
palette, emissive LED surface, world contribution, key, fill, rim, stage
softbox, AgX look, and exposure. Do not create shader nodes or lights manually.
Require `VP_BEAUTY_VISIBILITY_PASS`, `VP_MATERIAL_PASS`, `VP_LIGHTING_PASS`,
and `VP_RENDER_PASS` before `VP_BEAUTY_PASS`.
Require `VP_MATERIAL_PASS`, `VP_LIGHTING_PASS`, and `VP_RENDER_PASS` before
`VP_HERO_PREVIEW_PASS`. `render_preview()` rejects a uniform gray, blank, or
catastrophically misframed image; file existence alone never passes.

The required beauty is the unobstructed `stage_wide` presentation composition:
lens `(0,-840,96) in` -> `(0,-21.336,2.4384) m`, aimed at
`(-120,60,72) in` -> `(-3.048,1.524,1.8288) m`, with a 14 mm lens. This
position is inside the south clear volume, faces the open side of the curved
LED volume, and avoids the exterior wall, control glazing, and physical camera
proxies. Its verified wide field of view must show the curved LED wall, lit
stage floor, overhead grid, at least two physical production cameras, a hero
chair, a hero road case, and a complete practical light. Do not replace it with
CAM_E, CAM_F, scene-center bounds, origin aiming, or guessed coordinates. Other
physical cameras remain visible as production context.
The cleanup first requires a nonempty `VP_STUDIO_RHINO` mesh collection. It
hard-stops if the checked-in importer was not run or its result was not retained.
It removes only known stale aggregate/test objects such as
`vp_studio_01_export`, `CamTarget`, and `test_cube*`; it never removes the
validated `VP_STUDIO_RHINO` handoff collection.

The secondary presentation angle is
`vp.setup_manifest_camera("stage_three_quarter")`: lens `(600,-588,168) in`
aimed at `(-120,120,108) in` with a 24 mm lens. The physical CAM_A preset is a
tighter reference close-up only. CAM_E and CAM_F are not production-render
options because their locked marks can be occluded by modeled construction and
equipment.
Do not render secondary angles unless the beauty needs one occlusion check.
The validated canonical output from `render_beauty_preview(root)` is the
required ComfyUI source.

Only one passing initial preview and at most one targeted correction are allowed. Send
the absolute preview path to vision. If vision reports a defect, change the
smallest relevant camera preset value and call the helper once. Never replace
the helper's verified `to_track_quat("-Z", "Y")` aiming with handwritten Euler
angles.
The render gate must report mean luminance, foreground coverage, center-region
luminance, contrast, and dynamic range. A mostly black frame with a few visible
chairs is `VP_RENDER_REJECT`, never a passing source. If the second preview fails, stop with the two concrete verdicts; do not enter
a camera/render diagnostic loop.
