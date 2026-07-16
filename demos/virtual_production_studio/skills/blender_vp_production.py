"""Tested Blender utilities for the VP production phase.

This module does not design or build the studio. It resolves approved cached
assets, imports one asset, fits it to an existing Rhino proxy, and provides the
known-good Blender camera/render operations that should not be re-invented.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def _expected_handoff_path():
    root = os.environ.get("AEC_DEMO_ROOT")
    if not root:
        return None
    return Path(root) / "demos" / "virtual_production_studio" / "rhino" / "vp_studio_01.3dm"

ASSET_EXTENSIONS = (".glb", ".blend")
INCH_TO_METER = 0.0254
CAMERA_PRESETS_INCHES = {
    "stage_wide": {
        "manifest_camera": "VP_PRESENTATION_STAGE_WIDE",
        "location": (0.0, -588.0, 144.0),
        "target": (-120.0, 120.0, 96.0),
        "lens_mm": 20.0,
        "hide_for_render": (),
    },
    "stage_three_quarter": {
        "manifest_camera": "VP_PRESENTATION_THREE_QUARTER",
        "location": (600.0, -588.0, 168.0),
        "target": (-120.0, 120.0, 108.0),
        "lens_mm": 24.0,
        "hide_for_render": (),
    },
    "hero": {
        "manifest_camera": "CAM_A_HERO_TRACKED",
        "location": (-120.0, -420.0, 66.0),
        "target": (-120.0, -60.0, 72.0),
        "lens_mm": 28.0,
        "hide_for_render": ("CAM_A_HERO_TRACKED_BODY",),
    },
    "diagonal": {
        "manifest_camera": "CAM_E_WITNESS",
        "location": (600.0, -540.0, 120.0),
        "target": (-120.0, 0.0, 72.0),
        "lens_mm": 24.0,
        "hide_for_render": ("CAM_E_WITNESS_BODY",),
    },
    "control_room": {
        "manifest_camera": "CAM_F_CONTROL_ROOM",
        "location": (750.0, 684.0, 66.0),
        "target": (-120.0, 0.0, 72.0),
        "lens_mm": 28.0,
        "hide_for_render": ("CONTROL_VIEW_GLAZING",),
    },
}
ASSET_ALIASES = {
    "camera_tripod": "camera_tripod_silver_key",
    "director_chair": "chair_director_creativejenna",
    "monitor": "control_monitor_datsketch",
    "roadcase": "roadcase_thomas_kole",
    "grip_light": "grip_c_stand_kilianpohl",
}
FIXED_ASSET_PLACEMENT = {
    "camera_tripod_silver_key": {"source_size_m": (4.258815, 4.392436, 10.697300), "scale_xyz": (0.286276816, 0.277568074, 0.170959027), "target_size_in": (48.0, 48.0, 72.0), "anchor": "world_floor"},
    "chair_director_creativejenna": {"source_size_m": (34.020267, 34.020271, 20.453735), "scale_xyz": (0.016425503, 0.016425501, 0.044705771), "target_size_in": (22.0, 22.0, 36.0), "anchor": "proxy_floor"},
    "control_monitor_datsketch": {"source_size_m": (252.750580, 831.104492, 549.273865), "scale_xyz": (0.000602966, 0.000733482, 0.000832372), "target_size_in": (6.0, 24.0, 18.0), "anchor": "proxy_top"},
    "roadcase_thomas_kole": {"source_size_m": (452.888000, 260.606750, 424.406189), "scale_xyz": (0.002692056, 0.002339157, 0.001795450), "target_size_in": (48.0, 24.0, 30.0), "anchor": "proxy_floor"},
    "grip_c_stand_kilianpohl": {"source_size_m": (0.783726, 0.751831, 1.025059), "scale_xyz": (1.166734292, 1.216230775, 2.081441166), "target_size_in": (36.0, 36.0, 84.0), "anchor": "proxy_floor"},
    "light_led_soft_panel_roy": {"source_size_m": (0.566704, 0.579315, 1.510474), "scale_xyz": (1.075693837, 1.052277258, 1.210745766), "target_size_in": (24.0, 24.0, 72.0), "anchor": "proxy_floor"},
    "control_server_rack_anais": {"source_size_m": (2.255901, 1.874858, 2.672694), "scale_xyz": (0.270224624, 0.569003093, 0.798295652), "target_size_in": (24.0, 42.0, 84.0), "anchor": "proxy_floor"},
}
REQUIRED_SET_DRESSING = {
    "camera_tripod_silver_key": (
        "CAM_A_HERO_TRACKED_BODY", "CAM_B_DOLLY_TRACKED_BODY", "CAM_E_WITNESS_BODY",
    ),
    "chair_director_creativejenna": (
        "REVIEW_CHAIR_01", "REVIEW_CHAIR_02", "REVIEW_CHAIR_03",
        "REVIEW_CHAIR_04", "REVIEW_CHAIR_05", "REVIEW_CHAIR_06",
        "STAGE_DIRECTOR_CHAIR_01", "STAGE_DIRECTOR_CHAIR_02",
    ),
    "control_monitor_datsketch": tuple(
        "WORKSTATION_{:02d}".format(index) for index in range(1, 7)
    ),
    "roadcase_thomas_kole": (
        "ROAD_CASE_01", "ROAD_CASE_02", "ROAD_CASE_03", "ROAD_CASE_04",
        "HERO_ROAD_CASE_01", "HERO_ROAD_CASE_02",
    ),
    "light_led_soft_panel_roy": ("FLOOR_LIGHT_01", "FLOOR_LIGHT_02"),
    "control_server_rack_anais": ("SERVER_RACK_01", "SERVER_RACK_02"),
}
MATERIAL_PALETTE = {
    "M_LED_Emissive": {
        "base_color": (0.012, 0.025, 0.055, 1.0),
        "metallic": 0.05,
        "roughness": 0.24,
        "emission_color": (0.015, 0.10, 0.55, 1.0),
        "emission_strength": 1.8,
    },
    "M_Concrete_Neutral": {
        "base_color": (0.16, 0.18, 0.20, 1.0),
        "metallic": 0.0,
        "roughness": 0.78,
    },
    "M_Metal_Dark": {
        "base_color": (0.035, 0.045, 0.060, 1.0),
        "metallic": 0.88,
        "roughness": 0.28,
    },
    "M_Fabric_Dark": {
        "base_color": (0.055, 0.070, 0.095, 1.0),
        "metallic": 0.0,
        "roughness": 0.88,
    },
    "M_Equipment_Black": {
        "base_color": (0.012, 0.016, 0.024, 1.0),
        "metallic": 0.32,
        "roughness": 0.34,
    },
    "M_Wall_Neutral": {
        "base_color": (0.34, 0.38, 0.44, 1.0),
        "metallic": 0.0,
        "roughness": 0.64,
    },
    "M_Glass_Clear": {
        "base_color": (0.12, 0.22, 0.30, 1.0),
        "metallic": 0.0,
        "roughness": 0.08,
        "transmission_weight": 0.92,
        "ior": 1.45,
    },
    "M_Proxy_Neutral": {
        "base_color": (0.20, 0.23, 0.28, 1.0),
        "metallic": 0.0,
        "roughness": 0.58,
    },
}
PRODUCTION_LIGHTS = {
    "VP_KEY_AREA": {
        "location": (-3.0, -6.5, 8.5),
        "target": (-3.0, -1.5, 1.8),
        "energy": 6000.0,
        "size": 7.0,
        "color": (1.0, 0.78, 0.62),
    },
    "VP_FILL_AREA": {
        "location": (7.0, -1.0, 6.5),
        "target": (-2.0, -0.5, 1.8),
        "energy": 3500.0,
        "size": 9.0,
        "color": (0.58, 0.72, 1.0),
    },
    "VP_RIM_AREA": {
        "location": (-5.0, 7.0, 7.5),
        "target": (-3.0, -1.5, 2.0),
        "energy": 4500.0,
        "size": 6.0,
        "color": (0.30, 0.52, 1.0),
    },
    "VP_STAGE_SOFTBOX": {
        "location": (-3.0, -1.0, 10.5),
        "target": (-3.0, -1.5, 0.0),
        "energy": 5000.0,
        "size": 8.0,
        "color": (0.92, 0.96, 1.0),
    },
    "VP_FRONT_WASH": {
        "location": (0.0, -10.0, 5.5),
        "target": (-3.0, 2.0, 2.0),
        "energy": 6000.0,
        "size": 12.0,
        "color": (0.82, 0.90, 1.0),
    },
}
LEGACY_SCENE_OBJECTS = {"vp_studio_01_export", "CamTarget"}
LEGACY_SCENE_PREFIXES = ("test_cube", "camera_fix", "codex_test_cam")


def _validated_handoff_meshes():
    import bpy
    import hashlib

    root = bpy.data.collections.get("VP_STUDIO_RHINO")
    if root is None:
        return []
    handoff = _expected_handoff_path()
    if handoff is not None:
        if not handoff.is_file():
            return []
        digest = hashlib.sha256(handoff.read_bytes()).hexdigest()
        if str(root.get("source_3dm_sha256", "")) != digest:
            return []
    return [obj for obj in root.all_objects if obj.type == "MESH"]


def remove_legacy_scene_debris(require_handoff=True):
    """Remove known stale aggregate/test objects without touching the handoff."""
    import bpy

    handoff = _validated_handoff_meshes()
    if require_handoff and not handoff:
        raise RuntimeError(
            "VP_STUDIO_RHINO handoff is absent; run the checked-in 3dm importer before production cleanup"
        )
    removed = []
    for obj in list(bpy.data.objects):
        lower = obj.name.lower()
        if obj.name in LEGACY_SCENE_OBJECTS or lower.startswith(LEGACY_SCENE_PREFIXES):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def save_production_checkpoint(project_root):
    """Save only after a real validated handoff is present in the scene."""
    import bpy

    handoff = _validated_handoff_meshes()
    if not handoff:
        raise RuntimeError("refusing to save production scene without VP_STUDIO_RHINO meshes")
    target = (
        Path(project_root)
        / "demos"
        / "virtual_production_studio"
        / "blender_assets"
        / "vp_studio_01.blend"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    if not target.is_file() or target.stat().st_size <= 1024:
        raise RuntimeError("Blender checkpoint missing or empty: " + str(target))
    return str(target), len(handoff)


def import_current_handoff(project_root, reset_scene=True):
    """Reset Blender and import only this run's validated canonical handoff."""
    import bpy
    import importlib.util

    project_root = Path(project_root)
    handoff = project_root / "demos" / "virtual_production_studio" / "rhino" / "vp_studio_01.3dm"
    importer_path = project_root / "skills" / "import_with_metadata.py"
    if not handoff.is_file():
        raise RuntimeError("missing canonical VP handoff: " + str(handoff))
    if not importer_path.is_file():
        raise RuntimeError("missing checked-in VP importer: " + str(importer_path))
    spec = importlib.util.spec_from_file_location("vp_import_current_handoff", importer_path)
    importer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(importer)
    audit = importer.inspect_3dm(str(handoff))
    if audit["joined_meshes"] <= 0 or audit["invalid_joined_meshes"] != 0:
        raise RuntimeError("invalid joined-mesh handoff: " + repr(audit))
    required = {
        "LED_ACTIVE_WALL": (0.0, 288.0),
        "LED_REAR_SUPPORT": (0.0, 312.0),
    }
    for name, (z0, z1) in required.items():
        bounds = audit["joined_bounds"].get(name)
        if bounds is None:
            raise RuntimeError("canonical handoff is missing required object: " + name)
        if abs(bounds["min"][2] - z0) > 0.05 or abs(bounds["max"][2] - z1) > 0.05:
            raise RuntimeError("canonical handoff has invalid LED Z bounds: {} {}".format(name, bounds))
    if reset_scene:
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for collection in list(bpy.data.collections):
            bpy.data.collections.remove(collection)
    imported, skipped, layers = importer.import_3dm(
        str(handoff), root_name="VP_STUDIO_RHINO", replace_existing=True
    )
    if imported != audit["joined_meshes"]:
        raise RuntimeError("VP handoff count mismatch imported={} expected={}".format(imported, audit["joined_meshes"]))
    signature = importer.assert_import_matches_source(str(handoff), root_name="VP_STUDIO_RHINO")
    print("VP_HANDOFF_PASS imported={} skipped={} layers={} sha256={}".format(
        imported, skipped, len(layers), signature["sha256"]
    ))
    return {
        "imported": imported,
        "skipped": skipped,
        "layers": len(layers),
        "sha256": signature["sha256"],
        "handoff": str(handoff),
    }


