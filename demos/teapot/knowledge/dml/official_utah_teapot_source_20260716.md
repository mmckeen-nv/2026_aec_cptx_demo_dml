# Official Utah teapot source correction — 2026-07-16

## Failure to avoid

A derived Rhino-export OBJ was labeled canonical. Its body, handle, spout, and
lid proportions did not match the familiar Utah teapot, even though its hash
and counts passed the then-current validator. Hash validation only proves that
a file is unchanged; it does not establish correct provenance.

## Validated pattern

- Use only `demos/teapot/utah_teapot.obj` at SHA-256
  `a447b8936e70678c70438a4155b6ef5310c4d0a647cee362f84d53c8b38baf9f`.
- Source is the University of Utah Graphics Lab generator's 1987 Frank Crow
  preset: Blinn scale, round bottom, no later shape modifications.
- Require 18,530 positions, 18,432 faces, and exactly four named groups.
- Require combined bounds X -3.000000..3.434042, Y -2.000000..2.000000,
  Z 0.000000..3.150000 before visual review.
- In Blender, derive camera and lighting placement from imported world bounds;
  never reuse fixed coordinates calibrated to a different mesh.

This memory is advisory evidence for the agent. The checked-in prompt's numeric
and hash gates remain the authority.
