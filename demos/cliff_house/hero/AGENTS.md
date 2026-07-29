# Cliff House HERO quick-render lane

Project memory namespace: `project:cliff-house-hero-01`.

This lane is intentionally Blender -> ComfyUI only. It never runs Rhino and it
never rebuilds the Cliff House. Read `QUICK_DEMO.md`, then accept short user
requests for a camera choice or ComfyUI style prompt.

For the AEC quick-demo trigger, open only `cliff_house_QUICK_MASTER.blend`
through `skills/blender_cliff_quick.py`. Require `CLIFF_QUICK_OPEN_PASS` and
`CLIFF_QUICK_RENDER_PASS` before ComfyUI. The older
`cliff_house_02_HERO.blend` remains the separate legacy HERO-lane master.
After the render, run only the checked-in Comfy wrapper through the registered
terminal tool. It runs one approved direct FLUX.2 Klein reference generation.
Require `COMFY_FLUX2_PREFLIGHT_PASS` and
`COMFY_OUTPUT_PASS stage=flux2-direct`. Never use Rhino, SDXL, browser-built
graphs, or an improvised workflow.

This is a separate conversational lane, but only one Hermes session may issue
Blender MCP mutations at a time when both profiles point to port 9876. Once the
HERO render receipt exists, this lane releases Blender and can run ComfyUI while
the BAC Teapot lane uses Blender.
