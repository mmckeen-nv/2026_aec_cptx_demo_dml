# Utah Teapot geometry provenance

`utah_teapot.obj` is generated from the official University of Utah Graphics
Lab Utah Teapot generator at <https://graphics.cs.utah.edu/teapot/>.

- Historical version: **1987 — Frank Crow**
- Shape: the familiar Blinn-scaled Utah teapot with Frank Crow's round bottom
- Patch basis: 32 cubic Bézier patches / 512 control points
- Mesh: quad-dominant, resolution 24, Z-up, triangulated tips
- Generator settings: round bottom; no interior, circularization, trimming,
  chamfer, curvature modification, spout cap, or lid cap
- Download settings: welded vertices, injective UV layout, symmetric
  triangulation, both sides
- Generated groups: `teapot_handle`, `teapot_spout`, `teapot_lid`, `teapot_body`
- SHA-256: `a447b8936e70678c70438a4155b6ef5310c4d0a647cee362f84d53c8b38baf9f`
- Counts: 18,530 positions; 18,432 faces; 4 groups
- Generated: 2026-07-16

The University page makes the models freely available for any use and asks
users to cite the page. `tools/generate_official_teapot.js` records the exact
generator options used to reproduce this checked-in OBJ. The previous derived
Rhino export is intentionally excluded from the demo so it cannot be mistaken
for canonical source data.
