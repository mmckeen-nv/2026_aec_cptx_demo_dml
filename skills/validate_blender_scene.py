"""Post-import validation gate. Run after every import / geometry edit batch.
Refuses (returns False) if critical issues remain. Returns dict of findings.
"""
import bpy, sys, os
from collections import Counter, defaultdict
from mathutils import Vector

def _find_duplicates_by_name(scene):
    """Names like foo, foo.001, foo.002 are Blender's auto-rename for duplicates."""
    suspects = defaultdict(list)
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.visible_get(): continue
        # Strip .NNN suffix
        base = obj.name.rsplit(".", 1)[0]
        try:
            int(obj.name.rsplit(".", 1)[1])  # only count if numeric suffix
            suspects[base].append(obj.name)
        except (ValueError, IndexError):
            pass
    return {b: lst for b, lst in suspects.items() if lst}

def validate(min_overlap_area=0.10, offset_resolution=0.005,
             critical_overlap=1.0, verbose=True):
    if SKILLS_DIR_HERE not in sys.path: sys.path.insert(0, SKILLS_DIR_HERE)
    import coplanar_detector as cd
    pairs, offenders = cd.run(min_overlap_area=min_overlap_area,
                              offset_resolution=offset_resolution,
                              verbose=False)
    critical_pairs = [p for p in pairs if p["overlap_m2"] >= critical_overlap]
    dup_names = _find_duplicates_by_name(bpy.context.scene)
    no_material = [o.name for o in bpy.data.objects
                   if o.type == "MESH" and o.visible_get()
                   and len(o.data.materials) == 0]
    findings = {
        "coplanar_pairs_total": len(pairs),
        "coplanar_pairs_critical": len(critical_pairs),
        "duplicate_name_suspects": dup_names,
        "objects_without_material": no_material[:20],
        "top_offenders": [(n, c) for n, c in offenders.most_common(10)],
    }
    if verbose:
        print(f"Coplanar pairs: {findings['coplanar_pairs_total']} "
              f"(critical, >{critical_overlap}m^2: {findings['coplanar_pairs_critical']})")
        print(f"Name-duplicate suspects: {len(dup_names)}")
        print(f"Objects without material: {len(no_material)}")
        if critical_pairs:
            print("Top critical coplanar pairs:")
            for p in critical_pairs[:10]:
                print(f"  {p['overlap_m2']:.1f}m^2  {p['axis']}={p['plane_offset']:.3f}  "
                      f"{p['obj1']} <-> {p['obj2']}")
    ok = findings["coplanar_pairs_critical"] == 0 and len(dup_names) == 0
    return ok, findings

SKILLS_DIR_HERE = os.path.dirname(os.path.abspath(__file__))
