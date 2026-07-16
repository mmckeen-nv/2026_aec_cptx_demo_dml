---
status: CURRENT_POLICY
project: vp-studio-01
date: 2026-07-15
---

# LED negative-Z and stale Blender handoff failure

Observed failure: a clockwise planar LED ring caused a positive-height Rhino
extrusion to follow the profile normal into negative Z. An older populated
Blender collection was then mistaken for the current handoff, and opening an
existing `.blend` allowed stale geometry to survive under a correct filename.

Validated recovery:

- Require `LED_ACTIVE_WALL` bounds Z `0..288 in` and `LED_REAR_SUPPORT` bounds
  Z `0..312 in` before Phase 3 and again before handoff.
- If a trial extrusion has negative minimum Z, recreate it with the opposite
  height sign and verify exact bounds before adding it to Rhino.
- Determine phase completion from live Rhino objects, never checkpoint files.
- Begin Blender from the launcher-owned generic scene and call
  `blender_vp_production.import_current_handoff(reset_scene=True)`.
- Never open an existing `.blend` as workflow input. The final `.blend` is
  output-only.
- Require the imported collection SHA-256 to match the canonical current
  `rhino/vp_studio_01.3dm` before assets, cameras, renders, or saves.
