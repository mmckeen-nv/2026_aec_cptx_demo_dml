"""
Utah Teapot demo — Blender-only build script.

Loads utah_teapot.obj, scales/positions it on a simple ground plane with a
neutral ceramic material, adds a camera + sun light, and (optionally)
renders a hero shot. Fully self-contained — no other demo's objects or
scenes are touched.

Usage (headless):
  blender --background --python build_teapot_demo.py -- \
      --obj utah_teapot.obj --out teapot_demo.blend --render renders/hero.png

Usage (inside an already-running Blender via MCP execute_blender_code):
  exec(open(r"<this file>").read())
  build_teapot_scene(obj_path=r"...\\utah_teapot.obj")
"""
import bpy
import math
import os
import sys
from mathutils import Vector


def point_at(obj, target):
    """Aim a camera or spotlight's local -Z axis at a world-space target."""
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def build_teapot_scene(obj_path, target_size=0.3, scene_name="TeapotDemo"):
    """Build the teapot demo scene in a NEW bpy.data.scenes entry named
    scene_name, so it never touches whatever scene is already active
    (e.g. the cliff house demo). Returns the new scene."""
    scene = bpy.data.scenes.new(scene_name)

    prev_scene = bpy.context.window.scene if bpy.context.window else None
    if bpy.context.window:
        bpy.context.window.scene = scene

    # This OBJ was exported from Rhino and is already Z-up. Blender's OBJ
    # default assumes Y-up, which rotates the lid onto the side of the body.
    bpy.ops.wm.obj_import(filepath=obj_path, forward_axis='NEGATIVE_Y', up_axis='Z')
    teapot = bpy.context.selected_objects[0]
    teapot.name = "utah_teapot"

    # Normalize scale so the largest dimension = target_size (meters)
    current_max_dim = max(teapot.dimensions)
    scale_factor = target_size / current_max_dim
    teapot.scale = (scale_factor, scale_factor, scale_factor)
    bpy.context.view_layer.objects.active = teapot
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    for polygon in teapot.data.polygons:
        polygon.use_smooth = True

    # Ceramic material
    mat = bpy.data.materials.new("M_Teapot_Ceramic")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.85, 0.82, 0.75, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.25
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.6
    teapot.data.materials.clear()
    teapot.data.materials.append(mat)

    # Sit on the ground using the actual transformed mesh bounds. The OBJ is
    # not centered on its local origin, so half-height placement penetrates.
    min_z = min((teapot.matrix_world @ vertex.co).z for vertex in teapot.data.vertices)
    teapot.location.z -= min_z

    # Ground plane
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "TeapotGround"
    ground_mat = bpy.data.materials.new("M_Ground_Neutral")
    ground_mat.use_nodes = True
    gbsdf = ground_mat.node_tree.nodes["Principled BSDF"]
    gbsdf.inputs["Base Color"].default_value = (0.2, 0.2, 0.22, 1.0)
    gbsdf.inputs["Roughness"].default_value = 0.6
    ground.data.materials.append(ground_mat)

    # Camera
    cam_data = bpy.data.cameras.new("TeapotCamData")
    cam = bpy.data.objects.new("TeapotCam", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (0.6, -0.6, 0.4)
    cam_data.lens = 58
    point_at(cam, (0.0, 0.0, 0.11))
    scene.camera = cam

    # Sun light
    light_data = bpy.data.lights.new("TeapotLightData", type='SUN')
    light_data.energy = 1.0
    light = bpy.data.objects.new("TeapotLight", light_data)
    scene.collection.objects.link(light)
    light.rotation_euler = (math.radians(50), 0, math.radians(30))

    # A broad key makes the ceramic form readable without relying on a
    # workstation-specific world or color-management setup.
    key_data = bpy.data.lights.new("TeapotKeyData", type='AREA')
    key_data.energy = 180.0
    key_data.shape = 'DISK'
    key_data.size = 1.2
    key = bpy.data.objects.new("TeapotKey", key_data)
    scene.collection.objects.link(key)
    key.location = (-0.5, -0.45, 0.7)
    point_at(key, (0.0, 0.0, 0.1))

    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 960

    if prev_scene and bpy.context.window:
        bpy.context.window.scene = prev_scene

    return scene


def render_teapot_scene(scene, output_path):
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = 'PNG'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    bpy.ops.render.render(write_still=True, scene=scene.name)


if __name__ == "__main__":
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []

    obj_path = None
    out_path = None
    render_path = None
    i = 0
    while i < len(argv):
        if argv[i] == "--obj":
            obj_path = argv[i + 1]; i += 2
        elif argv[i] == "--out":
            out_path = argv[i + 1]; i += 2
        elif argv[i] == "--render":
            render_path = argv[i + 1]; i += 2
        else:
            i += 1

    demo_root = os.path.dirname(os.path.abspath(__file__))

    def resolve_demo_path(path):
        return os.path.normpath(path if os.path.isabs(path) else os.path.join(demo_root, path))

    if not obj_path:
        obj_path = os.path.join(demo_root, "utah_teapot.obj")
    else:
        obj_path = resolve_demo_path(obj_path)
    if out_path:
        out_path = resolve_demo_path(out_path)
    if render_path:
        render_path = resolve_demo_path(render_path)

    scene = build_teapot_scene(obj_path)

    # A standalone artifact should open directly into the completed demo
    # scene. The reusable function above still restores the caller's scene.
    if bpy.context.window:
        bpy.context.window.scene = scene

    if render_path:
        render_teapot_scene(scene, render_path)

    if out_path:
        bpy.ops.wm.save_as_mainfile(filepath=out_path)

    print("Teapot demo build complete.")
