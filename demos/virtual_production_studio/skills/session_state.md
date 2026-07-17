---
project: vp-studio-01
session_state: true
phase: 03_asset_sourcing
phase_label: Asset sourcing ready — fresh set dressing, production look, and hero preview required
status: ready
completed_at: null
asset_cache:
  local: assets/cache
  external: G:/AEC-CPTX/demos/virtual_production_studio/assets/cache
  entries: 12
  note: Use the checked-in cache index and blender_vp_production helper only.
blender_checkpoint:
  blend_file: blender_assets/vp_studio_01.blend
  status: output_only
handoff_source:
  rhino_file: rhino/vp_studio_01.3dm
  requirement: Import fresh and require VP_HANDOFF_PASS before set dressing.
next: Run one fresh Blender handoff, then apply required set dressing, materials, lighting, camera, render, and ComfyUI.
dml_notes:
  - Handoff resolver accepts either repository root or VP demo root.
  - Cached assets use one measured source collection plus lightweight placement instances.
  - Camera tripod placement uses oriented physical-size validation after deterministic yaw.
  - Require zero asset collisions, protected-zone clearance, and hero-role camera visibility.
  - Do not retry, monkey-patch, rewrite, symlink, or hand-scale assets after a failed deployment.
