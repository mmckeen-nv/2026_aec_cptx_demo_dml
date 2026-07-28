"""Render the terrain-free oblique source frame used only by ComfyUI."""

from pathlib import Path
import json

import bpy
from mathutils import Vector


ROOT = Path(r"C:\Users\test\Documents\RX Spark AEC\2026_aec_cptx_demo_dml")
PROJECT = ROOT / "aa_demo_versions" / "cliff_house_single_frame_01"
CAMERA_LOCATION = Vector((-50.0, -42.0, 18.0))
CAMERA_TARGET = Vector((2.0, 2.0, 4.5))
CAMERA_LENS_MM = 50.0


def apply_environment_filter():
    script = ROOT / "scripts" / "remove_tagged_blender_environment.py"
    namespace = {"__name__": "cliff_house_environment_filter"}
    exec(compile(script.read_text(encoding="utf-8"), str(script), "exec"), namespace)
    return namespace["apply_environment_filter"]()


def get_camera():
    scene = bpy.context.scene
    camera = bpy.data.objects.get("comfy_ocean_view")
    if camera is None:
        data = bpy.data.cameras.new("comfy_ocean_view")
        camera = bpy.data.objects.new("comfy_ocean_view", data)
        scene.collection.objects.link(camera)
    camera.data.type = "PERSP"
    camera.data.lens = CAMERA_LENS_MM
    camera.data.sensor_fit = "HORIZONTAL"
    camera.data.shift_x = 0.0
    camera.data.shift_y = 0.0
    camera.location = CAMERA_LOCATION
    camera.rotation_euler = (
        CAMERA_TARGET - CAMERA_LOCATION
    ).to_track_quat("-Z", "Y").to_euler()
    camera["composition"] = "comfy_coastal_cliff_oblique"
    camera["target"] = list(CAMERA_TARGET)
    return camera


def render():
    scene = bpy.context.scene
    filter_receipt = apply_environment_filter()
    review_camera = scene.camera
    camera = get_camera()
    output = (
        PROJECT
        / "renders"
        / "single_frame"
        / "comfy_source"
        / "frame_0000.png"
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    scene.camera = camera
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)

    scene.camera = review_camera
    bpy.ops.wm.save_as_mainfile(
        filepath=str(PROJECT / "blender_assets" / "base_model.blend")
    )
    receipt = {
        "status": "PASS",
        "camera": camera.name,
        "location": list(camera.location),
        "target": list(CAMERA_TARGET),
        "lens_mm": camera.data.lens,
        "resolution": [1920, 1080],
        "cycles_samples": scene.cycles.samples,
        "output": str(output),
        "environment_filter": filter_receipt,
        "restored_review_camera": review_camera.name if review_camera else None,
    }
    print("COMFY_SOURCE_RENDER_PASS " + json.dumps(receipt))


if __name__ == "__main__":
    render()
