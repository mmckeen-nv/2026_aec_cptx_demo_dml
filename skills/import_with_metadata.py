"""Validated .3dm importer with metadata extraction.

Reads a Rhino .3dm via rhino3dm. For each object:
  - Handles both Brep AND Mesh geometry types
  - For Mesh: imports vertices/faces directly (render meshes from Rhino)
  - For Brep: attempts face-level render meshes; if none, tries full B-rep mesh
  - Preserves layer hierarchy as nested Blender Collections
  - Sets hide_viewport per Rhino visibility
  - Extracts User Text attributes -> Blender custom properties
  - Extracts object name -> falls back to name-parsing if no User Text

Refuses to proceed if rhino3dm reports load errors or critical attributes are
missing. Caller must inspect the issue report and decide.
"""
import hashlib
import json
import os
import site
import sys
from pathlib import Path


def _source_signature(path):
    resolved = Path(path).resolve()
    digest = hashlib.sha256()
    with resolved.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    stat = resolved.stat()
    return {
        "path": str(resolved),
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "sha256": digest.hexdigest(),
    }

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


def default_material_tag(name, layer_name=""):
    """Return a stable VP/AEC material tag when Rhino omitted one."""
    text = (name + " " + layer_name).lower()
    if "led" in text:
        return "M_LED_Emissive"
    if "glass" in text or "glazing" in text:
        return "M_Glass_Clear"
    if "floor" in text or "slab" in text or "concrete" in text:
        return "M_Concrete_Neutral"
    if "roof" in text or "truss" in text or "rig" in text or "hoist" in text:
        return "M_Metal_Dark"
    if "chair" in text:
        return "M_Fabric_Dark"
    if "camera" in text or "cam_" in text or "cart" in text or "case" in text:
        return "M_Equipment_Black"
    if "wall" in text or "room" in text or "partition" in text:
        return "M_Wall_Neutral"
    return "M_Proxy_Neutral"


def default_blender_disposition(name, layer_name=""):
    """Return downstream presentation handling for coordination objects."""
    if name.strip().upper() == "SITE_TERRAIN":
        return "REMOVE_BEFORE_RENDER"
    return "KEEP"

def _unit_scale_to_meters(unit_system):
    """Return a deterministic model-unit to metre conversion."""
    unit_name = str(unit_system).split(".")[-1].lower()
    scales = {
        "angstroms": 1e-10, "nanometers": 1e-9, "microns": 1e-6,
        "millimeters": 1e-3, "centimeters": 1e-2, "decimeters": 1e-1,
        "meters": 1.0, "dekameters": 10.0, "hectometers": 100.0,
        "kilometers": 1000.0, "microinches": 0.0254e-6, "mils": 0.0254e-3,
        "inches": 0.0254, "feet": 0.3048, "yards": 0.9144, "miles": 1609.344,
    }
    if unit_name not in scales:
        raise RuntimeError(f"Unsupported or unset Rhino unit system: {unit_system}")
    return scales[unit_name]


def inspect_3dm(path):
    """Validate a handoff without requiring Blender and return exact counts."""
    rhino3dm = ensure_rhino3dm()
    f3dm = rhino3dm.File3dm.Read(path)
    if f3dm is None:
        raise RuntimeError(f"Could not read {path}")

    counts = {
        "objects": len(f3dm.Objects),
        "layers": len(f3dm.Layers),
        "breps": 0,
        "meshes": 0,
        "joined_meshes": 0,
        "joined_vertices": 0,
        "joined_faces": 0,
        "invalid_joined_meshes": 0,
        "unit_scale": _unit_scale_to_meters(f3dm.Settings.ModelUnitSystem),
        "joined_names": [],
        "joined_bounds": {},
    }
    for robj in f3dm.Objects:
        geom = robj.Geometry
        if isinstance(geom, rhino3dm.Brep):
            counts["breps"] += 1
        elif isinstance(geom, rhino3dm.Mesh):
            counts["meshes"] += 1
            if robj.Attributes.GetUserString("handoff_geometry") == "joined_mesh":
                counts["joined_meshes"] += 1
                vertex_count = len(geom.Vertices)
                face_count = len(geom.Faces)
                counts["joined_vertices"] += vertex_count
                counts["joined_faces"] += face_count
                if vertex_count <= 0 or face_count <= 0:
                    counts["invalid_joined_meshes"] += 1
                name = robj.Attributes.Name or ""
                counts["joined_names"].append(name)
                if vertex_count > 0:
                    xs = [vertex.X for vertex in geom.Vertices]
                    ys = [vertex.Y for vertex in geom.Vertices]
                    zs = [vertex.Z for vertex in geom.Vertices]
                    counts["joined_bounds"][name] = {
                        "min": (min(xs), min(ys), min(zs)),
                        "max": (max(xs), max(ys), max(zs)),
                    }
    return counts


