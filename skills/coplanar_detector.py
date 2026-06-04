"""Scene-level coplanar-face z-fight detector for Blender.

Bucket every axis-aligned face from every visible mesh by (axis, world_offset).
Pairs of faces from DIFFERENT objects landing in the same bucket with overlapping
projections are literal coplanar z-fights, regardless of rendering.

Usage:
    import sys
    sys.path.insert(0, "C:/Users/swags/Documents/aec_demo_master/skills")
    import coplanar_detector as cd
    pairs, offenders = cd.run(min_overlap_area=0.10, offset_resolution=0.005)
"""
import bpy
from mathutils import Vector
from collections import defaultdict, Counter

def run(normal_tol=0.97, offset_resolution=0.005,
        min_face_area=0.05, min_overlap_area=0.10, verbose=True):
    visible = [o for o in bpy.data.objects if o.type == "MESH" and o.visible_get()]
    buckets = defaultdict(list)
    for obj in visible:
        mw = obj.matrix_world
        inv_t = mw.to_3x3().inverted().transposed()
        for face in obj.data.polygons:
            n = inv_t @ face.normal
            if n.length < 1e-6: continue
            n = n.normalized()
            for ax in range(3):
                if abs(n[ax]) > normal_tol:
                    vw = [mw @ obj.data.vertices[vi].co for vi in face.vertices]
                    offset = sum(v[ax] for v in vw) / len(vw)
                    others = [i for i in range(3) if i != ax]
                    amn = min(v[others[0]] for v in vw); amx = max(v[others[0]] for v in vw)
                    bmn = min(v[others[1]] for v in vw); bmx = max(v[others[1]] for v in vw)
                    area = (amx - amn) * (bmx - bmn)
                    if area < min_face_area: break
                    key = (ax, round(offset / offset_resolution))
                    buckets[key].append((obj.name, offset, amn, amx, bmn, bmx, area))
                    break

    pairs = []
    for (ax, ob), faces in buckets.items():
        n = len(faces)
        if n < 2: continue
        for i in range(n):
            for j in range(i+1, n):
                f1, f2 = faces[i], faces[j]
                if f1[0] == f2[0]: continue
                a_ov = max(0, min(f1[3], f2[3]) - max(f1[2], f2[2]))
                b_ov = max(0, min(f1[5], f2[5]) - max(f1[4], f2[4]))
                ov = a_ov * b_ov
                if ov < min_overlap_area: continue
                pairs.append({
                    "overlap_m2": ov,
                    "gap_mm": abs(f1[1] - f2[1]) * 1000,
                    "axis": ["X", "Y", "Z"][ax],
                    "plane_offset": (f1[1] + f2[1]) / 2,
                    "obj1": f1[0],
                    "obj2": f2[0],
                })
    pairs.sort(key=lambda p: -p["overlap_m2"])
    offender_counter = Counter()
    for p in pairs:
        offender_counter[p["obj1"]] += 1
        offender_counter[p["obj2"]] += 1
    if verbose:
        print(f"Coplanar face pairs (>{min_overlap_area}m^2 overlap): {len(pairs)}")
        for p in pairs[:25]:
            print(f"  {p['overlap_m2']:6.2f}m^2 gap={p['gap_mm']:.1f}mm "
                  f"{p['axis']}={p['plane_offset']:.3f}  [{p['obj1']}] <-> [{p['obj2']}]")
        print("\nTop offenders by conflict count:")
        for name, c in offender_counter.most_common(20):
            print(f"  {c:3d}  {name}")
    return pairs, offender_counter