def cache_roots(project_root):
    project_root = Path(project_root)
    candidates = [
        project_root / "demos" / "virtual_production_studio" / "assets" / "cache",
        Path(r"G:\AEC-CPTX\demos\virtual_production_studio\assets\cache"),
    ]
    roots = []
    for candidate in candidates:
        if candidate.is_dir() and candidate not in roots:
            roots.append(candidate)
    return roots


def resolve_cached_asset(project_root, asset_key):
    project_root = Path(project_root)
    asset_key = ASSET_ALIASES.get(asset_key, asset_key)
    index_path = project_root / "demos" / "virtual_production_studio" / "assets" / "cache" / "cache_index.json"
    if not index_path.is_file():
        raise RuntimeError("missing cache index: " + str(index_path))
    index = json.loads(index_path.read_text(encoding="utf-8"))
    entry = next((item for item in index.get("cached", []) if item.get("asset", {}).get("key") == asset_key), None)
    if entry is None:
        raise RuntimeError("asset key not present in cache index: " + asset_key)
    indexed = [item.get("path", "") for item in entry.get("files", [])]
    for extension in ASSET_EXTENSIONS:
        for relative in indexed:
            if Path(relative).suffix.lower() != extension:
                continue
            for root in cache_roots(project_root):
                candidate = root / Path(relative)
                if candidate.is_file():
                    return str(candidate)
    raise RuntimeError("approved asset payload is absent from local and external cache: " + asset_key)