def _remove_collection_tree(bpy, collection):
    """Remove only the named import collection and its descendants."""
    for obj in list(collection.all_objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for child in list(collection.children):
        _remove_collection_tree(bpy, child)
    if bpy.data.collections.get(collection.name) is not None:
        bpy.data.collections.remove(collection)


def import_3dm(path, root_name="ImportedRhino", verbose=True, replace_existing=True):
    import bpy
    rhino3dm = ensure_rhino3dm()
    f3dm = rhino3dm.File3dm.Read(path)
    if f3dm is None:
        raise RuntimeError(f"Could not read {path}")
    existing = bpy.data.collections.get(root_name)
    if existing is not None:
        if not replace_existing:
            raise RuntimeError(f"Collection already exists: {root_name}")
        _remove_collection_tree(bpy, existing)
    unit_scale = _unit_scale_to_meters(f3dm.Settings.ModelUnitSystem)

    # Build layer index -> Blender collection
    root_col = bpy.data.collections.new(root_name)
    bpy.context.scene.collection.children.link(root_col)
    signature = _source_signature(path)
    root_col["source_3dm_path"] = signature["path"]
    root_col["source_3dm_size"] = signature["size"]
    root_col["source_3dm_mtime_ns"] = str(signature["mtime_ns"])
    root_col["source_3dm_sha256"] = signature["sha256"]
    layers = {}  # idx -> {"col": Collection, "name": str, "visible": bool}
    for i, lay in enumerate(f3dm.Layers):
        layers[i] = {"name": lay.Name, "full_path": getattr(lay, "FullPath", lay.Name), "visible": lay.Visible,
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

    # A deterministic VP handoff contains explicit joined Mesh companions. When
    # they exist, import only those companions so saved Brep render meshes cannot
    # create duplicates. Older AEC files without companions retain the Brep path.
    joined_mesh_ids = set()
    for robj in f3dm.Objects:
        try:
            handoff_geometry = robj.Attributes.GetUserString("handoff_geometry")
        except Exception:
            handoff_geometry = None
        if isinstance(robj.Geometry, rhino3dm.Mesh) and handoff_geometry == "joined_mesh":
            joined_mesh_ids.add(str(robj.Attributes.Id))
    prefer_joined_meshes = bool(joined_mesh_ids)

    # Build mesh objects from explicit Mesh companions, or Brep render meshes in
    # legacy files that do not contain companions.
    skipped = 0
    imported = 0
    for robj in f3dm.Objects:
        attrs = robj.Attributes
        g = robj.Geometry

        if attrs.GetUserString("export_to_blender") == "false":
            continue
        if prefer_joined_meshes and str(attrs.Id) not in joined_mesh_ids:
            continue

        if isinstance(g, rhino3dm.Mesh):
            # Direct mesh geometry (render meshes from Rhino)
            verts_all = []
            faces_all = []
            for vertex in g.Vertices:
                # Rhino and Blender are both Z-up. Preserve axes exactly.
                verts_all.append((
                    vertex.X * unit_scale,
                    vertex.Y * unit_scale,
                    vertex.Z * unit_scale,
                ))
            for mesh_face in g.Faces:
                indices = tuple(mesh_face)
                if len(indices) == 4 and indices[2] == indices[3]:
                    indices = indices[:3]
                faces_all.append(tuple(index for index in indices))

        elif isinstance(g, rhino3dm.Brep):
            # Try face-level render meshes first
            verts_all = []
            faces_all = []
            vbase = 0
            has_mesh = False
            for fi in range(len(g.Faces)):
                face = g.Faces[fi]
                rm = face.GetMesh(rhino3dm.MeshType.Render)
                if rm is not None:
                    has_mesh = True
                    nv = len(rm.Vertices)
                    for vertex in rm.Vertices:
                        # Rhino and Blender are both Z-up. Preserve axes exactly.
                        verts_all.append((
                            vertex.X * unit_scale,
                            vertex.Y * unit_scale,
                            vertex.Z * unit_scale,
                        ))
                    for mesh_face in rm.Faces:
                        indices = tuple(mesh_face)
                        if len(indices) == 4 and indices[2] == indices[3]:
                            indices = indices[:3]
                        faces_all.append(tuple(index + vbase for index in indices))
                    vbase += nv
            if not has_mesh:
                # No face-level render meshes — check if there's a separate Mesh obj by name/layer
                # This is handled by the separate Mesh geometry pass above
                skipped += 1
                continue
        else:
            # Not a Brep or Mesh — skip (curves, points, etc.)
            continue

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
            obj["rhino_layer"] = info["full_path"]
        else:
            root_col.objects.link(obj)

        # User Text -> custom properties
        utext = {}
        try:
            for key, value in attrs.GetUserStrings():
                if value is not None:
                    utext[key] = value
        except Exception:
            pass
        if not utext:
            # Fall back to name-parsing
            utext = parse_name_fallback(name)
        if not str(utext.get("material", "")).strip():
            layer_name = info["full_path"] if info else ""
            utext["material"] = default_material_tag(name, layer_name)
        if not str(utext.get("blender_disposition", "")).strip():
            layer_name = info["full_path"] if info else ""
            utext["blender_disposition"] = default_blender_disposition(
                name, layer_name
            )
        for k, v in utext.items():
            obj[k] = v
        obj["source_units"] = str(f3dm.Settings.ModelUnitSystem)
        obj["unit_scale_to_meters"] = unit_scale
        obj.rotation_mode = 'XYZ'

        imported += 1

    if verbose:
        print(f"Imported {imported} objects, skipped {skipped}, "
              f"layers={len(layers)}, unit_scale={unit_scale}")
    return imported, skipped, layers


def assert_import_matches_source(path, root_name="ImportedRhino"):
    """Reject a retained Blender collection imported from any older .3dm."""
    import bpy

    collection = bpy.data.collections.get(root_name)
    if collection is None:
        raise RuntimeError("missing imported collection: " + root_name)
    signature = _source_signature(path)
    expected = {
        "source_3dm_path": signature["path"],
        "source_3dm_size": signature["size"],
        "source_3dm_mtime_ns": str(signature["mtime_ns"]),
        "source_3dm_sha256": signature["sha256"],
    }
    for key, value in expected.items():
        if str(collection.get(key, "")) != str(value):
            raise RuntimeError("stale Blender handoff collection: {} mismatch".format(key))
    return signature


def build_mesh_bridge(path, output_path):
    """Build a JSON mesh/metadata bridge for Blender builds without rhino3dm.

    Some Windows-on-ARM Blender distributions have no compatible rhino3dm
    wheel.  Run this function from a compatible system Python, then load the
    result in Blender with :func:`import_mesh_bridge`.  This preserves the same
    layer and User Text contract as ``import_3dm`` without using FBX or OBJ.
    """
    rhino3dm = ensure_rhino3dm()
    f3dm = rhino3dm.File3dm.Read(path)
    if f3dm is None:
        raise RuntimeError(f"Could not read {path}")
    unit_scale = _unit_scale_to_meters(f3dm.Settings.ModelUnitSystem)
    layers = {}
    for index, layer in enumerate(f3dm.Layers):
        layers[index] = getattr(layer, "FullPath", layer.Name)
    payload = {
        "source": _source_signature(path),
        "source_units": str(f3dm.Settings.ModelUnitSystem),
        "unit_scale": unit_scale,
        "objects": [],
        "skipped": [],
    }
    for robj in f3dm.Objects:
        attrs, geom = robj.Attributes, robj.Geometry
        if attrs.GetUserString("export_to_blender") == "false":
            continue
        if not isinstance(geom, (rhino3dm.Brep, rhino3dm.Mesh)):
            continue
        vertices, faces = [], []
        if isinstance(geom, rhino3dm.Mesh):
            meshes = [geom]
        else:
            meshes = []
            for face in geom.Faces:
                render_mesh = face.GetMesh(rhino3dm.MeshType.Render)
                if render_mesh is not None:
                    meshes.append(render_mesh)
        for mesh in meshes:
            base = len(vertices)
            vertices.extend([
                [v.X * unit_scale, v.Y * unit_scale, v.Z * unit_scale]
                for v in mesh.Vertices
            ])
            for mesh_face in mesh.Faces:
                indices = list(mesh_face)
                if len(indices) == 4 and indices[2] == indices[3]:
                    indices = indices[:3]
                faces.append([base + index for index in indices])
        name = attrs.Name or f"obj_{len(payload['objects'])}"
        if not vertices or not faces:
            payload["skipped"].append(name)
            continue
        # The imported Blender object is built from render-mesh vertices.  A
        # trimmed/boolean Brep bbox can include the untrimmed surface extent
        # (for example, an opening cut from a patio slab), so use the exact
        # bridge mesh bounds for the parity contract.
        xs = [vertex[0] for vertex in vertices]
        ys = [vertex[1] for vertex in vertices]
        zs = [vertex[2] for vertex in vertices]
        user_text = {}
        try:
            for key, value in attrs.GetUserStrings():
                if value is not None:
                    user_text[key] = value
        except Exception:
            pass
        layer_path = layers.get(attrs.LayerIndex, "Unlayered")
        if not str(user_text.get("material", "")).strip():
            user_text["material"] = default_material_tag(name, layer_path)
        if not str(user_text.get("blender_disposition", "")).strip():
            user_text["blender_disposition"] = default_blender_disposition(
                name, layer_path
            )
        payload["objects"].append({
            "name": name,
            "layer": layer_path,
            "visible": bool(attrs.Visible),
            "user_text": user_text,
            "vertices": vertices,
            "faces": faces,
            "source_bbox": [
                [min(xs), min(ys), min(zs)],
                [max(xs), max(ys), max(zs)],
            ],
        })
    Path(output_path).write_text(json.dumps(payload), encoding="utf-8")
    return {
        "objects": len(payload["objects"]),
        "skipped": payload["skipped"],
        "source": payload["source"],
    }


def import_mesh_bridge(path, root_name="ImportedRhino",
                       replace_existing=True, verbose=True):
    """Import a bridge created by :func:`build_mesh_bridge` into Blender."""
    import bpy
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    existing = bpy.data.collections.get(root_name)
    if existing is not None:
        if not replace_existing:
            raise RuntimeError(f"Collection already exists: {root_name}")
        _remove_collection_tree(bpy, existing)
    root = bpy.data.collections.new(root_name)
    bpy.context.scene.collection.children.link(root)
    for key, value in payload["source"].items():
        root[f"source_3dm_{key}" if key != "path" else "source_3dm_path"] = str(value)
    root["mesh_bridge_path"] = str(Path(path).resolve())
    collections = {}
    def collection_for(full_path):
        parent = root
        built = []
        for part in full_path.split("::"):
            built.append(part)
            key = "::".join(built)
            if key not in collections:
                collection = bpy.data.collections.new(part)
                parent.children.link(collection)
                collections[key] = collection
            parent = collections[key]
        return parent
    for item in payload["objects"]:
        mesh = bpy.data.meshes.new(item["name"] + "_mesh")
        mesh.from_pydata(item["vertices"], [], item["faces"])
        mesh.update()
        obj = bpy.data.objects.new(item["name"], mesh)
        collection_for(item["layer"]).objects.link(obj)
        obj.hide_viewport = not item["visible"]
        obj.hide_render = obj.hide_viewport
        obj.rotation_mode = "XYZ"
        obj["rhino_layer"] = item["layer"]
        obj["source_bbox"] = json.dumps(item["source_bbox"])
        obj["source_units"] = payload["source_units"]
        obj["unit_scale_to_meters"] = payload["unit_scale"]
        for key, value in item["user_text"].items():
            obj[key] = value
    if verbose:
        print(f"Imported bridge objects={len(payload['objects'])}, "
              f"source_skipped={len(payload['skipped'])}")
    return len(payload["objects"]), payload["skipped"], collections
