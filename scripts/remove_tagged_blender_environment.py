"""Hide Rhino coordination geometry that ComfyUI must replace."""

import json

import bpy


REMOVE_DISPOSITIONS = {
    "REMOVE_BEFORE_RENDER",
    "COMFY_REPLACE",
}


def apply_environment_filter():
    hidden = []
    retained = []
    for obj in bpy.context.scene.objects:
        disposition = str(obj.get("blender_disposition", "KEEP")).upper()
        if obj.name == "SITE_TERRAIN" and disposition == "KEEP":
            disposition = "REMOVE_BEFORE_RENDER"
            obj["blender_disposition"] = disposition
        if disposition in REMOVE_DISPOSITIONS:
            obj.hide_render = True
            obj.hide_viewport = True
            obj["comfy_environment_role"] = "GENERATIVE_COASTAL_CLIFF"
            hidden.append(obj.name)
        else:
            retained.append(obj.name)

    terrain = bpy.data.objects.get("SITE_TERRAIN")
    if terrain is None:
        raise RuntimeError("SITE_TERRAIN is missing; disposition cannot be verified")
    if not terrain.hide_render:
        raise RuntimeError("SITE_TERRAIN remained render-visible")

    receipt = {
        "status": "PASS",
        "hidden": sorted(hidden),
        "retained_count": len(retained),
        "terrain_disposition": terrain["blender_disposition"],
        "terrain_environment_role": terrain["comfy_environment_role"],
    }
    print("BLENDER_ENVIRONMENT_FILTER_PASS " + json.dumps(receipt))
    return receipt


if __name__ == "__main__":
    apply_environment_filter()