def import_cached_asset(project_root, asset_key, collection_name=None):
    import bpy

    path = resolve_cached_asset(project_root, asset_key)
    collection_name = collection_name or ("ASSET_" + asset_key.upper())
    old = bpy.data.collections.get(collection_name)
    if old is not None:
        for obj in list(old.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)
    before = set(bpy.data.objects)
    suffix = Path(path).suffix.lower()
    if suffix == ".glb":
        bpy.ops.import_scene.gltf(filepath=path)
        imported = [obj for obj in bpy.data.objects if obj not in before]
    elif suffix == ".blend":
        with bpy.data.libraries.load(path, link=False) as (source, destination):
            destination.objects = list(source.objects)
        imported = [obj for obj in destination.objects if obj is not None]
        for obj in imported:
            if not obj.users_collection:
                collection.objects.link(obj)
    else:
        raise RuntimeError("unsupported cached asset type: " + suffix)
    if not imported:
        raise RuntimeError("asset import produced no objects: " + path)
    for obj in imported:
        for owner in list(obj.users_collection):
            if owner != collection:
                owner.objects.unlink(obj)
        if collection.objects.get(obj.name) is None:
            collection.objects.link(obj)
        obj["asset_key"] = asset_key
        obj["asset_source_path"] = path
    return imported, collection, path


