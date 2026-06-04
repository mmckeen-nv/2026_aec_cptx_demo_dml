# Rhino Architectural Modeling — Pre-Export Discipline

A modeling-time checklist for clean NURBS-to-mesh handoff (Rhino → Blender or any
depth-buffer renderer). The core principle: **every coplanar face pair in the source
becomes a z-fight in the render**. Catch them at the source.

---

## Anti-patterns that create z-fighting

### 1. Coincident outer faces at wall corners
North wall outer at Y=10, east wall also extends to Y=10 → coplanar at the NE corner.
**Fix:** Pick one wall as "continuous" and trim the other to butt into its *inner* face.
NE corner becomes a single outer surface (the north wall's), not two coplanar ones.

### 2. Painted-on finishes
Stone facing modeled as a 0-thickness surface flat against the concrete.
**Fix:** `_OffsetSrf` the finish to give it real thickness (5–25 mm). Stone outer at
Y=10.025, concrete outer at Y=10. No coplanar.

### 3. Boolean Union artifacts
`_BooleanUnion` of two Breps sharing an edge creates duplicate faces along the seam.
**Fix:** Run `_SelDup` immediately after every Boolean. Delete the duplicates.

### 4. Slab edges flush with wall outer face
Floor slab edge at X=17, wall outer at X=17 → vertical coplanar line.
**Fix:** Slabs end at the wall's *inner* face (X=16.7). Embedded in the wall, not flush.

### 5. Stacked wall materials with shared transition planes
Stone wainscot Z=0–1.45, concrete above Z=1.45–3.45 → stone top and concrete bottom
are coplanar back-to-back at Z=1.45.
**Fix:** Model the wall as a single Brep with no internal transition face. Apply the
material change via face assignment in Blender, not separate geometry. If you must
keep them as separate solids, offset the concrete UP 5 mm so its bottom is at Z=1.455.

### 6. Slab top = wall bottom (or top = top)
Wall extends from Z=0.25, slab top is also at Z=0.25 → coplanar.
**Fix:** Wall extends slightly below slab top so it's *embedded* in the slab.
Wall Z range: 0.20–3.45, slab Z range: 0.05–0.25. Wall bottom is inside the slab.

### 7. Mullion / window frame coplanar with glass
Mullion at Y=10, glass at Y=10 → fight.
**Fix:** Glass set back 10–20 mm from the mullion outer face.

---

## Pre-modeling setup

In Rhino's Document Properties:
| Setting | Value |
|---|---|
| **Absolute tolerance** | 0.001 m (so sub-mm overlaps register) |
| **Angle tolerance** | 1.0° |
| **Mesh density** | Custom: Max angle 20°, Density 0.8+, Min edge 0.1 |
| **Save render meshes** | On (`_SaveSmall=_No` if using compact format) |

---

## Modeling discipline

For every wall / slab / surface, every time:
1. Build as a **closed Brep with explicit thickness** — never zero-thickness surfaces.
2. **Walls don't share outer faces.** Pick one continuous and trim the perpendicular ones.
3. After every Boolean: `_SelDup` → delete duplicates.
4. After every `_Join` or `_BooleanUnion`: `_What` to verify the result is "Closed polysurface."

---

## Periodic audit during modeling

Every ~30 minutes:

| Command | What it catches |
|---|---|
| `_SelDup` | Duplicate objects (the most common z-fight source) |
| `_SelDupAll` | All duplicate categories (curves, points, surfaces) |
| `_Audit3dm` | File-level topology issues |
| `_SelOpenPolysrf` | Solids that aren't actually closed |
| `_ShowEdges` (Naked + Non-manifold) | Open edges where surfaces don't actually meet |

---

## Pre-export checklist

Before saving the .3dm for export to Blender:
1. `_SelDup` one last sweep — delete everything it finds.
2. `_SelOpenPolysrf` — fix or delete anything that returns.
3. Toggle render mesh display (`_-Properties → RenderMesh → Custom`), inspect every
   wall/slab junction visually for shared faces.
4. Run a slow camera fly-through in Rhino's render preview — z-fighting will flicker
   if present. Mark and fix anywhere it does.
5. `_SaveAs` with render meshes ON.

---

## Quick reference: Rhino commands

| Command | Purpose |
|---|---|
| `_SelDup`, `_SelDupAll`, `_SelDupBlock` | Find duplicates |
| `_OffsetSrf` | Give a finish/surface real thickness |
| `_Trim` / `_Split` | Cut walls cleanly at corner intersections |
| `_BooleanDifference` | Subtract — useful for trimming walls cleanly |
| `_Audit3dm` | Run topology audit |
| `_SelOpenPolysrf` | Find "solids" that aren't closed |
| `_What` | Inspect selected object's classification |
| `_ShowEdges` | Show naked / non-manifold edges |

---

## Edge alignment problems (separate from z-fighting)

Different bug, same family. When what should be a single straight edge has a
visible "lump" or step, it's because two pieces of geometry that should share an
edge are *not exactly aligned* — they're millimeters apart.

**Causes:** Manually-modeled parts where snap wasn't engaged, or two surfaces
trimmed against slightly different cutters.

**Catch with:** `_ShowEdges → Naked edges`. A naked edge along what should be an
interior boundary means two surfaces that should connect, don't.

**Prevent with:** Always use object snaps (Near, End, Int). Match coplanar edges
with `_MatchSrf → Edge`. Never eyeball alignment.
