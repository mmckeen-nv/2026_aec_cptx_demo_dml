"""Deterministic Blender operations for the BAC Teapot house HERO lane."""

from __future__ import annotations

import hashlib
import math
import shutil
from pathlib import Path


EXPECTED = {"objects": 506, "meshes": 257, "cameras": 6, "lights": 1}
MASTER_SHA256 = "350e19eb3db88cf5c98c98ba76f5d9f2017ed168b5fcf7e276a2c3bb13c7b882"
DEFAULT_CAMERA = "Camera_day"
POOL_COLLECTION = "BAC_POOL_ASSETS"
POOL_WATER_OBJECT = "water_surface_new"
POOL_SCENE_SCALE = 0.001
POOL_WATER_BOUNDS = (
    (-0.006502751, -0.011499996, 0.000495059),
    (-0.002648030, 0.001000830, 0.000508416),
)
POOL_ASSET_SHA256 = {
    "beach_chair_v1.blend": "7c27fe5b19bd211a6736342636876993fb04d91690feba0c3d49993d9adc1f9e",
    "beach_chair_v2.blend": "cbd8b8bef53865f6528859515ef55afeffd83e4dbfc6b5474686604f853db509",
    "beach_chair_v3.blend": "560e94ffe989f5b0eec97163e99d4de7b1182c8f7e3fc35351d651f0b7438792",
    "float_ring.blend": "04333a1b08d114412e591e89725cc660e29a6dda042be52ca5ccad7e21a06344",
    "OutdoorFurniture1.blend": "11388046766d5fd5d39337d1a3cd9213d3ffccc84498ec308db2efcdbbbf935a",
    "pool_flamingo.blend": "40e58bd288c8154345b5ee490f09d2fcefd027c3a04d7edeb3ded5ea43af9f37",
}
POOL_PLACEMENTS = (
    # Floating assets: centered inside the verified water rectangle.
    {"name": "FLOAT_RING", "file": "float_ring.blend", "objects": ("Float_Ring_Group", "Pool_Raft"),
     "location": (-0.00520, -0.00750, 0.000506), "rotation": math.radians(12.0), "span": 0.00120,
     "category": "float"},
    {"name": "POOL_FLAMINGO", "file": "pool_flamingo.blend", "objects": ("Pool_Toy_Group", "Pool_Toy"),
     "location": (-0.00370, -0.00250, 0.000506), "rotation": math.radians(-18.0), "span": 0.00160,
     "category": "float"},
    # Loungers: east pool deck, long axis facing the water, clear of its edge.
    {"name": "BEACH_CHAIR_1", "file": "beach_chair_v1.blend", "objects": ("Beach_Chair_v1",),
     "location": (-0.00140, -0.00850, 0.000520), "rotation": math.radians(270.0), "span": 0.00200,
     "category": "chair"},
    {"name": "BEACH_CHAIR_2", "file": "beach_chair_v2.blend", "objects": ("Beach_Chair_V2",),
     "location": (-0.00140, -0.00550, 0.000520), "rotation": math.radians(270.0), "span": 0.00200,
     "category": "chair"},
    {"name": "BEACH_CHAIR_3", "file": "beach_chair_v3.blend", "objects": ("Beach_Chair_V3",),
     "location": (-0.00140, -0.00250, 0.000520), "rotation": math.radians(270.0), "span": 0.00200,
     "category": "chair"},
    # Dining set: north patio zone, outside the water and chair lane.
    {"name": "OUTDOOR_FURNITURE_1", "file": "OutdoorFurniture1.blend", "prefix": "outdoorfurniture1_",
     "location": (-0.00450, 0.00450, 0.000520), "rotation": math.radians(8.0), "span": 0.00320,
     "category": "furniture"},
)


def _bpy():
    import bpy
    return bpy


def _hero_master(root):
    return Path(root).resolve() / "demos" / "teapot" / "hero" / "BAC_TEAPOT_HERO.blend"


