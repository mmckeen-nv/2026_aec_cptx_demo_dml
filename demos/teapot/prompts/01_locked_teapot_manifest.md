# Locked Canonical Utah Teapot Manifest

## Source

- File: `demos/teapot/utah_teapot.obj`
- Dataset: University of Utah Graphics Lab, 1987 Frank Crow preset, resolution 24
- SHA-256: `a447b8936e70678c70438a4155b6ef5310c4d0a647cee362f84d53c8b38baf9f`
- Counts: 18,530 vertices; 18,432 faces; four named groups
- Source bounds: X -3.000000..3.434042, Y -2.000000..2.000000,
  Z 0.000000..3.150000

Any mismatch is `CANONICAL_DATA_FAIL`. Never substitute primitives, proxies,
generated fallback geometry, the legacy `.3dm`, or `build_teapot_demo.py`.

## Blender construction contract

- BAC Teapot is Blender-only. Rhino is prohibited.
- Use `build_canonical_teapot()` from the checked-in Blender helper.
- Preserve source XYZ orientation and Z-up.
- Uniformly scale the source X span 6.434042 to exactly 0.300000 m.
- Preserve ground contact at world Z=0; do not recenter vertically.
- Create exactly `TEAPOT_BODY`, `TEAPOT_LID`, `TEAPOT_SPOUT`, and
  `TEAPOT_HANDLE` in collection `BAC_TEAPOT`.
- Preserve per-object canonical source, hash, and version metadata.

Require both receipts:

- `CANONICAL_DATA_PASS source=utah-official-1987-frank-crow vertices=18530 faces=18432 groups=4`
- `TEAPOT_BUILD_PASS objects=4 width_m=0.300000 zmin_m=0.000000`

Visual recognizability never overrides a numeric failure.
