"""Apply and preview the operator-approved frontal Cliff House composition."""

from pathlib import Path
import json

import bpy
from mathutils import Vector


PROJECT = Path(
    r"C:\Users\test\Documents\RX Spark AEC\2026_aec_cptx_demo_dml"
    r"\aa_demo_versions\cliff_house_single_frame_01"
)
CAMERA_LOCATION = Vector((-55.0, -1.45, 14.5))
CAMERA_TARGET = Vector((4.0, -1.45, 4.8))
CAMERA_LENS_MM = 52.0
EXPOSURE = 0.6
SUN_ENERGY = 1.5
WARM_AREA_ENERGY = 900.0


def apply_camera():
    scene = bpy.context.scene
    camera = bpy.data.objects.get("ocean_view")
    if camera is None:
        camera_data = bpy.data.cameras.new("ocean_view")
        camera = bpy.data.objects.new("ocean_view", camera_data)
        scene.collection.objects.link(camera)
    if camera.type != "CAMERA":
        raise RuntimeError("ocean_view exists but is not a camera")

    for constraint in list(camera.constraints):
        camera.constraints.remove(constraint)

    camera.data.type = "PERSP"
    camera.data.lens = CAMERA_LENS_MM
    camera.data.sensor_fit = "HORIZONTAL"
    camera.data.shift_x = 0.0
    camera.data.shift_y = 0.0
    camera.location = CAMERA_LOCATION
    camera.rotation_euler = (
        CAMERA_TARGET - CAMERA_LOCATION
    ).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera

    camera["composition_authority"] = (
        "Screenshot 2026-07-27 at 12.49.16 PM.png"
    )
    camera["composition"] = "frontal_west_elevation"
    camera["target"] = list(CAMERA_TARGET)
    return camera


def apply_reference_look():
    terrain = bpy.data.materials.get("M_Terrain_Coastal")
    if terrain and terrain.use_nodes:
        principled = terrain.node_tree.nodes.get("Principled BSDF")
        if principled:
            principled.inputs["Base Color"].default_value = (
                0.24,
                0.25,
                0.25,
                1.0,
            )
            principled.inputs["Roughness"].default_value = 0.95

    exposed = bpy.data.materials.get("M_Concrete_Exposed")
    if exposed:
        for name in ("L2_roof_garage", "L3_roof_slab"):
            obj = bpy.data.objects.get(name)
            if obj and obj.type == "MESH":
                obj.data.materials.clear()
                obj.data.materials.append(exposed)

    water = bpy.data.materials.get("M_Water_NearBlack")
    if water and water.use_nodes:
        principled = water.node_tree.nodes.get("Principled BSDF")
        if principled:
            principled.inputs["Base Color"].default_value = (
                0.005,
                0.09,
                0.15,
                1.0,
            )
            principled.inputs["Roughness"].default_value = 0.06
            if "IOR" in principled.inputs:
                principled.inputs["IOR"].default_value = 1.333

    world = bpy.context.scene.world
    if world and world.use_nodes:
        background = world.node_tree.nodes.get("Background")
        if background:
            for link in list(background.inputs["Color"].links):
                world.node_tree.links.remove(link)
            background.inputs["Color"].default_value = (0.42, 0.44, 0.45, 1.0)
            background.inputs["Strength"].default_value = 0.50


def render_preview():
    scene = bpy.context.scene
    camera = apply_camera()
    apply_reference_look()
    scene.view_settings.exposure = EXPOSURE
    sun = bpy.data.objects.get("Sun")
    if sun and sun.type == "LIGHT":
        sun.data.energy = SUN_ENERGY
        sun.data.color = (1.0, 0.90, 0.80)
    warm_area = bpy.data.objects.get("Warm_Area")
    if warm_area and warm_area.type == "LIGHT":
        warm_area.data.energy = WARM_AREA_ENERGY
        warm_area.data.color = (1.0, 0.78, 0.62)
    original = {
        "engine": scene.render.engine,
        "resolution_x": scene.render.resolution_x,
        "resolution_y": scene.render.resolution_y,
        "resolution_percentage": scene.render.resolution_percentage,
        "filepath": scene.render.filepath,
    }

    preview_dir = PROJECT / "renders" / "camera_reference_tests"
    preview_dir.mkdir(parents=True, exist_ok=True)
    output = preview_dir / "front_elevation_v5.png"
    try:
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.resolution_x = 960
        scene.render.resolution_y = 540
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
    finally:
        scene.render.engine = original["engine"]
        scene.render.resolution_x = original["resolution_x"]
        scene.render.resolution_y = original["resolution_y"]
        scene.render.resolution_percentage = original["resolution_percentage"]
        scene.render.filepath = original["filepath"]

    bpy.ops.wm.save_as_mainfile(
        filepath=str(PROJECT / "blender_assets" / "base_model.blend")
    )
    receipt = {
        "status": "PASS",
        "camera": camera.name,
        "composition": camera["composition"],
        "location": list(camera.location),
        "target": list(CAMERA_TARGET),
        "lens_mm": camera.data.lens,
        "exposure": scene.view_settings.exposure,
        "sun_energy": sun.data.energy if sun else None,
        "warm_area_energy": warm_area.data.energy if warm_area else None,
        "preview": str(output),
    }
    print("FRONT_CAMERA_PASS " + json.dumps(receipt))


def render_final():
    scene = bpy.context.scene
    camera = apply_camera()
    apply_reference_look()
    scene.view_settings.exposure = EXPOSURE
    scene.camera = camera
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    output = PROJECT / "renders" / "single_frame" / "png" / "frame_0000.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(
        filepath=str(PROJECT / "blender_assets" / "base_model.blend")
    )
    print(
        "FRONT_FINAL_PASS "
        + json.dumps(
            {
                "status": "PASS",
                "camera": camera.name,
                "location": list(camera.location),
                "target": list(CAMERA_TARGET),
                "lens_mm": camera.data.lens,
                "exposure": scene.view_settings.exposure,
                "resolution": [
                    scene.render.resolution_x,
                    scene.render.resolution_y,
                ],
                "cycles_samples": scene.cycles.samples,
                "output": str(output),
            }
        )
    )


render_preview()
render_final()
