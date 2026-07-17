# BAC HERO pool dressing - two audience gates

The base BAC HERO render and Comfy result must exist before pool dressing.
Opening the house does not authorize either stage below.

## STOP GATE A - Floaties

Wait for a new user turn such as:

> Let's add the floaties to the pool.

Only then call `add_pool_floaties(root, reset=True)`. Require
`BAC_POOL_FLOATIES_PASS floats=2 chairs=0 furniture=0`, render
`Cam_Shot_A` to `bac_teapot_pool_floaties.png`, run the stage-aware Comfy
wrapper, report its floaties artifact, and **STOP**. Do not add loungers,
chairs, tables, umbrellas, or other furniture.

## STOP GATE B - Other assets

Wait for another, later user turn such as:

> Now add the other pool assets: the chairs and Outdoor Furniture 1.

Only then call `add_pool_furniture(root)`. It must reject a scene without a
validated floaties stage. Require
`BAC_POOL_FURNITURE_PASS floats=2 chairs=3 furniture=1`, then render
`Cam_Shot_A` to `bac_teapot_pool_complete.png`.

Never call both stage functions in one turn and never call the disabled
`add_pool_assets` function. Do not discover asset files, append manually,
estimate transforms, or alter the immutable HERO master. The helper owns the
six hashes, measured water/deck/patio zones, normal sizes, chair orientation,
and required 1:1000 scene conversion.