def _world_bounds(objects):
    from mathutils import Vector

    points = []
    for obj in objects:
        if hasattr(obj, "bound_box"):
            points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        raise RuntimeError("no bounded objects supplied")
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def fit_to_proxy(imported_objects, proxy, fill=0.9, rotation_xyz=(0.0, 0.0, 0.0)):
    import bpy
    from mathutils import Euler, Matrix, Vector

    if proxy is None or proxy.type != "MESH":
        raise RuntimeError("a mesh proxy is required")
    source_min, source_max = _world_bounds(imported_objects)
    target_min, target_max = _world_bounds([proxy])
    source_size = source_max - source_min
    target_size = target_max - target_min
    ratios = [target_size[i] / source_size[i] for i in range(3) if source_size[i] > 1e-6]
    if not ratios:
        raise RuntimeError("asset has zero-size bounds")
    scale = min(ratios) * float(fill)
    source_anchor = Vector(((source_min.x + source_max.x) / 2, (source_min.y + source_max.y) / 2, source_min.z))
    target_anchor = Vector(((target_min.x + target_max.x) / 2, (target_min.y + target_max.y) / 2, target_min.z))
    transform = Matrix.Translation(target_anchor) @ Euler(rotation_xyz, "XYZ").to_matrix().to_4x4() @ Matrix.Scale(scale, 4) @ Matrix.Translation(-source_anchor)
    for obj in imported_objects:
        obj.matrix_world = transform @ obj.matrix_world
    proxy.hide_render = True
    proxy["replacement_asset"] = imported_objects[0].get("asset_key", "")
    bpy.context.view_layer.update()
    return scale


