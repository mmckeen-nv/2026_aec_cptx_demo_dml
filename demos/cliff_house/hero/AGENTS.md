# Cliff House HERO quick-render lane

Project memory namespace: `project:cliff-house-hero-01`.

This lane is intentionally Blender -> ComfyUI only. It never runs Rhino and it
never rebuilds the Cliff House. Read `QUICK_DEMO.md`, then accept short user
requests for a camera choice or ComfyUI style prompt.

Open only `cliff_house_02_HERO.blend` through the checked-in Blender helper.
Require `CLIFF_HERO_OPEN_PASS` and `CLIFF_HERO_RENDER_PASS` before ComfyUI.
After the render, run only the checked-in Comfy wrapper through the registered
terminal tool. Never use Rhino, browser-built graphs, or an improvised workflow.

This is a separate conversational lane, but only one Hermes session may issue
Blender MCP mutations at a time when both profiles point to port 9876. Once the
HERO render receipt exists, this lane releases Blender and can run ComfyUI while
the BAC Teapot lane uses Blender.
