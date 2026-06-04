"""
scatter_landscape_plants.py
Run inside Rhino via: Tools > RunPythonScript

What it does:
  1. Audits the document — lists all layers and closed curves
  2. Finds landscape plan boundary curves (on layers containing
     "landscape", "planting", "zone", "plan", "site" in name,
     OR all closed planar curves if no matching layers found)
  3. Finds the terrain surface (layer containing "terrain" or "site")
  4. Projects each boundary curve onto the terrain
  5. Fills the projected boundary with scattered Point objects
  6. Names each point by plant species appropriate to the zone

Plant palette — coastal California desert:
  Ground cover:  Echeveria elegans, Aeonium arboreum, Dudleya pulverulenta, Aloe vera
  Shrubs:        Salvia leucophylla, Ceanothus thyrsiflorus, Artemisia californica
  Grasses:       Festuca ovina glauca, Muhlenbergia rigens
  Specimens:     Agave americana, Yucca whipplei, Opuntia ficus-indica
  Cliff edge:    Dudleya farinosa, Eriogonum fasciculatum
"""

import rhinoscriptsyntax as rs
import Rhino
import Rhino.Geometry as rg
import random
import math
import scriptcontext as sc

# ── Plant palettes keyed by zone keyword ────────────────────────────────
# Each entry: (species_name, relative_weight)
# Density = points per square meter

ZONES = {
    "patio":    { "density": 0.3,  "plants": [
        ("Agave americana",     0.30),
        ("Aloe vera",           0.30),
        ("Echeveria elegans",   0.40),
    ]},
    "ground":   { "density": 2.0,  "plants": [
        ("Echeveria elegans",   0.35),
        ("Aeonium arboreum",    0.25),
        ("Dudleya pulverulenta",0.20),
        ("Aloe vera",           0.20),
    ]},
    "shrub":    { "density": 0.5,  "plants": [
        ("Salvia leucophylla",  0.35),
        ("Ceanothus thyrsiflorus", 0.30),
        ("Artemisia californica",  0.20),
        ("Rosmarinus officinalis", 0.15),
    ]},
    "cliff":    { "density": 0.8,  "plants": [
        ("Dudleya farinosa",       0.40),
        ("Eriogonum fasciculatum", 0.35),
        ("Artemisia californica",  0.25),
    ]},
    "grass":    { "density": 3.0,  "plants": [
        ("Festuca ovina glauca",   0.50),
        ("Muhlenbergia rigens",    0.35),
        ("Nassella tenuissima",    0.15),
    ]},
    "specimen": { "density": 0.1,  "plants": [
        ("Agave americana",        0.40),
        ("Yucca whipplei",         0.35),
        ("Opuntia ficus-indica",   0.25),
    ]},
    "default":  { "density": 1.0,  "plants": [
        ("Salvia leucophylla",     0.20),
        ("Echeveria elegans",      0.20),
        ("Aeonium arboreum",       0.15),
        ("Dudleya pulverulenta",   0.15),
        ("Festuca ovina glauca",   0.15),
        ("Agave americana",        0.10),
        ("Artemisia californica",  0.05),
    ]},
}

def pick_plant(zone_key):
    """Weighted random plant pick from zone palette."""
    zone = ZONES.get(zone_key, ZONES["default"])
    plants, weights = zip(*zone["plants"])
    total = sum(weights)
    r = random.uniform(0, total)
    acc = 0
    for plant, w in zip(plants, weights):
        acc += w
        if r <= acc:
            return plant
    return plants[-1]

def zone_from_layer(layer_name):
    """Infer zone type from layer name."""
    n = layer_name.lower()
    for key in ZONES:
        if key in n:
            return key
    # Fuzzy matches
    if any(x in n for x in ["succulent", "cactus", "aloe", "agave"]):
        return "ground"
    if any(x in n for x in ["shrub", "sage", "salvia"]):
        return "shrub"
    if any(x in n for x in ["grass", "meadow"]):
        return "grass"
    if any(x in n for x in ["specimen", "tree", "accent"]):
        return "specimen"
    return "default"