def place_cached_asset(project_root, asset_key, proxy_name, collection_name=None):
    """Import with a measured fixed XYZ scale and role-specific anchor."""
    import bpy
    from mathutils import Matrix, Vector

    if not _validated_handoff_meshes():
        raise RuntimeError("current VP_STUDIO_RHINO handoff is absent or stale; re-run the checked-in importer")

    canonical_key = ASSET_ALIASES.get(asset_key, asset_key)
    if canonical_key == "grip_c_stand_kilianpohl":
        raise RuntimeError(
            "bare C-stand placement is prohibited; use light_led_soft_panel_roy "
            "for a complete practical-light assembly"
        )
    spec = FIXED_ASSET_PLACEMENT.get(canonical_key)
    if spec is None:
        raise RuntimeError("asset has no approved fixed placement spec: " + canonical_key)
    proxy = bpy.data.objects.get(proxy_name)
    if proxy is None or proxy.type != "MESH":
        raise RuntimeError("placement proxy is missing or is not a mesh: " + proxy_name)
    if canonical_key in {"grip_c_stand_kilianpohl", "light_led_soft_panel_roy"} and proxy_name.startswith("STAGE_LIGHT_"):
        raise RuntimeError("floor-standing light assets cannot replace overhead STAGE_LIGHT proxies")
    collection_name = collection_name or ("ASSET_" + proxy_name)
    imported, collection, path = import_cached_asset(project_root, canonical_key, collection_name)
    source_min, source_max = _world_bounds(imported)
    source_size = source_max - source_min
    expected_source = Vector(spec["source_size_m"])
    for axis in range(3):
        tolerance = max(0.002, expected_source[axis] * 0.001)
        if abs(source_size[axis] - expected_source[axis]) > tolerance:
            raise RuntimeError("cached asset bounds changed for {} axis {}: actual={} expected={}".format(canonical_key, axis, source_size[axis], expected_source[axis]))
    proxy_min, proxy_max = _world_bounds([proxy])
    target_anchor = Vector(((proxy_min.x + proxy_max.x) / 2.0, (proxy_min.y + proxy_max.y) / 2.0, proxy_min.z))
    if spec["anchor"] == "world_floor":
        target_anchor.z = 0.0
    elif spec["anchor"] == "proxy_top":
        target_anchor.z = proxy_max.z
    elif spec["anchor"] != "proxy_floor":
        raise RuntimeError("unknown fixed anchor mode: " + spec["anchor"])
    source_anchor = Vector(((source_min.x + source_max.x) / 2.0, (source_min.y + source_max.y) / 2.0, source_min.z))
    sx, sy, sz = spec["scale_xyz"]
    transform = Matrix.Translation(target_anchor) @ Matrix.Diagonal((sx, sy, sz, 1.0)) @ Matrix.Translation(-source_anchor)
    imported_set = set(imported)
    imported_roots = [obj for obj in imported if obj.parent not in imported_set]
    if not imported_roots:
        raise RuntimeError("cached asset import has no transform root: " + canonical_key)
    for obj in imported_roots:
        obj.matrix_world = transform @ obj.matrix_world
    for obj in imported:
        obj["placement_proxy"] = proxy_name
        obj["fixed_scale_xyz"] = "{:.9f},{:.9f},{:.9f}".format(sx, sy, sz)
    proxy.hide_render = True
    proxy["replacement_asset"] = canonical_key
    bpy.context.view_layer.update()
    final_min, final_max = _world_bounds(imported)
    final_size = final_max - final_min
    target_size = Vector(tuple(value * INCH_TO_METER for value in spec["target_size_in"]))
    for axis in range(3):
        if abs(final_size[axis] - target_size[axis]) > 0.003:
            raise RuntimeError("fixed placement size verification failed for {} axis {}: actual={} target={}".format(canonical_key, axis, final_size[axis], target_size[axis]))
    return imported, collection, path, tuple(final_size)


