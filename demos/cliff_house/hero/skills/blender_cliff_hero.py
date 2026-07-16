"""Deterministic Blender operations for the Cliff House HERO quick lane."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


EXPECTED = {"objects": 183, "meshes": 174, "cameras": 7, "lights": 2}
MASTER_SHA256 = "d0756bfa299b89d51642bf5688eba875f68cf99a9a72978bc24fac1f23d4413a"


def _bpy():
    import bpy
    return bpy


def _hero_master(root):
    return Path(root).resolve() / "demos" / "cliff_house" / "hero" / "cliff_house_02_HERO.blend"


def _hero_working_copy(root):
    return Path(root).resolve() / "demos" / "cliff_house" / "hero" / "work" / "cliff_house_02_HERO_working.blend"


def _audit():
    bpy = _bpy()
    counts = {
        "objects": len(bpy.data.objects),
        "meshes": sum(obj.type == "MESH" for obj in bpy.data.objects),
        "cameras": sum(obj.type == "CAMERA" for obj in bpy.data.objects),
        "lights": sum(obj.type == "LIGHT" for obj in bpy.data.objects),
    }
    if counts != EXPECTED:
        raise RuntimeError("CLIFF_HERO_OPEN_FAIL expected={} actual={}".format(EXPECTED, counts))
    if bpy.data.objects.get("HeroCamera") is None:
        raise RuntimeError("CLIFF_HERO_OPEN_FAIL missing HeroCamera")
    return counts


def open_verified_hero(root):
    bpy = _bpy()
    master = _hero_master(root)
    working = _hero_working_copy(root)
    if not master.is_file() or master.stat().st_size < 100_000:
        raise RuntimeError("CLIFF_HERO_OPEN_FAIL missing/undersized master: " + str(master))
    digest = hashlib.sha256(master.read_bytes()).hexdigest()
    if digest != MASTER_SHA256:
        raise RuntimeError("CLIFF_HERO_MASTER_FAIL sha256={} expected={}".format(digest, MASTER_SHA256))
    current = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    if current != working.resolve():
        working.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(master, working)
        bpy.ops.wm.open_mainfile(filepath=str(working))
    counts = _audit()
    receipt = (
        "CLIFF_HERO_OPEN_PASS objects={objects} meshes={meshes} cameras={cameras} lights={lights} "
        "master_sha256={sha} working_copy={working}"
    ).format(sha=digest[:12], working=working, **counts)
    print(receipt)
    return receipt


def list_cameras():
    bpy = _bpy()
    names = sorted(obj.name for obj in bpy.data.objects if obj.type == "CAMERA")
    print("CLIFF_HERO_CAMERAS " + ",".join(names))
    return names


def render_hero(root, camera_name="HeroCamera", filename="cliff_house_hero_source.png",
                resolution=(960, 540), samples=32):
    bpy = _bpy()
    _audit()
    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != "CAMERA":
        raise ValueError("unknown HERO camera {!r}; choices={}".format(camera_name, list_cameras()))
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = map(int, resolution)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    if hasattr(scene, "cycles"):
        scene.cycles.samples = int(samples)
    output = Path(root).resolve() / "demos" / "cliff_house" / "hero" / "renders" / Path(filename).name
    output.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    if not output.is_file() or output.stat().st_size < 20_000:
        raise RuntimeError("CLIFF_HERO_RENDER_FAIL missing/undersized output: " + str(output))
    receipt = "CLIFF_HERO_RENDER_PASS camera={} output={} bytes={}".format(
        camera_name, output, output.stat().st_size)
    print(receipt)
    return receipt
