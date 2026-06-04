# Visual Engagement Rule — AEC Demo Projects

**Default behavior — applies to every session, every phase.**

## Design discussions
When discussing user preferences, style choices, materials, or any design
decision — proactively display relevant reference images from the active
project's references folder:
  aa_demo_versions/[project]/references/
  aa_demo_versions/[project]/references/images/

Don't wait to be asked. Pull the most relevant image(s) and display them
as part of the conversation so the discussion is grounded in visuals.

## Rhino scene work
When discussing changes to the Rhino scene — terrain, building footprint,
walls, patios, stairs, or any geometry — get a Rhino viewport screenshot
showing the area being discussed. Display it before and after changes so
Sean can see exactly what is being modified.

## Image viewer always active
The image viewer (Rhino viewport screenshot or reference image) should
always be open and displaying the most current, relevant part of the
project. Update it as the topic shifts.

## Implementation
- Reference images: use Desktop Commander read_file (image mode) to display
- Rhino viewport: use rhinoceros3d viewport screenshot or get_scene +
  orient camera to relevant area before screenshotting
- Timing: display BEFORE discussing, not after — images lead, words follow

*Added: 2026-05-20 per Sean's directive.*