def _hero_working_copy(root):
    return Path(root).resolve() / "demos" / "teapot" / "hero" / "work" / "BAC_TEAPOT_HERO_working.blend"


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _audit():
    bpy = _bpy()
    pool = bpy.data.collections.get(POOL_COLLECTION)
    pool_objects = set(pool.objects) if pool else set()
    counts = {
        "objects": sum(obj not in pool_objects for obj in bpy.data.objects),
        "meshes": sum(obj.type == "MESH" and obj not in pool_objects for obj in bpy.data.objects),
        "cameras": sum(obj.type == "CAMERA" for obj in bpy.data.objects),
        "lights": sum(obj.type == "LIGHT" for obj in bpy.data.objects),
    }
    if counts != EXPECTED:
        raise RuntimeError("BAC_HERO_OPEN_FAIL expected={} actual={}".format(EXPECTED, counts))
    camera = bpy.data.objects.get(DEFAULT_CAMERA)
    if camera is None or camera.type != "CAMERA":
        raise RuntimeError("BAC_HERO_OPEN_FAIL missing {}".format(DEFAULT_CAMERA))
    return counts


def _object_bounds(objects):
    from mathutils import Vector

    points = [obj.matrix_world @ Vector(corner) for obj in objects if obj.type == "MESH" for corner in obj.bound_box]
    if not points:
        raise RuntimeError("BAC_POOL_ASSETS_FAIL no mesh bounds")
    return (
        tuple(min(point[axis] for point in points) for axis in range(3)),
        tuple(max(point[axis] for point in points) for axis in range(3)),
    )


def _remove_pool_collection():
    bpy = _bpy()
    collection = bpy.data.collections.get(POOL_COLLECTION)
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def _append_pool_placement(asset_dir, collection, placement):
    bpy = _bpy()
    from mathutils import Matrix

    source = asset_dir / placement["file"]
    if not source.is_file() or _sha256(source) != POOL_ASSET_SHA256[placement["file"]]:
        raise RuntimeError("BAC_POOL_ASSETS_FAIL missing/changed asset: " + str(source))
    requested = set(placement.get("objects", ()))
    prefix = placement.get("prefix")
    with bpy.data.libraries.load(str(source), link=False) as (data_from, data_to):
        names = [name for name in data_from.objects if name in requested or (prefix and name.startswith(prefix))]
        if not names:
            raise RuntimeError("BAC_POOL_ASSETS_FAIL no approved objects in " + source.name)
        data_to.objects = names
    loaded = [obj for obj in data_to.objects if obj is not None]
    loaded_set = set(loaded)
    for obj in loaded:
        for owner in list(obj.users_collection):
            owner.objects.unlink(obj)
        collection.objects.link(obj)
    roots = [obj for obj in loaded if obj.parent not in loaded_set]
    initial = _object_bounds(loaded)
    center_bottom = (
        (initial[0][0] + initial[1][0]) * 0.5,
        (initial[0][1] + initial[1][1]) * 0.5,
        initial[0][2],
    )
    anchor = bpy.data.objects.new("BAC_POOL_" + placement["name"], None)
    collection.objects.link(anchor)
    shift = Matrix.Translation(tuple(-value for value in center_bottom))
    for obj in roots:
        world = obj.matrix_world.copy()
        obj.parent = anchor
        obj.matrix_world = shift @ world
    source_span = max(initial[1][0] - initial[0][0], initial[1][1] - initial[0][1])
    scale = placement["span"] / source_span
    anchor.scale = (scale, scale, scale)
    anchor.rotation_euler[2] = placement["rotation"]
    anchor.location = placement["location"]
    for obj in loaded:
        obj.name = "BAC_POOL_{}_{}".format(placement["name"], obj.name)
    bpy.context.view_layer.update()
    return anchor, loaded, _object_bounds(loaded)


def _verify_pool_scene():
    water = _bpy().data.objects.get(POOL_WATER_OBJECT)
    if water is None or water.type != "MESH":
        raise RuntimeError("BAC_POOL_ASSETS_FAIL missing " + POOL_WATER_OBJECT)
    actual = _object_bounds([water])
    for axis in range(3):
        for side in range(2):
            if abs(actual[side][axis] - POOL_WATER_BOUNDS[side][axis]) > 0.0000001:
                raise RuntimeError("BAC_POOL_ASSETS_FAIL pool bounds changed: {}".format(actual))
    return actual


