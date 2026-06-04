"""Pre-export validation gate. Run IMMEDIATELY before File > Export to Blender.

Refuses to proceed if any critical issue remains. Lists exactly what needs fixing.
"""
import Rhino
import scriptcontext as sc
import rhinoscriptsyntax as rs
from collections import defaultdict

doc = sc.doc

# Reuse the audit logic via simple inline check
breps = [o for o in doc.Objects if not o.IsDeleted and
         isinstance(o.Geometry, (Rhino.Geometry.Brep, Rhino.Geometry.Extrusion))]

# Critical coplanar check
critical_pairs = 0
buckets = defaultdict(list)
for obj in breps:
    g = obj.Geometry
    brep = g.ToBrep() if isinstance(g, Rhino.Geometry.Extrusion) else g
    for face in brep.Faces:
        if not face.IsPlanar(0.001): continue
        ok, plane = face.TryGetPlane()
        if not ok: continue
        n = plane.Normal
        comps = (abs(n.X), abs(n.Y), abs(n.Z))
        ax = comps.index(max(comps))
        if comps[ax] < 0.97: continue
        fbb = face.GetBoundingBox(True)
        if ax == 0:
            offset = (fbb.Min.X+fbb.Max.X)/2; a_min,a_max=fbb.Min.Y,fbb.Max.Y; b_min,b_max=fbb.Min.Z,fbb.Max.Z
        elif ax == 1:
            offset = (fbb.Min.Y+fbb.Max.Y)/2; a_min,a_max=fbb.Min.X,fbb.Max.X; b_min,b_max=fbb.Min.Z,fbb.Max.Z
        else:
            offset = (fbb.Min.Z+fbb.Max.Z)/2; a_min,a_max=fbb.Min.X,fbb.Max.X; b_min,b_max=fbb.Min.Y,fbb.Max.Y
        if (a_max-a_min)*(b_max-b_min) < 0.05: continue
        buckets[(ax, round(offset/0.005))].append(
            (obj.Id, obj.Attributes.Name or "?", a_min, a_max, b_min, b_max))

for faces in buckets.values():
    n = len(faces)
    if n < 2: continue
    for i in range(n):
        for j in range(i+1, n):
            f1, f2 = faces[i], faces[j]
            if f1[0] == f2[0]: continue
            ov = max(0, min(f1[3],f2[3])-max(f1[2],f2[2])) * max(0, min(f1[5],f2[5])-max(f1[4],f2[4]))
            if ov >= 1.0:
                critical_pairs += 1

# Metadata check
no_meta = 0
for obj in breps:
    user_strings = obj.Attributes.GetUserStrings()
    keys = [user_strings.GetKey(i) for i in range(user_strings.Count)]
    if 'material' not in keys: no_meta += 1

print("=" * 60)
print("PRE-EXPORT VALIDATION")
print("=" * 60)
print(f"Critical coplanar pairs (>1.0 m^2): {critical_pairs}")
print(f"Objects without 'material' tag:    {no_meta}")

if critical_pairs > 0 or no_meta > 0:
    print()
    print(">>> DO NOT EXPORT - fix issues first")
    print(">>> Run audit_active_document.py for detailed report")
    rs.MessageBox(f"NOT READY FOR EXPORT:\n\n"
                  f"  Critical coplanar pairs: {critical_pairs}\n"
                  f"  Untagged objects: {no_meta}\n\n"
                  f"Run audit_active_document.py for details.",
                  0 | 48)  # OK + warning icon
else:
    print()
    print(">>> READY FOR EXPORT")
    rs.MessageBox("Ready for export.\nAll checks passed.", 0 | 64)
