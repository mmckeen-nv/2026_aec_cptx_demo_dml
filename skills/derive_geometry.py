"""Prototype-then-rebuild helpers for Blender.

Given a "messy" prototype mesh, extract clean reference curves/points/planes
that can be used to construct a clean replacement. The new geometry derives its
positions from the references -- no eyeballing.

Typical workflow:
    proto = bpy.data.objects["wall_garage_spandrel"]
    refs = extract_references(proto)
    # refs has 'edges', 'corner_points', 'face_planes'
    new_obj = build_axis_aligned_box(refs['corner_points'], material=...)
    bpy.data.objects.remove(proto)  # delete prototype
"""
import bpy
from mathutils import Vector

def extract_references(obj):
    """Return dict of clean geometric references from an existing mesh."""
    me = obj.data
    mw = obj.matrix_world
    # World-space vertex positions
    verts_w = [mw @ v.co for v in me.vertices]
    # World bounding box from actual verts (not cached bound_box)
    mn = Vector((min(v.x for v in verts_w), min(v.y for v in verts_w), min(v.z for v in verts_w)))
    mx = Vector((max(v.x for v in verts_w), max(v.y for v in verts_w), max(v.z for v in verts_w)))
    # 8 corner points
    corners = [Vector((x, y, z)) for x in (mn.x, mx.x) for y in (mn.y, mx.y) for z in (mn.z, mx.z)]
    # Face planes from face normals + centers (axis-aligned only)
    planes = []
    inv_t = mw.to_3x3().inverted().transposed()
    for face in me.polygons:
        n = inv_t @ face.normal
        if n.length < 1e-6: continue
        n = n.normalized()
        for ax in range(3):
            if abs(n[ax]) > 0.97:
                vw = [mw @ me.vertices[vi].co for vi in face.vertices]
                offset = sum(v[ax] for v in vw) / len(vw)
                planes.append({"axis": ax, "offset": offset, "normal_sign": 1 if n[ax] > 0 else -1})
                break
    return {"bbox_min": mn, "bbox_max": mx, "corners": corners,
            "face_planes": planes, "vertex_count": len(verts_w)}

def build_axis_aligned_box(min_corner, max_corner, name="DerivedBox", collection=None):
    """Build a clean 8-vertex 6-face axis-aligned box. Returns the new object."""
    mn = Vector(min_corner); mx = Vector(max_corner)
    verts = [
        (mn.x, mn.y, mn.z), (mx.x, mn.y, mn.z), (mx.x, mx.y, mn.z), (mn.x, mx.y, mn.z),
        (mn.x, mn.y, mx.z), (mx.x, mn.y, mx.z), (mx.x, mx.y, mx.z), (mn.x, mx.y, mx.z),
    ]
    faces = [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    me = bpy.data.meshes.new(name + "_mesh")
    me.from_pydata(verts, [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    if collection:
        collection.objects.link(obj)
    else:
        bpy.context.scene.collection.objects.link(obj)
    return obj

def shrink_face_inward(obj, axis, sign, amount_m=0.005, tol=0.001):
    """Pull the vertices of one face inward by amount_m. axis=0/1/2, sign=+1/-1."""
    if obj.data.users > 1:
        obj.data = obj.data.copy()
    me = obj.data
    coords_along = [v.co[axis] for v in me.vertices]
    target = max(coords_along) if sign > 0 else min(coords_along)
    moved = 0
    for v in me.vertices:
        if abs(v.co[axis] - target) < tol:
            v.co[axis] -= sign * amount_m
            moved += 1
    me.update()
    return moved

def offset_object(obj, axis, amount_m):
    """Translate the entire object on an axis."""
    obj.location[axis] += amount_m
