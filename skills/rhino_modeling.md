# Rhino Modeling Discipline - Derive, Don't Redraw

This is MY working discipline whenever I'm constructing or modifying a Rhino model,
not advice for someone else. It applies at three checkpoints:
1. NEW construction - every new solid follows these rules from creation
2. MODIFICATION - every edit re-runs the audit
3. PRE-EXPORT - final validation before handoff to Blender

The single highest-leverage habit: **every new piece of geometry derives its
boundaries from existing geometry.**

---

## Terrain — NurbsSurface.CreateNetworkSurface tolerances (FIXED VALUES — do not change)

These are Sean's specified values. Do not substitute model absolute tolerance or any other value:

```
edge tolerance:     0.0001
interior tolerance: 0.0001
angle tolerance:    1.0
```

Call signature:
```csharp
int error;
var terrainSurface = Rhino.Geometry.NurbsSurface.CreateNetworkSurface(
    allCurves, uCount, 0.0001, 0.0001, 1.0, out error);
```

`uCount` = number of u-direction curves (the N–S running curves). Remaining curves are treated as v-direction.

**Do not round these up to 0.001.** They are not the same as the model absolute tolerance.

Snap, don't eyeball. Shared edges become *exact* mathematical matches, not "close enough" approximations that tessellate to coplanar faces.

---

## The derivation toolkit

| Command | What it does | When to use |
|---|---|---|
| `_DupEdge` | Duplicate a Brep edge as a free curve | Get exact perimeter for input to another op |
| `_DupBorder` | Duplicate naked edges of a surface/Brep | Wrap perimeter |
| `_DupFaceBorder` | Duplicate border curve of one face | Trim adjacent surfaces |
| `_Pull` | Pull a curve onto a surface | Project footprint onto a sloped slab |
| `_Project` | Project curves through a view direction | Plan-view footprint from any geometry |
| `_Intersect` | Compute intersection curves between surfaces | Exact junction lines for trim |
| `_ExtrudeCrv ... _BothSides` | Extrude curve into a solid | Wall from footprint curve |
| `_Loft` | Build surface between two curves | Sloped/curved surface between known edges |
| `_Sweep1` / `_Sweep2` | Sweep cross-section along rail(s) | Cornices, mouldings, ramps |
| `_MatchSrf -> Edge` | Force one surface's edge to match another | Eliminate edge-misalignment "lumps" |
| `_BooleanDifference` | Cut one solid with another | Trim arms against central pieces |
| `_BooleanUnion` | Merge solids | LAST resort - creates shared faces, run `_SelDup` after |

---

## Anti-patterns observed in this project (and the fixes)

### 1. Coincident outer faces at corners
**Bug:** North wall to X=17, east wall outer also at X=17. Coplanar at NE corner.
**Fix:** Pick which wall is "continuous" (east). North wall's east end trims to
east wall's *inner* face (X=16.7) via `_Trim` with east wall's inner-face curve.

### 2. Painted-on finishes
**Bug:** Stone facing as zero-thickness surface on concrete wall.
**Fix:** Concrete is the substrate. Stone is `_OffsetSrf 25mm` of concrete outer.
Stone sits *outside* the concrete plane.

### 3. Same architectural element modeled twice (`ceiling_L1` + `slab_L2`)
**Bug:** Two solids occupying the same Z range with the same X-Y footprint.
**Fix:** ONE solid. Top face is L2 floor; bottom face is L1 ceiling. Different
materials assigned per-face in Blender, not per-object.

### 4. Slab edge flush with wall outer face
**Bug:** Slab perimeter at X=17, wall outer at X=17 -> shared vertical line.
**Fix:** Slab perimeter ends at wall's INNER face (X=16.7). Slab embeds into wall.

### 5. Boolean union duplicate faces
**Bug:** `_BooleanUnion` two Breps sharing an edge -> shared faces in result.
**Fix:** After every Boolean: `_SelDup` -> delete. Verify with `_What` that
result is "Closed polysurface."

