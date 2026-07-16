# VP Studio coordinate-drift failure

project: vp-studio-01
phase: rhino
operation: multi-phase agent-authored geometry
outcome: FAILURE_VALIDATED
timestamp_local: 2026-07-15T09:13:00-07:00

## Intent

Build a recognizable VP studio with local Qwen while retaining the original
Cliff House execution rhythm and advisory Daystrom memory.

## Objective evidence

- Main model: `nvidia/Qwen3.6-35B-A3B-NVFP4` through local vLLM.
- Shell world bounds were approximately X -15.15..15.15 m and
  Y -12.15..12.15 m.
- LED screen world bounds were approximately X -10.05..13.66 m and
  Y -21.66..4.91 m.
- The LED geometry extended about 9.5 m outside the south shell boundary even
  though most component types were recognizable.
- The run reached about 130K input tokens and 60 model calls in roughly nine
  minutes before context compression.

## Root cause

The deployed VP skill conflicted with the checked-in project brief: the skill
used meter-scale loose defaults while the project required Rhino inches. It
specified sizes but no immutable scene-wide coordinate schedule. Individual
phases regenerated local positions, and the LED polar helper omitted an explicit
center offset. Vision evaluated visible composition but no numeric containment
gate rejected the drift.

## Avoidance lesson

Before geometry, read `prompts/01a_locked_scene_manifest.md`. Use inches and
absolute world coordinates from one datum. Every polar helper accepts explicit
`cx` and `cy`; for VP Studio 01 the LED center is exactly (-120,0) inches. Build
one manifest-defined assembly per mutation, print constituent world bounds, and
stop on the first envelope violation. Numeric validation must pass before vision.
Do not let DML replace the manifest or turn this avoidance lesson into a rigid
tool-call controller.

## Next safe action

Start a clean document from the template and rebuild from Phase 1 using the
locked manifest. Do not attempt to translate the scattered scene as a group;
its phases used inconsistent origins.
