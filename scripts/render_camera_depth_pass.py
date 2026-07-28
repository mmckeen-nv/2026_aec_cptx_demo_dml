"""Render a fast, metric camera-space depth PNG from the active Blender scene.

This is intentionally a material-override Eevee pass. It avoids Blender 5.2's
removed compositor math nodes while preserving real per-pixel view distance.
Near geometry is white, far geometry is dark, and the background is black.
"""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


OUTPUT_PATH = Path(
    globals().get(
        "DEPTH_OUTPUT_PATH",
        "aa_demo_versions/cliff_house_single_frame_01/"
        "renders/single_frame/depth/frame_0000.png",
    )
).resolve()
VALIDATION_PATH = OUTPUT_PATH.with_name("camera_depth_validation.json")
PREVIEW_PATH = OUTPUT_PATH.with_name(f"{OUTPUT_PATH.stem}_preview.png")


def visible_meshes(scene: bpy.types.Scene) -> list[bpy.types.Object]:
    return [
        obj
        for obj in scene.objects
        if obj.type == "MESH" and not obj.hide_render
    ]


def camera_depth_range(
    camera: bpy.types.Object,
    objects: list[bpy.types.Object],
) -> tuple[float, float]:
    camera_inverse = camera.matrix_world.inverted()
    depths: list[float] = []
    for obj in objects:
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            depth = -(camera_inverse @ world).z
            if camera.data.clip_start < depth < camera.data.clip_end:
                depths.append(depth)
    if not depths:
        raise RuntimeError("CAMERA_DEPTH_FAIL no visible mesh bounds are in front of the camera")
    raw_near = min(depths)
    raw_far = max(depths)
    span = max(raw_far - raw_near, 0.01)
    margin = span * 0.025
    near = max(float(camera.data.clip_start), raw_near - margin)
    far = min(float(camera.data.clip_end), raw_far + margin)
    if far - near < 0.01:
        raise RuntimeError("CAMERA_DEPTH_FAIL scene depth range is effectively flat")
    return near, far


def build_depth_material(near: float, far: float) -> bpy.types.Material:
    material = bpy.data.materials.get("AEC_CAMERA_DEPTH") or bpy.data.materials.new(
        "AEC_CAMERA_DEPTH"
    )
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()

    camera_data = nodes.new("ShaderNodeCameraData")
    remap = nodes.new("ShaderNodeMapRange")
    emission = nodes.new("ShaderNodeEmission")
    output = nodes.new("ShaderNodeOutputMaterial")

    remap.interpolation_type = "LINEAR"
    remap.clamp = True
    remap.inputs["From Min"].default_value = near
    remap.inputs["From Max"].default_value = far
    remap.inputs["To Min"].default_value = 1.0
    remap.inputs["To Max"].default_value = 0.02
    emission.inputs["Strength"].default_value = 1.0

    # Blender 5.2 exposes signed View Z Depth in this shader path; feeding it
    # into a positive near/far range clamps the entire subject to white. View
    # Distance is positive and retains the required per-pixel depth gradient.
    links.new(camera_data.outputs["View Distance"], remap.inputs["Value"])
    links.new(remap.outputs["Result"], emission.inputs["Color"])
    links.new(emission.outputs["Emission"], output.inputs["Surface"])
    return material


def main() -> None:
    scene = bpy.context.scene
    camera = scene.camera
    if camera is None or camera.type != "CAMERA":
        raise RuntimeError("CAMERA_DEPTH_FAIL active scene camera is missing")

    objects = visible_meshes(scene)
    near, far = camera_depth_range(camera, objects)
    material = build_depth_material(near, far)
    view_layer = bpy.context.view_layer
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")

    previous = {
        "engine": scene.render.engine,
        "filepath": scene.render.filepath,
        "format": scene.render.image_settings.file_format,
        "color_mode": scene.render.image_settings.color_mode,
        "color_depth": scene.render.image_settings.color_depth,
        "film_transparent": scene.render.film_transparent,
        "view_transform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "exposure": scene.view_settings.exposure,
        "gamma": scene.view_settings.gamma,
        "override": view_layer.material_override,
        "background_color": (
            tuple(background.inputs["Color"].default_value)
            if background is not None
            else None
        ),
        "background_strength": (
            float(background.inputs["Strength"].default_value)
            if background is not None
            else None
        ),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        view_layer.material_override = material
        if background is not None:
            background.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
            background.inputs["Strength"].default_value = 0.0
        scene.render.engine = "BLENDER_EEVEE"
        scene.render.filepath = str(OUTPUT_PATH)
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "BW"
        scene.render.image_settings.color_depth = "16"
        scene.render.film_transparent = False
        scene.view_settings.view_transform = "Raw"
        scene.view_settings.look = "None"
        scene.view_settings.exposure = 0.0
        scene.view_settings.gamma = 1.0
        bpy.ops.render.render(write_still=True)
        # Browsers and dashboard image surfaces inconsistently display 16-bit
        # grayscale PNGs. Render the identical data mapping once more as an
        # 8-bit operator preview while retaining the 16-bit source above.
        scene.render.filepath = str(PREVIEW_PATH)
        scene.render.image_settings.color_depth = "8"
        bpy.ops.render.render(write_still=True)
    finally:
        view_layer.material_override = previous["override"]
        scene.render.engine = previous["engine"]
        scene.render.filepath = previous["filepath"]
        scene.render.image_settings.file_format = previous["format"]
        scene.render.image_settings.color_mode = previous["color_mode"]
        scene.render.image_settings.color_depth = previous["color_depth"]
        scene.render.film_transparent = previous["film_transparent"]
        scene.view_settings.view_transform = previous["view_transform"]
        scene.view_settings.look = previous["look"]
        scene.view_settings.exposure = previous["exposure"]
        scene.view_settings.gamma = previous["gamma"]
        if background is not None and previous["background_color"] is not None:
            background.inputs["Color"].default_value = previous["background_color"]
            background.inputs["Strength"].default_value = previous["background_strength"]

    if not OUTPUT_PATH.exists() or OUTPUT_PATH.stat().st_size < 10_000:
        raise RuntimeError("CAMERA_DEPTH_FAIL output PNG is missing or unexpectedly small")
    if not PREVIEW_PATH.exists() or PREVIEW_PATH.stat().st_size < 10_000:
        raise RuntimeError("CAMERA_DEPTH_FAIL preview PNG is missing or unexpectedly small")
    validation = {
        "pass": True,
        "method": "camera_data_view_distance_material_override",
        "camera": camera.name,
        "near_distance": near,
        "far_distance": far,
        "distance_span": far - near,
        "visible_meshes": len(objects),
        "engine": "BLENDER_EEVEE",
        "bit_depth": 16,
        "near_is_white": True,
        "output": str(OUTPUT_PATH),
        "bytes": OUTPUT_PATH.stat().st_size,
        "preview": str(PREVIEW_PATH),
        "preview_bytes": PREVIEW_PATH.stat().st_size,
    }
    VALIDATION_PATH.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print("CAMERA_DEPTH_PASS " + json.dumps(validation, separators=(",", ":")))


if __name__ == "__main__":
    main()
