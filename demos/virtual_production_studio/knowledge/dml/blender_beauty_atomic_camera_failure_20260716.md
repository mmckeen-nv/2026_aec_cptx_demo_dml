# Blender beauty camera must be atomic

- outcome: failure repaired
- approach_signature: blender|setup_beauty_camera-three-value-unpack|render-after-exception
- observed_evidence: The Rhino handoff and all 27 cached set-dressing placements passed. The agent then unpacked three values from `setup_beauty_camera()`, which returns `(camera, alignment)`. Camera setup raised before changing the active scene camera, but the next call rendered anyway. The resulting frame showed only an old physical camera against a nearly uniform background (`foreground=0.0161`, `range=0.0039`).
- root_cause: Camera activation and rendering were exposed as separate agent steps, and the execution rail consumed retry budget before knowing whether camera setup succeeded.
- avoidance_rule: Call only `render_beauty_preview(root)`. It atomically applies materials and lighting, activates the locked stage-wide camera, verifies that it is the active scene camera, writes the canonical absolute path, and requires `VP_RENDER_PASS` plus `VP_BEAUTY_PASS`. Never unpack `setup_beauty_camera()` or render after a camera-helper exception.
- next_safe_action: Reload the checked-in Blender production helper, retain the validated handoff and set dressing, and call `render_beauty_preview(root)` once.
