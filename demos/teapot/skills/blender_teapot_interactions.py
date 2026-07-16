"""Tested Blender operations for the BAC Teapot live demo.

Load this module only through Blender MCP. It builds the verified 1987 Utah
teapot directly from the checked-in canonical OBJ, then owns the product stage,
reversible material interactions, camera, lighting, previews, and checkpoint.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path


ROOT_COLLECTION = "BAC_TEAPOT"
TEAPOT_NAMES = {"TEAPOT_BODY", "TEAPOT_LID", "TEAPOT_SPOUT", "TEAPOT_HANDLE"}
CANONICAL_SHA256 = "a447b8936e70678c70438a4155b6ef5310c4d0a647cee362f84d53c8b38baf9f"
CANONICAL_VERTICES = 18530
CANONICAL_FACES = 18432
TARGET_WIDTH_M = 0.30
SOURCE_X_SPAN = 6.434042

PRESETS = {
    "glazed_ceramic": dict(rgba=(0.12, 0.32, 0.62, 1.0), metallic=0.0, roughness=0.16),
    "white_porcelain": dict(rgba=(0.92, 0.90, 0.84, 1.0), metallic=0.0, roughness=0.12),
    "copper": dict(rgba=(0.72, 0.22, 0.07, 1.0), metallic=0.92, roughness=0.22),
    "brushed_steel": dict(rgba=(0.42, 0.48, 0.53, 1.0), metallic=0.95, roughness=0.30),
    "chrome": dict(rgba=(0.72, 0.76, 0.80, 1.0), metallic=1.0, roughness=0.07),
    "glass": dict(rgba=(0.30, 0.56, 0.72, 1.0), metallic=0.0, roughness=0.08, transmission=0.82, alpha=0.34),
    "matte_black": dict(rgba=(0.012, 0.015, 0.020, 1.0), metallic=0.05, roughness=0.68),
}

ALIASES = {
    "ceramic": "glazed_ceramic", "blue ceramic": "glazed_ceramic",
    "porcelain": "white_porcelain", "white": "white_porcelain",
    "steel": "brushed_steel", "metal": "brushed_steel",
    "shiny metal": "chrome", "black": "matte_black",
    "transparent": "glass",
}


def _bpy():
    import bpy
    return bpy


def _source(root: Path) -> Path:
    return root / "demos" / "teapot" / "utah_teapot.obj"


def _objects():
    bpy = _bpy()
    collection = bpy.data.collections.get(ROOT_COLLECTION)
    if collection is None:
        raise RuntimeError("missing canonical teapot collection: " + ROOT_COLLECTION)
    objects = [obj for obj in collection.all_objects if obj.type == "MESH"]
    names = {obj.name for obj in objects}
    if names != TEAPOT_NAMES:
        raise RuntimeError("teapot object mismatch missing={} extra={}".format(
            sorted(TEAPOT_NAMES - names), sorted(names - TEAPOT_NAMES)))
    return objects


def _clear_scene():
    bpy = _bpy()
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        if collection.users == 0:
            bpy.data.collections.remove(collection)


def _parse_canonical_obj(source: Path):
    """Parse the fixed OBJ without Blender import axis/scale heuristics."""
    vertices = []
    grouped_faces = {}
    current = None
    for raw in source.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("v "):
            vertices.append(tuple(float(v) for v in line.split()[1:4]))
        elif line.startswith("g "):
            current = line.split(None, 1)[1].strip().lower()
            grouped_faces.setdefault(current, [])
        elif line.startswith("f "):
            if current is None:
                raise RuntimeError("CANONICAL_DATA_FAIL face before group")
            grouped_faces[current].append(tuple(int(v.split("/")[0]) - 1 for v in line.split()[1:]))
    return vertices, grouped_faces


def build_canonical_teapot(root, reset_scene=True):
    """Build the canonical four-part Utah teapot directly in Blender."""
    bpy = _bpy()
    root = Path(root).resolve()
    source = _source(root)
    if not source.is_file() or source.stat().st_size == 0:
        raise RuntimeError("CANONICAL_DATA_FAIL missing source: " + str(source))
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != CANONICAL_SHA256:
        raise RuntimeError("CANONICAL_DATA_FAIL sha256=" + digest)
    vertices, grouped_faces = _parse_canonical_obj(source)
    expected_groups = {"teapot_body", "teapot_lid", "teapot_spout", "teapot_handle"}
    face_count = sum(len(faces) for faces in grouped_faces.values())
    if len(vertices) != CANONICAL_VERTICES or face_count != CANONICAL_FACES or set(grouped_faces) != expected_groups:
        raise RuntimeError("CANONICAL_DATA_FAIL vertices={} faces={} groups={}".format(
            len(vertices), face_count, sorted(grouped_faces)))
    if reset_scene:
        _clear_scene()
    old = bpy.data.collections.get(ROOT_COLLECTION)
    if old is not None:
        for obj in list(old.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    collection = old or bpy.data.collections.new(ROOT_COLLECTION)
    if collection.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(collection)
    scale = TARGET_WIDTH_M / SOURCE_X_SPAN
    name_map = {
        "teapot_body": "TEAPOT_BODY", "teapot_lid": "TEAPOT_LID",
        "teapot_spout": "TEAPOT_SPOUT", "teapot_handle": "TEAPOT_HANDLE",
    }
    for group, faces in grouped_faces.items():
        used = sorted({index for face in faces for index in face})
        remap = {old_index: new_index for new_index, old_index in enumerate(used)}
        local_vertices = [tuple(coordinate * scale for coordinate in vertices[index]) for index in used]
        local_faces = [tuple(remap[index] for index in face) for face in faces]
        object_name = name_map[group]
        mesh = bpy.data.meshes.new(object_name + "_MESH")
        mesh.from_pydata(local_vertices, [], local_faces)
        mesh.update(calc_edges=True)
        obj = bpy.data.objects.new(object_name, mesh)
        collection.objects.link(obj)
        obj["project"] = "teapot-01"
        obj["canonical_source"] = "utah_teapot.obj"
        obj["canonical_sha256"] = CANONICAL_SHA256
        obj["canonical_version"] = "1987-frank-crow-resolution-24"
        for polygon in mesh.polygons:
            polygon.use_smooth = True
    objects = _objects()
    minimum, maximum, _target, _span = _world_bounds()
    width = maximum[0] - minimum[0]
    if len(objects) != 4 or abs(width - TARGET_WIDTH_M) > 1e-6 or abs(minimum[2]) > 1e-6:
        raise RuntimeError("TEAPOT_BUILD_FAIL objects={} width_m={:.9f} zmin={:.9f}".format(
            len(objects), width, minimum[2]))
    print("CANONICAL_DATA_PASS source=utah-official-1987-frank-crow vertices={} faces={} groups=4 sha256={}".format(
        len(vertices), face_count, digest))
    receipt = "TEAPOT_BUILD_PASS objects=4 width_m={:.6f} zmin_m={:.6f} sha256={}".format(
        width, minimum[2], digest[:12])
    print(receipt)
    return receipt


def _set_input(bsdf, name, value):
    socket = bsdf.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def apply_custom_material(name, rgba=None, metallic=0.0, roughness=0.25,
                          transmission=0.0, alpha=1.0):
    """Apply a bounded Principled material without altering geometry."""
    bpy = _bpy()
    if rgba is None:
        rgba = (0.12, 0.32, 0.62, 1.0)
    rgba = tuple(float(max(0.0, min(1.0, v))) for v in rgba)
    if len(rgba) == 3:
        rgba = rgba + (1.0,)
    metallic = float(max(0.0, min(1.0, metallic)))
    roughness = float(max(0.02, min(1.0, roughness)))
    transmission = float(max(0.0, min(1.0, transmission)))
    alpha = float(max(0.05, min(1.0, alpha)))
    material_name = "BAC_Teapot_" + "".join(c if c.isalnum() else "_" for c in name)
    material = bpy.data.materials.get(material_name) or bpy.data.materials.new(material_name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        raise RuntimeError("Principled BSDF missing from " + material.name)
    _set_input(bsdf, "Base Color", rgba)
    _set_input(bsdf, "Metallic", metallic)
    _set_input(bsdf, "Roughness", roughness)
    _set_input(bsdf, "Transmission Weight", transmission)
    _set_input(bsdf, "Transmission", transmission)
    _set_input(bsdf, "Alpha", alpha)
    _set_input(bsdf, "IOR", 1.46)
    material.diffuse_color = (rgba[0], rgba[1], rgba[2], alpha)
    for obj in _objects():
        obj.data.materials.clear()
        obj.data.materials.append(material)
        obj["bac_material_style"] = name
    receipt = "TEAPOT_MATERIAL_PASS style={} metallic={:.2f} roughness={:.2f} transmission={:.2f}".format(
        name, metallic, roughness, transmission)
    print(receipt)
    return receipt


def apply_material(style):
    key = str(style).strip().lower().replace("-", "_")
    key = ALIASES.get(key, key)
    if key not in PRESETS:
        raise ValueError("unknown teapot material {!r}; choices={}".format(style, sorted(PRESETS)))
    values = dict(PRESETS[key])
    alpha = values.pop("alpha", 1.0)
    return apply_custom_material(key, alpha=alpha, **values)


def _look_at(obj, target):
    from mathutils import Vector
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def _world_bounds():
    """Return a framing target and span from the canonical live meshes."""
    from mathutils import Vector
    points = [obj.matrix_world @ Vector(corner) for obj in _objects() for corner in obj.bound_box]
    minimum = tuple(min(point[i] for point in points) for i in range(3))
    maximum = tuple(max(point[i] for point in points) for i in range(3))
    target = tuple((minimum[i] + maximum[i]) * 0.5 for i in range(3))
    span = max(maximum[i] - minimum[i] for i in range(3))
    if span <= 0.0:
        raise RuntimeError("invalid teapot bounds")
    return minimum, maximum, target, span


def _ensure_stage():
    bpy = _bpy()
    scene = bpy.context.scene
    minimum, maximum, target, span = _world_bounds()
    ground = bpy.data.objects.get("BAC_Product_Ground")
    if ground is None:
        bpy.ops.mesh.primitive_plane_add(size=max(1.2, span * 5.0), location=(target[0], target[1], minimum[2] - 0.002))
        ground = bpy.context.object
        ground.name = "BAC_Product_Ground"
    else:
        ground.location = (target[0], target[1], minimum[2] - 0.002)
    ground_mat = bpy.data.materials.get("BAC_Ground") or bpy.data.materials.new("BAC_Ground")
    ground_mat.use_nodes = True
    g = ground_mat.node_tree.nodes.get("Principled BSDF")
    _set_input(g, "Base Color", (0.035, 0.042, 0.055, 1.0))
    _set_input(g, "Roughness", 0.48)
    ground.data.materials.clear(); ground.data.materials.append(ground_mat)

    for name, kind, offset, energy, size_factor, color in (
        ("BAC_Key", "AREA", (-1.25, -1.35, 1.65), 120.0, 1.25, (1.0, 0.78, 0.60)),
        ("BAC_Fill", "AREA", (1.35, -0.75, 0.75), 45.0, 1.10, (0.55, 0.72, 1.0)),
        ("BAC_Rim", "AREA", (0.15, 1.10, 1.35), 85.0, 0.90, (0.65, 0.78, 1.0)),
    ):
        obj = bpy.data.objects.get(name)
        if obj is None:
            data = bpy.data.lights.new(name + "Data", kind)
            obj = bpy.data.objects.new(name, data)
            scene.collection.objects.link(obj)
        obj.location = tuple(target[i] + span * offset[i] for i in range(3))
        obj.data.energy = energy
        obj.data.shape = "DISK"
        obj.data.size = span * size_factor
        obj.data.color = color
        _look_at(obj, target)

    camera = bpy.data.objects.get("BAC_Hero_Camera")
    if camera is None:
        data = bpy.data.cameras.new("BAC_Hero_Camera_Data")
        camera = bpy.data.objects.new("BAC_Hero_Camera", data)
        scene.collection.objects.link(camera)
    # Near-profile framing keeps both the negative-X handle and positive-X
    # spout legible. Distance derives from the imported canonical bounds.
    camera.location = (target[0] + span * 0.10, target[1] - span * 2.35, target[2] + span * 0.62)
    camera.data.lens = 55.0
    _look_at(camera, target)
    scene.camera = camera
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.018, 0.024, 0.040, 1.0)
        background.inputs["Strength"].default_value = 0.10
    scene.render.resolution_x = 960
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.exposure = -0.7
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    return camera


def prepare_product_stage(style="glazed_ceramic"):
    _objects()
    camera = _ensure_stage()
    material_receipt = apply_material(style)
    receipt = "TEAPOT_LOOK_PASS camera={} lights=3 ground=1 {}".format(camera.name, material_receipt)
    print(receipt)
    return receipt


def set_camera_view(azimuth_degrees=-90.0, elevation_degrees=15.0, distance=None):
    bpy = _bpy()
    camera = _ensure_stage()
    azimuth = math.radians(float(azimuth_degrees))
    elevation = math.radians(float(elevation_degrees))
    _minimum, _maximum, target, span = _world_bounds()
    distance = span * 2.35 if distance is None else float(distance)
    distance = float(max(span * 1.8, min(span * 4.0, distance)))
    camera.location = (
        target[0] + distance * math.cos(elevation) * math.cos(azimuth),
        target[1] + distance * math.cos(elevation) * math.sin(azimuth),
        target[2] + distance * math.sin(elevation),
    )
    _look_at(camera, target)
    receipt = "TEAPOT_CAMERA_PASS azimuth={:.1f} elevation={:.1f} distance={:.2f}".format(
        float(azimuth_degrees), float(elevation_degrees), distance)
    print(receipt)
    return receipt


def render_preview(root, filename="teapot_preview.png", samples=32):
    bpy = _bpy()
    root = Path(root).resolve()
    _objects(); _ensure_stage()
    output = root / "demos" / "teapot" / "renders" / Path(filename).name
    output.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = int(samples)
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    if not output.is_file() or output.stat().st_size < 10_000:
        raise RuntimeError("TEAPOT_PREVIEW_FAIL missing/undersized render: " + str(output))
    image = bpy.data.images.get("Render Result")
    if image is not None and len(image.pixels) >= 4:
        pixels = image.pixels
        stride = max(4, (len(pixels) // 4096 // 4) * 4)
        values = []
        for i in range(0, len(pixels) - 3, stride):
            values.append(0.2126 * pixels[i] + 0.7152 * pixels[i + 1] + 0.0722 * pixels[i + 2])
        mean = sum(values) / max(1, len(values))
        dynamic = max(values) - min(values) if values else 0.0
        if mean < 0.015 or dynamic < 0.04:
            raise RuntimeError("TEAPOT_PREVIEW_FAIL mean={:.4f} dynamic={:.4f}".format(mean, dynamic))
    receipt = "TEAPOT_PREVIEW_PASS output={} bytes={}".format(output, output.stat().st_size)
    print(receipt)
    return receipt


def save_checkpoint(root):
    bpy = _bpy()
    root = Path(root).resolve()
    _objects()
    destination = root / "demos" / "teapot" / "blender_assets" / "teapot_interactive.blend"
    destination.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(destination))
    receipt = "TEAPOT_SAVE_PASS output={} bytes={}".format(destination, destination.stat().st_size)
    print(receipt)
    return receipt
