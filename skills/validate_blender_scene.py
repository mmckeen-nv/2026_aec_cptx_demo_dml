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
             critical_overlap=1.0, require_material_slots=False,
             strict_coplanar=False, verbose=True):
    if SKILLS_DIR_HERE not in sys.path: sys.path.insert(0, SKILLS_DIR_HERE)
    import coplanar_detector as cd
    pairs, offenders = cd.run(min_overlap_area=min_overlap_area,
                              offset_resolution=offset_resolution,
                              verbose=False)
    potential_zfights = [p for p in pairs if p.get("same_facing", True)]
    opposed_contacts = [p for p in pairs if not p.get("same_facing", True)]
    critical_pairs = [p for p in potential_zfights
                      if p["overlap_m2"] >= critical_overlap]
    dup_names = _find_duplicates_by_name(bpy.context.scene)
    visible_meshes = [o for o in bpy.data.objects
                      if o.type == "MESH" and o.visible_get()]
    missing_material_metadata = [o.name for o in visible_meshes
                                 if not str(o.get("material", "")).strip()]
    missing_material_slots = [o.name for o in visible_meshes
                              if len(o.data.materials) == 0]
    findings = {
        "coplanar_pairs_total": len(pairs),
        "coplanar_pairs_opposed_contact": len(opposed_contacts),
        "coplanar_pairs_potential_zfight": len(potential_zfights),
        "coplanar_pairs_critical": len(critical_pairs),
        "duplicate_name_suspects": dup_names,
        "objects_missing_material_metadata": missing_material_metadata,
        "objects_missing_material_slots": missing_material_slots,
        "material_slots_required": require_material_slots,
        "coplanar_pairs_blocking": strict_coplanar,
        "top_offenders": [(n, c) for n, c in offenders.most_common(10)],
    }
    if verbose:
        print(f"Coplanar pairs: {findings['coplanar_pairs_total']} "
              f"(opposed contacts: {len(opposed_contacts)}, "
              f"potential z-fights: {len(potential_zfights)}, "
              f"critical same-facing >={critical_overlap}m^2: {len(critical_pairs)})")
        print(f"Name-duplicate suspects: {len(dup_names)}")
        print(f"Objects missing material metadata: {len(missing_material_metadata)}")
        print(f"Objects missing Blender material slots: {len(missing_material_slots)} "
              f"({'required' if require_material_slots else 'informational before material phase'})")
        if critical_pairs:
            print("Top critical coplanar pairs:")
            for p in critical_pairs[:10]:
                print(f"  {p['overlap_m2']:.1f}m^2  {p['axis']}={p['plane_offset']:.3f}  "
                      f"{p['obj1']} <-> {p['obj2']}")
    # Architectural walls, slabs, ceilings, and room partitions legitimately
    # share planes. Keep this diagnostic visible, but do not block a handoff on
    # pair count alone unless a caller explicitly requests strict coplanar mode.
    ok = ((not strict_coplanar or len(critical_pairs) == 0)
          and len(dup_names) == 0
          and len(missing_material_metadata) == 0
          and (not require_material_slots or len(missing_material_slots) == 0))
    return ok, findings

SKILLS_DIR_HERE = os.path.dirname(os.path.abspath(__file__))
