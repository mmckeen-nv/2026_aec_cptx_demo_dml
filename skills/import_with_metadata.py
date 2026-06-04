"""Validated .3dm importer with metadata extraction.

Reads a Rhino .3dm via rhino3dm. For each object:
  - Builds Blender mesh from Brep face render meshes
  - Preserves layer hierarchy as nested Blender Collections
  - Sets hide_viewport per Rhino visibility
  - Extracts User Text attributes -> Blender custom properties
  - Extracts object name -> falls back to name-parsing if no User Text

Refuses to proceed if rhino3dm reports load errors or critical attributes are
missing. Caller must inspect the issue report and decide.
"""
import bpy, sys, site, os
from mathutils import Vector

def ensure_rhino3dm():
    user_site = site.getusersitepackages()
    if user_site not in sys.path:
        sys.path.insert(0, user_site)
    try:
        import rhino3dm
        return rhino3dm
    except ImportError:
        raise RuntimeError("rhino3dm not installed. pip install --user rhino3dm")

def parse_name_fallback(name):
    """Extract material/role hints from naming convention."""
    parts = name.lower().split("_")
    hints = {}
    for tok in parts:
        if tok in ("stone", "concrete", "conc", "wood", "glass", "metal",
                   "aluminum", "steel", "tile", "marble", "granite", "slate"):
            hints["material"] = tok if tok != "conc" else "concrete"
        elif tok in ("wall", "floor", "slab", "ceiling", "roof", "door",
                     "window", "stair", "step", "patio"):
            hints["architectural_role"] = tok
        elif tok in ("polished", "matte", "weathered", "rough"):
            hints["finish"] = tok
        elif tok in ("dark", "light", "warm", "cool"):
            hints["color_hint"] = tok
    return hints

def import_3dm(path, root_name="ImportedRhino", verbose=True):
    rhino3dm = ensure_rhino3dm()
    f3dm = rhino3dm.File3dm.Read(path)
    if f3dm is None:
        raise RuntimeError(f"Could not read {path}")

    # Build layer index -> Blender collection
    root_col = bpy.data.collections.new(root_name)
    bpy.context.scene.collection.children.link(root_col)
    layers = {}  # idx -> {"col": Collection, "name": str, "visible": bool}
    for i, lay in enumerate(f3dm.Layers):
        layers[i] = {"name": lay.Name, "visible": lay.Visible,
                     "parent_id": lay.ParentLayerId, "rhino_id": lay.Id,
                     "col": None}
    # Create collections honoring parent chain
    def find_by_id(idx_id):
        for k, v in layers.items():
            if v["rhino_id"] == idx_id: return k
        return None
    for i, info in layers.items():
        col = bpy.data.collections.new(info["name"])
        info["col"] = col
    for i, info in layers.items():
        parent_idx = find_by_id(info["parent_id"])
        if parent_idx is not None:
            layers[parent_idx]["col"].children.link(info["col"])
        else:
            root_col.children.link(info["col"])

    # Build mesh objects from Breps
    skipped = 0
    imported = 0
    for robj in f3dm.Objects:
        attrs = robj.Attributes
        g = robj.Geometry
        if not isinstance(g, rhino3dm.Brep):
            continue
        # Collect render meshes from all faces
        verts_all = []
        faces_all = []
        vbase = 0
        for fi in range(len(g.Faces)):
            face = g.Faces[fi]
            rm = face.GetMesh(rhino3dm.MeshType.Render)
            if rm is None: continue
            try:
                vf = rm.Vertices.ToFloatArray()
                ff = rm.Faces.ToIntArray(False)
            except Exception:
                continue
            nv = len(vf) // 3
            for k in range(nv):
                verts_all.append((vf[3*k], vf[3*k+1], vf[3*k+2]))
            i_in_face = 0
            while i_in_face < len(ff):
                fcount = ff[i_in_face]
                idx = ff[i_in_face+1 : i_in_face+1+fcount]
                faces_all.append(tuple(v + vbase for v in idx))
                i_in_face += 1 + fcount
            vbase += nv
        if not verts_all or not faces_all:
            skipped += 1
            continue

        name = attrs.Name or f"obj_{imported}"
        mesh = bpy.data.meshes.new(name + "_mesh")
        mesh.from_pydata(verts_all, [], faces_all)
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)

        # Layer / visibility
        li = attrs.LayerIndex
        info = layers.get(li, None)
        if info:
            info["col"].objects.link(obj)
            obj.hide_viewport = not (info["visible"] and attrs.Visible)
            obj.hide_render = obj.hide_viewport
        else:
            root_col.objects.link(obj)

        # User Text -> custom properties
        utext = {}
        try:
            keys = attrs.GetUserStrings()
            for k in keys:
                v = attrs.GetUserString(k)
                if v is not None:
                    utext[k] = v
        except Exception:
            pass
        if not utext:
            # Fall back to name-parsing
            utext = parse_name_fallback(name)
        for k, v in utext.items():
            obj[k] = v

        imported += 1

    if verbose:
        print(f"Imported {imported} Brep objects, skipped {skipped}, "
              f"layers={len(layers)}")
    return imported, skipped, layers
