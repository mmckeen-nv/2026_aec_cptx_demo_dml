"""Deterministic Blender operations for the operator-approved quick scene."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path


EXPECTED = {"objects": 98, "meshes": 94, "cameras": 2, "lights": 2}
EXPECTED_MATERIALS = {
    "Bronze",
    "CoastalCliff",
    "DarkSteel",
    "Glass",
    "GrayConcrete",
    "PoolWater",
    "WhiteConcrete",
    "Wood",
    "WoodSlats_Vertical",
}
MASTER_SHA256 = "b62312601e6d0b1b448f8089984a7a527235c40f518d6d768ae1103d8716ba35"
DEFAULT_CAMERA = "ocean_view"


def _bpy():
    import bpy

    return bpy


def _quick_master(root):
    return (
        Path(root).resolve()
        / "demos"
        / "cliff_house"
        / "hero"
        / "cliff_house_QUICK_MASTER.blend"
    )


def _quick_working_copy(root):
    return (
        Path(root).resolve()
        / "demos"
        / "cliff_house"
        / "hero"
        / "work"
        / "cliff_house_QUICK_working.blend"
    )


def _audit():
    bpy = _bpy()
    counts = {
        "objects": len(bpy.data.objects),
        "meshes": sum(obj.type == "MESH" for obj in bpy.data.objects),
        "cameras": sum(obj.type == "CAMERA" for obj in bpy.data.objects),
        "lights": sum(obj.type == "LIGHT" for obj in bpy.data.objects),
    }
    if counts != EXPECTED:
        raise RuntimeError(
            "CLIFF_QUICK_OPEN_FAIL expected={} actual={}".format(EXPECTED, counts)
        )
    material_names = {material.name for material in bpy.data.materials}
    missing_materials = EXPECTED_MATERIALS - material_names
    unassigned = [
        obj.name
        for obj in bpy.data.objects
        if obj.type == "MESH" and not obj.data.materials
    ]
    if missing_materials or unassigned:
        raise RuntimeError(
            "CLIFF_QUICK_MATERIAL_FAIL missing={} unassigned={}".format(
                sorted(missing_materials), unassigned
            )
        )
    camera = bpy.data.objects.get(DEFAULT_CAMERA)
    if camera is None or camera.type != "CAMERA":
        raise RuntimeError(
            "CLIFF_QUICK_OPEN_FAIL missing camera {}".format(DEFAULT_CAMERA)
        )
    return counts


def open_verified_quick(root):
    bpy = _bpy()
    master = _quick_master(root)
    working = _quick_working_copy(root)
    if not master.is_file() or master.stat().st_size < 100_000:
        raise RuntimeError(
            "CLIFF_QUICK_OPEN_FAIL missing/undersized master: " + str(master)
        )
    digest = hashlib.sha256(master.read_bytes()).hexdigest()
    if digest != MASTER_SHA256:
        raise RuntimeError(
            "CLIFF_QUICK_MASTER_FAIL sha256={} expected={}".format(
                digest, MASTER_SHA256
            )
        )
    current = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None
    working_matches_master = (
        working.is_file()
        and hashlib.sha256(working.read_bytes()).hexdigest() == digest
    )
    if current != working.resolve() or not working_matches_master:
        working.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(master, working)
        bpy.ops.wm.open_mainfile(filepath=str(working))
    counts = _audit()
    receipt = (
        "CLIFF_QUICK_OPEN_PASS objects={objects} meshes={meshes} "
        "cameras={cameras} lights={lights} master_sha256={sha} "
        "working_copy={working}"
    ).format(sha=digest[:12], working=working, **counts)
    print(receipt)
    return receipt


def list_cameras():
    bpy = _bpy()
    names = sorted(obj.name for obj in bpy.data.objects if obj.type == "CAMERA")
    print("CLIFF_QUICK_CAMERAS " + ",".join(names))
    return names


def render_quick(
    root,
    camera_name=DEFAULT_CAMERA,
    filename="cliff_house_quick_source.png",
    resolution=(960, 540),
    samples=16,
):
    bpy = _bpy()
    _audit()
    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != "CAMERA":
        raise ValueError(
            "unknown QUICK camera {!r}; choices={}".format(
                camera_name, list_cameras()
            )
        )
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.resolution_x, scene.render.resolution_y = map(int, resolution)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    if hasattr(scene, "cycles"):
        scene.cycles.samples = int(samples)
    output = (
        Path(root).resolve()
        / "demos"
        / "cliff_house"
        / "hero"
        / "renders"
        / Path(filename).name
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
    if not output.is_file() or output.stat().st_size < 20_000:
        raise RuntimeError(
            "CLIFF_QUICK_RENDER_FAIL missing/undersized output: " + str(output)
        )
    receipt = "CLIFF_QUICK_RENDER_PASS camera={} output={} bytes={}".format(
        camera_name, output, output.stat().st_size
    )
    print(receipt)
    return receipt