def curve_area_approx(crv_id):
    """Approximate planar area via bounding box (fallback)."""
    bb = rs.BoundingBox(crv_id)
    if not bb:
        return 1.0
    dx = abs(bb[6].X - bb[0].X)
    dy = abs(bb[6].Y - bb[0].Y)
    return dx * dy * 0.7   # ~70% fill for irregular shapes

def point_in_curve(pt, crv_id):
    """Test if a 2D point (projected flat) is inside a closed curve."""
    crv = rs.coercecurve(crv_id)
    if not crv:
        return False
    test_pt = rg.Point3d(pt.X, pt.Y, crv.PointAtStart.Z)
    result = crv.Contains(test_pt, rg.Plane.WorldXY, sc.doc.ModelAbsoluteTolerance)
    return result == rg.PointContainment.Inside

def scatter_points_in_curve(crv_id, terrain_srf_id, zone_key, max_attempts=5000):
    """Generate scattered points inside crv, projected to terrain."""
    zone     = ZONES.get(zone_key, ZONES["default"])
    density  = zone["density"]

    bb = rs.BoundingBox(crv_id)
    if not bb:
        return []

    xmin, xmax = bb[0].X, bb[6].X
    ymin, ymax = bb[0].Y, bb[6].Y
    area_approx = (xmax - xmin) * (ymax - ymin) * 0.65
    n_points    = max(1, int(area_approx * density))

    print(f"    Zone '{zone_key}': targeting {n_points} plants in ~{area_approx:.1f} m²")

    points   = []
    attempts = 0
    while len(points) < n_points and attempts < max_attempts:
        attempts += 1
        x = random.uniform(xmin, xmax)
        y = random.uniform(ymin, ymax)

        test_pt = rg.Point3d(x, y, 0)
        if not point_in_curve(test_pt, crv_id):
            continue

        # Project onto terrain if available
        if terrain_srf_id:
            proj = rs.ProjectPointToSurface([rg.Point3d(x, y, 1000)],
                                            terrain_srf_id,
                                            [0, 0, -1])
            z = proj[0].Z if proj else 0.0
        else:
            z = rs.CurveStartPoint(crv_id).Z

        points.append(rg.Point3d(x, y, z))

    return points

