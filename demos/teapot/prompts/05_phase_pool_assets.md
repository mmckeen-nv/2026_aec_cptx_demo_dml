# BAC HERO pool-assets interaction

Trigger only after the BAC HERO working scene is open and the user explicitly
asks to add the pool assets. The canonical audience prompt is:

> Let's add the pool assets to the pool area. Put the float ring and flamingo
> into the actual pool, place the chairs around the pool, and place Outdoor
> Furniture 1 near the pool.

Do not use Blender file discovery, manual append operations, generic transforms,
or estimated coordinates. Load `skills/blender_bac_hero.py` through Blender MCP,
call `add_pool_assets(root, reset=True)`, require
`BAC_POOL_ASSETS_PASS floats=2 chairs=3 furniture=1`, then call
`render_hero(root, camera_name="Cam_Shot_A",
filename="bac_teapot_pool_assets.png")`.

The tested helper treats the HERO scene as a measured site plan. It places two
floating assets inside the exact water bounds, three normal-size loungers on
the east deck facing the pool, and the dining/umbrella set on the north patio.
It converts metre-authored assets to the HERO scene's 1:1000 numerical scale,
validates the resulting bounds, and saves only the working copy. Stop after the
render and wait for the next audience interaction.