def apply_required_set_dressing(project_root):
    """Replace the required hero-visible proxies and emit one bounded receipt."""
    import bpy

    expected = sum(len(names) for names in REQUIRED_SET_DRESSING.values())
    missing = [
        proxy_name
        for names in REQUIRED_SET_DRESSING.values()
        for proxy_name in names
        if bpy.data.objects.get(proxy_name) is None
    ]
    if missing:
        raise RuntimeError(
            "VP_SET_DRESSING_FAIL missing proxies: " + ", ".join(missing)
        )
    placed = []
    for asset_key, proxy_names in REQUIRED_SET_DRESSING.items():
        for proxy_name in proxy_names:
            imported, _collection, _path, _size = place_cached_asset(
                project_root, asset_key, proxy_name
            )
            if not imported:
                raise RuntimeError("VP_SET_DRESSING_FAIL empty asset: " + proxy_name)
            placed.append((asset_key, proxy_name))
    bare_stands = [
        obj.name
        for obj in bpy.data.objects
        if obj.get("asset_key") == "grip_c_stand_kilianpohl" and not obj.hide_render
    ]
    if bare_stands:
        raise RuntimeError(
            "VP_SET_DRESSING_FAIL bare C-stands are prohibited: "
            + ", ".join(bare_stands[:5])
        )
    if len(placed) != expected:
        raise RuntimeError(
            "VP_SET_DRESSING_FAIL placed={} expected={}".format(len(placed), expected)
        )
    print(
        "VP_SET_DRESSING_PASS categories={} placements={} cameras=3 chairs=8 "
        "monitors=6 roadcases=6 practical_lights=2 racks=2".format(
            len(REQUIRED_SET_DRESSING), len(placed)
        )
    )
    return {"categories": len(REQUIRED_SET_DRESSING), "placements": len(placed)}