def main():
    rs.EnableRedraw(False)
    random.seed(42)   # reproducible scatter; change seed for variation

    print("\n══════════════════════════════════════════")
    print("  Landscape Plant Scatter — aec_demo_master")
    print("══════════════════════════════════════════")

    # ── 1. Audit layers ──────────────────────────────────────────────
    all_layers = rs.LayerNames()
    print(f"\nAll layers ({len(all_layers)}):")
    for l in sorted(all_layers):
        print(f"  {l}")

    # ── 2. Find landscape layers ─────────────────────────────────────
    LANDSCAPE_KEYWORDS = ["landscape", "planting", "plant", "zone",
                          "site_plan", "site plan", "garden", "shrub",
                          "ground", "grass", "specimen", "patio", "cliff"]
    TERRAIN_KEYWORDS   = ["terrain", "topo", "site", "ground", "surface", "mesh"]
    SKIP_KEYWORDS      = ["wall", "window", "glass", "roof", "slab", "floor",
                           "ceiling", "door", "column", "curtain", "hidden"]

    landscape_layers = []
    terrain_layer    = None

    for layer in (all_layers or []):
        ln = layer.lower()
        if any(k in ln for k in TERRAIN_KEYWORDS) and "plan" not in ln:
            terrain_layer = layer
        if any(k in ln for k in LANDSCAPE_KEYWORDS):
            if not any(k in ln for k in SKIP_KEYWORDS):
                landscape_layers.append(layer)

    print(f"\nTerrain layer:     {terrain_layer or '(not found)'}")
    print(f"Landscape layers:  {landscape_layers or '(none matched)'}")

    # ── 3. Find closed curves ────────────────────────────────────────
    boundary_curves = []   # list of (curve_id, zone_key)

    if landscape_layers:
        for layer in landscape_layers:
            objs = rs.ObjectsByLayer(layer)
            if not objs:
                continue
            for obj in objs:
                if rs.IsCurve(obj) and rs.IsCurveClosed(obj):
                    zone = zone_from_layer(layer)
                    boundary_curves.append((obj, zone))
                    print(f"  Found closed curve on '{layer}' → zone '{zone}'")
    else:
        print("\nNo landscape layers matched — scanning ALL closed curves...")
        all_objects = rs.AllObjects()
        if all_objects:
            for obj in all_objects:
                if rs.IsCurve(obj) and rs.IsCurveClosed(obj) and rs.IsCurvePlanar(obj):
                    layer = rs.ObjectLayer(obj)
                    if not any(k in layer.lower() for k in SKIP_KEYWORDS):
                        zone = zone_from_layer(layer)
                        boundary_curves.append((obj, zone))
                        print(f"  Found curve on '{layer}' → zone '{zone}'")

    print(f"\nTotal boundary curves found: {len(boundary_curves)}")

    if not boundary_curves:
        rs.EnableRedraw(True)
        rs.MessageBox("No landscape boundary curves found.\n\n"
                      "Create closed curves on layers with names containing:\n"
                      "landscape, planting, zone, patio, shrub, grass, specimen, cliff\n\n"
                      "Then re-run this script.", 0, "Scatter Plants")
        return

    # ── 4. Find terrain surface ──────────────────────────────────────
    terrain_srf_id = None
    if terrain_layer:
        terrain_objs = rs.ObjectsByLayer(terrain_layer)
        if terrain_objs:
            for obj in terrain_objs:
                if rs.IsSurface(obj) or rs.IsPolysurface(obj) or rs.IsMesh(obj):
                    terrain_srf_id = obj
                    print(f"Terrain surface found on layer '{terrain_layer}'")
                    break
    if not terrain_srf_id:
        print("No terrain surface found — points placed at curve Z elevation")

    # ── 5. Create output layer ───────────────────────────────────────
    output_layer = "PLANTING_POINTS"
    if not rs.IsLayer(output_layer):
        rs.AddLayer(output_layer, rs.CreateColor(0, 180, 80))
    rs.CurrentLayer(output_layer)

    # ── 6. Scatter points and name them ─────────────────────────────
    total_placed = 0
    species_count = {}

    for crv_id, zone_key in boundary_curves:
        crv_name = rs.ObjectName(crv_id) or "(unnamed)"
        layer    = rs.ObjectLayer(crv_id)
        print(f"\nProcessing: '{crv_name}' on '{layer}' — zone: {zone_key}")

        pts = scatter_points_in_curve(crv_id, terrain_srf_id, zone_key)

        for pt in pts:
            species  = pick_plant(zone_key)
            pt_id    = rs.AddPoint(pt)
            rs.ObjectName(pt_id, species)
            rs.ObjectLayer(pt_id, output_layer)
            species_count[species] = species_count.get(species, 0) + 1
            total_placed += 1

    # ── 7. Report ────────────────────────────────────────────────────
    rs.EnableRedraw(True)

    print("\n══════════════════════════════════════════")
    print(f"  Done — {total_placed} plants placed")
    print("══════════════════════════════════════════")
    print("\nSpecies breakdown:")
    for species, count in sorted(species_count.items(), key=lambda x: -x[1]):
        print(f"  {count:4d}  {species}")
    print(f"\nAll points on layer: {output_layer}")
    print("Each point's Name property = species.\n")

    summary = "\n".join([f"{v:4d}  {k}" for k, v in
                         sorted(species_count.items(), key=lambda x: -x[1])])
    rs.MessageBox(
        f"{total_placed} plants placed on layer '{output_layer}'.\n\n"
        f"Species count:\n{summary}\n\n"
        f"Each point is named by species.\n"
        f"Edit ZONES dict in script to adjust palette / density.",
        0, "Scatter Plants — Done"
    )

main()