def add_pool_assets(root, reset=True):
    """Place the approved pool set into locked, measured HERO-scene zones."""
    bpy = _bpy()
    _audit()
    water_bounds = _verify_pool_scene()
    if reset:
        _remove_pool_collection()
    elif bpy.data.collections.get(POOL_COLLECTION):
        raise RuntimeError("BAC_POOL_ASSETS_FAIL collection already exists; call with reset=True")
    collection = bpy.data.collections.new(POOL_COLLECTION)
    bpy.context.scene.collection.children.link(collection)
    asset_dir = Path(root).resolve() / "demos" / "teapot" / "hero" / "assets" / "pool"
    results = []
    for placement in POOL_PLACEMENTS:
        anchor, objects, bounds = _append_pool_placement(asset_dir, collection, placement)
        results.append((placement, anchor, objects, bounds))

    water_min, water_max = water_bounds
    for placement, _anchor, _objects, bounds in results:
        if placement["category"] == "float":
            if not (bounds[0][0] >= water_min[0] and bounds[1][0] <= water_max[0]
                    and bounds[0][1] >= water_min[1] and bounds[1][1] <= water_max[1]):
                raise RuntimeError("BAC_POOL_ASSETS_FAIL float outside pool: {} {}".format(placement["name"], bounds))
        elif placement["category"] == "chair" and bounds[0][0] <= water_max[0] + 0.00010:
            raise RuntimeError("BAC_POOL_ASSETS_FAIL chair intersects water: {} {}".format(placement["name"], bounds))
        elif placement["category"] == "furniture" and bounds[0][1] <= water_max[1] + 0.00050:
            raise RuntimeError("BAC_POOL_ASSETS_FAIL furniture not on north patio: {}".format(bounds))

    working = _hero_working_copy(root)
    bpy.ops.wm.save_as_mainfile(filepath=str(working))
    receipt = (
        "BAC_POOL_ASSETS_PASS floats=2 chairs=3 furniture=1 scene_scale=0.001 "
        "pool_x=-0.006503..-0.002648 pool_y=-0.011500..0.001001 working_copy={}"
    ).format(working)
    print(receipt)
    return receipt


def open_verified_hero(root):
    bpy = _bpy()
    master = _hero_master(root)
    working = _hero_working_copy(root)
    if not master.is_file() or master.stat().st_size != 1548410063:
        raise RuntimeError("BAC_HERO_OPEN_FAIL missing/wrong-size master: " + str(master))
    digest = _sha256(master)
    if digest != MASTER_SHA256:
        raise RuntimeError("BAC_HERO_MASTER_FAIL sha256={} expected={}".format(digest, MASTER_SHA256))
    current = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    if current != working.resolve():
        working.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(master, working)
        bpy.ops.wm.open_mainfile(filepath=str(working))
    counts = _audit()
    receipt = (
        "BAC_HERO_OPEN_PASS objects={objects} meshes={meshes} cameras={cameras} lights={lights} "
        "master_sha256={sha} working_copy={working}"
    ).format(sha=digest[:12], working=working, **counts)
    print(receipt)
    return receipt


def list_cameras():
    bpy = _bpy()
    names = sorted(obj.name for obj in bpy.data.objects if obj.type == "CAMERA")
    print("BAC_HERO_CAMERAS " + ",".join(names))
    return names


def render_hero(root, camera_name=DEFAULT_CAMERA, filename="bac_teapot_hero_source.png",
                resolution=(960, 540)):
    bpy = _bpy()
    _audit()
    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != "CAMERA":
        raise ValueError("unknown BAC HERO camera {!r}; choices={}".format(camera_name, list_cameras()))
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = map(int, resolution)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    output = Path(root).resolve() / "demos" / "teapot" / "hero" / "renders" / Path(filename).name
    output.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    if not output.is_file() or output.stat().st_size < 20_000:
        raise RuntimeError("BAC_HERO_RENDER_FAIL missing/undersized output: " + str(output))
    lane_marker = Path(root).resolve() / "demos" / "teapot" / "work" / "active_render_lane.txt"
    lane_marker.parent.mkdir(parents=True, exist_ok=True)
    lane_marker.write_text("bac_hero\n{}\n".format(output), encoding="utf-8")
    receipt = "BAC_HERO_RENDER_PASS camera={} output={} bytes={}".format(
        camera_name, output, output.stat().st_size)
    print(receipt)
    return receipt
