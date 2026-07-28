"""Clear render-mesh terrain beneath the Cliff House hardscape.

Run this inside Blender after the fresh Rhino mesh bridge is imported. The
canonical NURBS terrain remains authoritative in Rhino; this removes only
occluded presentation-mesh faces that would otherwise rise through the patio,
pool, building pad, or driveway.
"""

from __future__ import annotations

import json

import bmesh
import bpy
from mathutils import Vector


TERRAIN_NAME = "SITE_TERRAIN"
HARDSCAPE_NAMES = ("PATIO", "BUILDING_PAD", "DRIVEWAY")
POOL_WATER_NAME = "INFINITY_POOL_WATER"
CLEARANCE_METRES = 0.03
MIN_WATER_ABOVE_PATIO_METRES = 0.015
SUBDIVISION_CUTS = 2
CLEARANCE_VERSION = 2


def world_bounds(obj):
    # Blender 5.2 exposes bound_box corners as bpy_prop_array values rather
    # than mathutils vectors, so normalize them before matrix multiplication.
    corners = [obj.matrix_world @ Vector(obj_point) for obj_point in obj.bound_box]
    return (
        (
            min(point.x for point in corners),
            min(point.y for point in corners),
            min(point.z for point in corners),
        ),
        (
            max(point.x for point in corners),
            max(point.y for point in corners),
            max(point.z for point in corners),
        ),
    )


def expanded_xy_bounds(obj, clearance=CLEARANCE_METRES):
    minimum, maximum = world_bounds(obj)
    return (
        minimum[0] - clearance,
        maximum[0] + clearance,
        minimum[1] - clearance,
        maximum[1] + clearance,
    )


def face_center_inside_xy(face, matrix_world, bounds):
    point = matrix_world @ face.calc_center_median()
    min_x, max_x, min_y, max_y = bounds
    return min_x <= point.x <= max_x and min_y <= point.y <= max_y


def clear_terrain_under_hardscape():
    terrain = bpy.data.objects.get(TERRAIN_NAME)
    if terrain is None or terrain.type != "MESH":
        raise RuntimeError(f"Missing mesh object: {TERRAIN_NAME}")

    missing = [name for name in HARDSCAPE_NAMES if bpy.data.objects.get(name) is None]
    if missing:
        raise RuntimeError(f"Missing hardscape objects: {missing}")

    hardscape_bounds = [
        expanded_xy_bounds(bpy.data.objects[name]) for name in HARDSCAPE_NAMES
    ]
    mesh = terrain.data
    before_faces = len(mesh.polygons)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    if terrain.get("terrain_clearance_version") != CLEARANCE_VERSION:
        bmesh.ops.subdivide_edges(
            bm,
            edges=list(bm.edges),
            cuts=SUBDIVISION_CUTS,
            use_grid_fill=True,
        )
    subdivided_faces = len(bm.faces)
    faces_to_delete = [
        face
        for face in bm.faces
        if any(
            face_center_inside_xy(face, terrain.matrix_world, bounds)
            for bounds in hardscape_bounds
        )
    ]
    bmesh.ops.delete(bm, geom=faces_to_delete, context="FACES")
    orphaned_vertices = [vertex for vertex in bm.verts if not vertex.link_faces]
    if orphaned_vertices:
        bmesh.ops.delete(bm, geom=orphaned_vertices, context="VERTS")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    terrain["terrain_clearance_version"] = CLEARANCE_VERSION

    water = bpy.data.objects.get(POOL_WATER_NAME)
    patio = bpy.data.objects.get("PATIO")
    if water is None or patio is None:
        raise RuntimeError("Missing pool water or patio object")
    water_bounds = world_bounds(water)
    patio_bounds = world_bounds(patio)
    water_above_patio = water_bounds[1][2] - patio_bounds[1][2]
    if water_above_patio < MIN_WATER_ABOVE_PATIO_METRES:
        raise RuntimeError(
            "Pool water is not safely above the patio: "
            f"{water_above_patio:.6f} m"
        )

    pool_xy = expanded_xy_bounds(water, clearance=0.0)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    pool_overlap_faces = sum(
        1
        for face in bm.faces
        if face_center_inside_xy(face, terrain.matrix_world, pool_xy)
    )
    bm.free()
    if pool_overlap_faces:
        raise RuntimeError(
            f"Terrain still overlaps the pool footprint: {pool_overlap_faces} faces"
        )

    result = {
        "status": "PASS",
        "terrain": TERRAIN_NAME,
        "faces_before": before_faces,
        "faces_after_subdivision": subdivided_faces,
        "faces_removed": len(faces_to_delete),
        "faces_after": len(mesh.polygons),
        "subdivision_cuts": SUBDIVISION_CUTS,
        "clearance_method": "subdivided_face_centroid_in_exact_footprint",
        "protected_hardscape": list(HARDSCAPE_NAMES),
        "pool_terrain_overlap_faces": pool_overlap_faces,
        "pool_water_above_patio_metres": round(water_above_patio, 6),
    }
    print("TERRAIN_HARDSCAPE_CLEARANCE_PASS " + json.dumps(result))
    return result


if __name__ == "__main__":
    clear_terrain_under_hardscape()
