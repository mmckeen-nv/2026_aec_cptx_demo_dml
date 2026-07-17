# Project Prompt - Virtual Production Studio 01

## Project

Build a standard-lot virtual-production studio from scratch: building shell,
soundstage, smooth LED volume, rooms, loading/circulation, rigging, cameras,
lighting positions, workstations, chairs, and recognizable equipment proxies.

## Priorities

1. Correct architectural scale and physical layout.
2. A thin, smooth, continuous LED wall.
3. Recognizable geometry rather than anonymous stacked boxes.
4. Clear camera, talent, loading, service, and circulation zones.
5. Metadata-preserving Rhino -> Blender handoff.
6. Blender asset replacement, materials, lighting, camera, and render.
7. Final geometry-preserving ComfyUI presentation: SDXL depth conditioning,
   followed by FLUX.2 Klein reference refinement using the user-editable style
   prompt.

## Exclusions

Do not model electrical, HVAC, data, fire protection, utilities, or distribution
runs. Produce only the planning-level estimated electrical-load note defined in
`prompts/01_standard_vp_studio_brief.md`.

## Authority

Use the dimensions and program in `prompts/01_standard_vp_studio_brief.md` and
the exact coordinates and object sizes in
`prompts/01a_locked_scene_manifest.md`. The locked scene manifest is the final
authority whenever the brief uses words such as approximately, nominal,
preferred, typical, or minimum.

Do not choose dimensions or positions. Do not recenter individual phases. Every
Rhino script uses absolute world coordinates from the locked manifest. If a
coordinate is not explicitly scheduled, derive it from scheduled geometry,
print the derivation, and obtain a numeric containment PASS before creation.

Treat engineering, code, rigging, accessibility, and life-safety statements as
planning assumptions pending qualified review.