def aim_camera(camera, location, target, lens_mm=28.0):
    import bpy
    from mathutils import Vector

    camera.location = Vector(location)
    direction = Vector(target) - camera.location
    if direction.length <= 1e-6:
        raise RuntimeError("camera location equals target")
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = float(lens_mm)
    bpy.context.view_layer.update()
    view_direction = (camera.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
    alignment = view_direction.dot(direction.normalized())
    if alignment < 0.999:
        raise RuntimeError("camera aim verification failed: alignment={:.6f}".format(alignment))
    return alignment


def _set_principled_input(shader, names, value):
    for name in names:
        socket = shader.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return name
    return None


def _material_from_spec(tag, spec):
    import bpy

    material = bpy.data.materials.get(tag) or bpy.data.materials.new(tag)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    shader = nodes.get("Principled BSDF")
    if shader is None:
        shader = next((node for node in nodes if node.type == "BSDF_PRINCIPLED"), None)
    if shader is None:
        raise RuntimeError("material has no Principled BSDF: " + tag)
    _set_principled_input(shader, ("Base Color",), spec["base_color"])
    _set_principled_input(shader, ("Metallic",), spec.get("metallic", 0.0))
    _set_principled_input(shader, ("Roughness",), spec.get("roughness", 0.5))
    _set_principled_input(shader, ("IOR",), spec.get("ior", 1.5))
    if "transmission_weight" in spec:
        _set_principled_input(
            shader,
            ("Transmission Weight", "Transmission"),
            spec["transmission_weight"],
        )
    if "emission_color" in spec:
        _set_principled_input(
            shader,
            ("Emission Color", "Emission"),
            spec["emission_color"],
        )
        _set_principled_input(
            shader,
            ("Emission Strength",),
            spec.get("emission_strength", 1.0),
        )
    material.diffuse_color = spec["base_color"]
    return material


def apply_production_materials():
    """Assign the fixed VP palette to imported Rhino meshes by metadata tag."""
    import bpy

    root = bpy.data.collections.get("VP_STUDIO_RHINO")
    if root is None or not root.all_objects:
        raise RuntimeError("VP_STUDIO_RHINO handoff is absent or empty")
    palette = {
        tag: _material_from_spec(tag, spec)
        for tag, spec in MATERIAL_PALETTE.items()
    }
    assigned = {}
    missing = []
    for obj in root.all_objects:
        if obj.type != "MESH":
            continue
        tag = str(obj.get("material", "M_Proxy_Neutral"))
        if tag not in palette:
            tag = "M_Proxy_Neutral"
        if obj.data is None:
            missing.append(obj.name)
            continue
        obj.data.materials.clear()
        obj.data.materials.append(palette[tag])
        assigned[tag] = assigned.get(tag, 0) + 1
    if missing:
        raise RuntimeError("material assignment found meshes without data: " + ", ".join(missing[:5]))
    if not assigned or assigned.get("M_LED_Emissive", 0) == 0:
        raise RuntimeError("production materials did not find an emissive LED mesh")
    print("VP_MATERIAL_PASS " + json.dumps(assigned, sort_keys=True))
    return assigned


def setup_production_lighting():
    """Create one deterministic studio-light rig without changing geometry."""
    import bpy
    from mathutils import Vector

    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("VP_WORLD")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    if background is not None:
        background.inputs["Color"].default_value = (0.018, 0.026, 0.045, 1.0)
        background.inputs["Strength"].default_value = 0.18
    created = []
    for name, spec in PRODUCTION_LIGHTS.items():
        light_obj = bpy.data.objects.get(name)
        if light_obj is not None and light_obj.type != "LIGHT":
            bpy.data.objects.remove(light_obj, do_unlink=True)
            light_obj = None
        if light_obj is None:
            data = bpy.data.lights.new(name=name, type="AREA")
            light_obj = bpy.data.objects.new(name, data)
            scene.collection.objects.link(light_obj)
        light_obj.data.type = "AREA"
        light_obj.data.energy = spec["energy"]
        light_obj.data.shape = "DISK"
        light_obj.data.size = spec["size"]
        light_obj.data.color = spec["color"]
        light_obj.location = Vector(spec["location"])
        direction = Vector(spec["target"]) - light_obj.location
        light_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        light_obj["vp_production_light"] = True
        created.append(name)
    scene.render.film_transparent = False
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except (TypeError, ValueError):
        scene.view_settings.look = "Medium High Contrast"
    scene.view_settings.exposure = 0.0
    print("VP_LIGHTING_PASS lights={} world_strength=0.18 exposure=0.0".format(len(created)))
    return created


def prepare_production_look():
    """Apply the fixed materials and lights and return one audit receipt."""
    assigned = apply_production_materials()
    lights = setup_production_lighting()
    return {"materials": assigned, "lights": lights}


def validate_render_image(
    output_path,
    min_contrast=0.025,
    min_range=0.08,
    min_mean=0.04,
    max_mean=0.82,
    min_foreground_fraction=0.06,
    min_center_mean=0.035,
    max_highlight_fraction=0.65,
):
    """Reject blank, uniformly gray, or catastrophically misframed renders."""
    import bpy

    image = bpy.data.images.load(os.path.abspath(output_path), check_existing=False)
    try:
        width, height = image.size
        if width < 64 or height < 64:
            raise RuntimeError("render is too small: {}x{}".format(width, height))
        pixels = image.pixels
        samples = []
        grid_x = 64
        grid_y = 36
        for gy in range(grid_y):
            y = min(height - 1, int((gy + 0.5) * height / grid_y))
            for gx in range(grid_x):
                x = min(width - 1, int((gx + 0.5) * width / grid_x))
                index = (y * width + x) * 4
                r, g, b = pixels[index], pixels[index + 1], pixels[index + 2]
                samples.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
        mean = sum(samples) / len(samples)
        variance = sum((value - mean) ** 2 for value in samples) / len(samples)
        contrast = variance ** 0.5
        ordered = sorted(samples)
        dynamic_range = ordered[int(len(ordered) * 0.90)] - ordered[int(len(ordered) * 0.10)]
        edge_samples = []
        center_samples = []
        for gy in range(grid_y):
            for gx in range(grid_x):
                value = samples[gy * grid_x + gx]
                if gx in (0, grid_x - 1) or gy in (0, grid_y - 1):
                    edge_samples.append(value)
                if grid_x // 4 <= gx < 3 * grid_x // 4 and grid_y // 4 <= gy < 3 * grid_y // 4:
                    center_samples.append(value)
        edge_ordered = sorted(edge_samples)
        background = edge_ordered[len(edge_ordered) // 2]
        foreground_fraction = sum(
            1 for value in samples if abs(value - background) >= 0.035
        ) / len(samples)
        highlight_fraction = sum(1 for value in samples if value >= 0.95) / len(samples)
        center_mean = sum(center_samples) / len(center_samples)
        if (
            contrast < min_contrast
            or dynamic_range < min_range
            or mean < min_mean
            or mean > max_mean
            or foreground_fraction < min_foreground_fraction
            or center_mean < min_center_mean
            or highlight_fraction > max_highlight_fraction
        ):
            raise RuntimeError(
                "VP_RENDER_REJECT blank/misframed render mean={:.4f} contrast={:.4f} "
                "range={:.4f} foreground={:.4f} center_mean={:.4f} highlights={:.4f}".format(
                    mean, contrast, dynamic_range, foreground_fraction, center_mean,
                    highlight_fraction,
                )
            )
        result = {
            "width": width,
            "height": height,
            "mean": round(mean, 4),
            "contrast": round(contrast, 4),
            "dynamic_range": round(dynamic_range, 4),
            "foreground_fraction": round(foreground_fraction, 4),
            "center_mean": round(center_mean, 4),
            "highlight_fraction": round(highlight_fraction, 4),
        }
        print("VP_RENDER_PASS " + json.dumps(result, sort_keys=True))
        return result
    finally:
        bpy.data.images.remove(image)


def setup_manifest_camera(preset="hero", name=None):
    """Create and aim one locked presentation camera in Blender metres."""
    import bpy

    if preset not in CAMERA_PRESETS_INCHES:
        raise RuntimeError("unknown VP camera preset: " + str(preset))
    remove_legacy_scene_debris()
    definition = CAMERA_PRESETS_INCHES[preset]
    name = name or ("VP_" + preset.upper() + "_CAMERA")
    camera = bpy.data.objects.get(name)
    if camera is None:
        data = bpy.data.cameras.new(name)
        camera = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(camera)
    elif camera.type != "CAMERA":
        raise RuntimeError("manifest hero camera name belongs to a non-camera object")
    for constraint in list(camera.constraints):
        camera.constraints.remove(constraint)
    hidden = []
    for object_name in definition.get("hide_for_render", ()):
        blocker = bpy.data.objects.get(object_name)
        if blocker is not None:
            blocker.hide_render = True
            blocker.hide_set(True)
            blocker["hidden_for_camera_preset"] = preset
            hidden.append(object_name)
    alignment = aim_camera(
        camera,
        tuple(value * INCH_TO_METER for value in definition["location"]),
        tuple(value * INCH_TO_METER for value in definition["target"]),
        definition["lens_mm"],
    )
    bpy.context.scene.camera = camera
    camera["manifest_camera"] = definition["manifest_camera"]
    camera["camera_preset"] = preset
    camera["source_units"] = "inches"
    camera["hidden_camera_blockers"] = ",".join(hidden)
    return camera, alignment


def setup_manifest_hero_camera(name="VP_HERO_CAMERA"):
    """Compatibility entry point for the required CAM_A beauty shot."""
    return setup_manifest_camera("hero", name=name)


def setup_beauty_camera(name="VP_BEAUTY_CAMERA"):
    """Use the unobstructed stage-wide presentation angle for the demo image."""
    return setup_manifest_camera("stage_wide", name=name)


def render_preview(output_path, resolution=(960, 540), samples=32):
    import bpy

    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    scene = bpy.context.scene
    if scene.camera is None:
        raise RuntimeError("scene has no active camera")
    scene.render.resolution_x = int(resolution[0])
    scene.render.resolution_y = int(resolution[1])
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = output_path
    if scene.render.engine == "CYCLES":
        scene.cycles.samples = int(samples)
    bpy.ops.render.render(write_still=True)
    if not os.path.isfile(output_path) or os.path.getsize(output_path) <= 1024:
        raise RuntimeError("preview render missing or empty: " + output_path)
    validate_render_image(output_path)
    return output_path
