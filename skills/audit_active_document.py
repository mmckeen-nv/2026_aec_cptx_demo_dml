"""Audit the ACTIVE Rhino document for the construction-discipline issues.

Run any time during modeling: Tools > PythonScript > Run, or bind to an alias.

Checks:
  1. Coplanar faces between different objects (>0.10 m^2 overlap)
  2. Exact duplicate objects (same bbox, same vertex/face counts)
  3. Cross-name duplicates (different names, identical geometry)
  4. Objects missing material metadata (User Text 'material' key)
  5. Open polysurfaces (solids that should be closed but aren't)

Output: report printed to command line + offending objects SELECTED in viewport.
You can then zoom-to-selection and fix.
"""
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs
from collections import defaultdict, Counter

doc = sc.doc
FLATNESS_TOL = 0.005
OFFSET_RES = 0.005
MIN_FACE_AREA = 0.05
MIN_OVERLAP_AREA = 0.10

def bbox_sig(brep, prec=200):
    bb = brep.GetBoundingBox(True)
    return (round(bb.Min.X*prec), round(bb.Min.Y*prec), round(bb.Min.Z*prec),
            round(bb.Max.X*prec), round(bb.Max.Y*prec), round(bb.Max.Z*prec))

def collect_brep_objects():
    out = []
    for obj in doc.Objects:
        if obj.IsDeleted: continue
        g = obj.Geometry
        if isinstance(g, Rhino.Geometry.Brep):
            out.append(obj)
        elif isinstance(g, Rhino.Geometry.Extrusion):
            out.append(obj)
    return out

print("=" * 60)
print("Active document audit")
print("=" * 60)
breps = collect_brep_objects()
print(f"Brep/Extrusion objects: {len(breps)}")

# --- Coplanar faces between different objects ---
buckets = defaultdict(list)
for obj in breps:
    g = obj.Geometry
    brep = g.ToBrep() if isinstance(g, Rhino.Geometry.Extrusion) else g
    for face in brep.Faces:
        if not face.IsPlanar(0.001): continue
        # Get face plane
        ok, plane = face.TryGetPlane()
        if not ok: continue
        n = plane.Normal
        # Determine dominant axis
        comps = (abs(n.X), abs(n.Y), abs(n.Z))
        ax = comps.index(max(comps))
        if comps[ax] < 0.97: continue
        # Get bounding box of face in world coords
        fbb = face.GetBoundingBox(True)
        if ax == 0:
            offset = (fbb.Min.X + fbb.Max.X) / 2
            a_min, a_max = fbb.Min.Y, fbb.Max.Y
            b_min, b_max = fbb.Min.Z, fbb.Max.Z
        elif ax == 1:
            offset = (fbb.Min.Y + fbb.Max.Y) / 2
            a_min, a_max = fbb.Min.X, fbb.Max.X
            b_min, b_max = fbb.Min.Z, fbb.Max.Z
        else:
            offset = (fbb.Min.Z + fbb.Max.Z) / 2
            a_min, a_max = fbb.Min.X, fbb.Max.X
            b_min, b_max = fbb.Min.Y, fbb.Max.Y
        area = (a_max - a_min) * (b_max - b_min)
        if area < MIN_FACE_AREA: continue
        key = (ax, round(offset / OFFSET_RES))
        buckets[key].append((obj.Id, obj.Attributes.Name or "(unnamed)",
                             offset, a_min, a_max, b_min, b_max, area))

pairs = []
for (ax, _), faces in buckets.items():
    n = len(faces)
    if n < 2: continue
    for i in range(n):
        for j in range(i+1, n):
            f1, f2 = faces[i], faces[j]
            if f1[0] == f2[0]: continue
            a_ov = max(0, min(f1[4], f2[4]) - max(f1[3], f2[3]))
            b_ov = max(0, min(f1[6], f2[6]) - max(f1[5], f2[5]))
            ov = a_ov * b_ov
            if ov < MIN_OVERLAP_AREA: continue
            pairs.append((ov, ["X","Y","Z"][ax], (f1[2]+f2[2])/2,
                          f1[0], f1[1], f2[0], f2[1]))
pairs.sort(key=lambda p: -p[0])

# --- Duplicates ---
dup_buckets = defaultdict(list)
for obj in breps:
    g = obj.Geometry
    brep = g.ToBrep() if isinstance(g, Rhino.Geometry.Extrusion) else g
    sig = bbox_sig(brep) + (brep.Vertices.Count, brep.Faces.Count)
    dup_buckets[sig].append(obj)
exact_dups = [(sig, group) for sig, group in dup_buckets.items() if len(group) >= 2]

# --- Missing metadata ---
missing_meta = []
for obj in breps:
    try:
        keys = list(obj.Attributes.GetUserStrings().Keys)
    except:
        try:
            user_strings = obj.Attributes.GetUserStrings()
            keys = [user_strings.GetKey(i) for i in range(user_strings.Count)]
        except:
            keys = []
    if 'material' not in keys:
        missing_meta.append(obj)

# --- Open Breps (where should be closed) ---
open_breps = []
for obj in breps:
    g = obj.Geometry
    brep = g.ToBrep() if isinstance(g, Rhino.Geometry.Extrusion) else g
    if not brep.IsSolid:
        # Tolerate intentionally-open: terrain, patio_wall_internals, glass-pane-faces
        nm = (obj.Attributes.Name or "").lower()
        if any(tok in nm for tok in ("terrain", "pw_", "_top", "_bot", "_inner", "_outer", "facia")):
            continue
        open_breps.append(obj)

# --- Report ---
print(f"\n[1] Coplanar pairs (>{MIN_OVERLAP_AREA:.2f} m^2): {len(pairs)}")
if pairs:
    print("    Top 10:")
    for ov, ax, off, _, n1, _, n2 in pairs[:10]:
        print(f"      {ov:5.1f} m^2  {ax}={off:6.2f}  {n1:28s} <--> {n2}")

print(f"\n[2] Exact duplicate groups: {len(exact_dups)}")
for sig, group in exact_dups[:5]:
    names = [o.Attributes.Name or "?" for o in group]
    print(f"    {len(group)}x  {names}")

print(f"\n[3] Objects missing 'material' User Text: {len(missing_meta)}")
if missing_meta:
    sample = [o.Attributes.Name or "?" for o in missing_meta[:8]]
    print(f"    e.g. {sample}")

print(f"\n[4] Open Breps (likely should be solid): {len(open_breps)}")
if open_breps:
    sample = [o.Attributes.Name or "?" for o in open_breps[:8]]
    print(f"    e.g. {sample}")

# --- Highlight offenders in viewport ---
rs.UnselectAllObjects()
critical_ids = set()
for ov, ax, off, id1, _, id2, _ in pairs:
    if ov >= 1.0:  # critical
        critical_ids.add(id1)
        critical_ids.add(id2)
for sig, group in exact_dups:
    for obj in group[1:]:  # all but one
        critical_ids.add(obj.Id)
if critical_ids:
    rs.SelectObjects(list(critical_ids))
    print(f"\nSelected {len(critical_ids)} offender objects in viewport for review.")
    print("Zoom-to-selection to inspect. _SelNone to deselect.")

# --- Verdict ---
critical_count = sum(1 for p in pairs if p[0] >= 1.0)
print("\n" + "=" * 60)
if critical_count == 0 and not exact_dups and not missing_meta:
    print(">>> PASS - document is in clean state for export")
else:
    print(f">>> FAIL - {critical_count} critical coplanar, "
          f"{len(exact_dups)} duplicate groups, "
          f"{len(missing_meta)} missing metadata")
print("=" * 60)
