"""Deterministic Blender operations for the BAC Teapot house HERO lane."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


EXPECTED = {"objects": 506, "meshes": 257, "cameras": 6, "lights": 1}
MASTER_SHA256 = "350e19eb3db88cf5c98c98ba76f5d9f2017ed168b5fcf7e276a2c3bb13c7b882"
DEFAULT_CAMERA = "Camera_day"


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
    counts = {
        "objects": len(bpy.data.objects),
        "meshes": sum(obj.type == "MESH" for obj in bpy.data.objects),
        "cameras": sum(obj.type == "CAMERA" for obj in bpy.data.objects),
        "lights": sum(obj.type == "LIGHT" for obj in bpy.data.objects),
    }
    if counts != EXPECTED:
        raise RuntimeError("BAC_HERO_OPEN_FAIL expected={} actual={}".format(EXPECTED, counts))
    camera = bpy.data.objects.get(DEFAULT_CAMERA)
    if camera is None or camera.type != "CAMERA":
        raise RuntimeError("BAC_HERO_OPEN_FAIL missing {}".format(DEFAULT_CAMERA))
    return counts


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