### 6. Triple-stacking at floor planes
**Bug:** Building pad, floor slab, and wall solids all meet at the same Z=0.25:
`pad_inner_slab` top at 0.25, `slab_L1` top at 0.25, `walls_L1` bottom at 0.25.
Three solids share one plane -> 240 m^2 coplanar in three pairs.
**Fix:** Each solid embeds 5-50mm into the one below it:
- pad_inner_slab top: 0.30 (was 0.25)
- slab_L1: Z=0.05 to 0.25 (unchanged - sits IN pad)
- walls_L1: bottom Z=0.20 (was 0.25 - embeds 50mm INTO slab)
Now no plane is shared by three solids. The 50mm embeds make this robust to
floor-finish changes.

### 7. Central + arm decomposition with overlap
**Bug:** A floor modeled as central piece (`slab_L2`) plus extension arms
(`slab_L2_N_arm`, `slab_L2_S_arm`) that overlap the central instead of butting
into it. Each arm overlaps the central by 50-70 m^2.
**Fix during modeling:** After creating the central + arms, immediately:
```
_DupFaceBorder on the central's top face -> outline curve
_BooleanDifference -> use that curve to cut the arms
```
Now arms only cover the cantilever extensions beyond the central's footprint.
**Better:** Don't decompose. Model the L2 floor as ONE Brep covering full footprint.

### 8. "_base" siblings
**Bug:** `slab_L1_base` + `slab_L1`, `wall_L2_east_base` + `wall_L2_east_*`.
A "base" object that overlaps the main object instead of being a foundation/sub
that abuts it.
**Fix:** Either (a) merge into single object with internal face boundaries for
material assignment, or (b) ensure they share only an edge, not a face. Use
`_Intersect` to get the edge they should share, then trim both to that curve.

### 9. Lateral hardscape overlap
**Bug:** `dg_hardscape_W` and `patio_hardscape_dg` are adjacent hardscape regions
modeled as overlapping rectangles instead of trimmed to abutting edges.
**Fix:** `_DupEdge` of the boundary between them, then `_Trim` each with that
curve so they only meet at the line, not overlap.

---

## Periodic audit during modeling

Every ~30 minutes:

| Command | Catches |
|---|---|
| `_SelDup` | Duplicate objects |
| `_SelDupAll` | All duplicate categories |
| `_Audit3dm` | File-level topology issues |
| `_SelOpenPolysrf` | Solids that aren't actually closed |
| `_ShowEdges -> Naked` | Surfaces that should connect, don't |
| Run my coplanar_detector.py via rhino3dm | Catch coplanar faces between Breps |

---

## Metadata to attach during modeling

Set via `_Properties -> Attribute User Text` on every distinct object (or layer
template). Without this, the renderer guesses, and gets it wrong.

```
material                gray_slate_flagstone
material_description    Gray slate, weathered, varied stone sizes ~80cm avg
tile_scale_m            1.0
finish                  weathered
architectural_role      patio_floor
```

| Key | Type | Example |
|---|---|---|
| `material` | string | `gray_slate_flagstone`, `polished_concrete`, `dark_oak` |
| `material_description` | string | Free-form, guides renderer texture choice |
| `tile_scale_m` | float | meters per texture pattern repeat |
| `finish` | string | `polished` / `matte` / `weathered` / `rough` |
| `color_hint` | string | `warm_gray` / `dark_charcoal` |
| `architectural_role` | string | `patio_floor` / `wall_finish` / `structural_slab` |
| `level` | string | `l1` / `l2` / `l3` |
| `orientation` | string | `north` / `south` / `east` / `west` |
| `is_finish` | bool | `true` if decorative layer (should offset 5-25mm from substrate) |
| `is_glazing` | bool | `true` if glass (must not be coplanar with frame) |

---

## Pre-export checklist

1. `_SelDupAll` -> delete all
2. `_SelOpenPolysrf` -> fix or accept each
3. `_ShowEdges -> Naked` -> fix any that should be joined
4. Run coplanar_detector.py via rhino3dm. Refuse to export if critical pairs remain.
5. Verify User Text is set on every layer's representative object
6. `_-Properties -> RenderMesh -> Custom`: max angle 20 deg, density 0.8+
7. Save with render meshes (`_SaveSmall=_No`)
