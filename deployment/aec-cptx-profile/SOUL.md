# Hermes Agent Persona

<!--
The demo's behavior is defined by its project files, skill index, and numbered
phase prompts. Keep this persona layer neutral so it does not compete with the
workflow, matching the pristine Cliff House control profile.
-->

For this profile, the exact operator phrase "Run the Cliff House quick demo"
and unambiguous equivalents select QUICK DEMO MODE. Immediately read and
execute
`deployment/aec-cptx-profile/cliff-house-quick-demo.txt`. This is the verified
HERO Blender-to-FLUX.2 lane and never uses Rhino.

An instruction to "load/open the HERO model", "load/open the hero house", or
"load/open the quick model" means the operator-approved current scene
`demos/cliff_house/hero/cliff_house_QUICK_MASTER.blend`, opened through
`demos/cliff_house/hero/skills/blender_cliff_quick.py`. Do not open
`cliff_house_02_HERO.blend` unless the operator explicitly asks for the
"legacy HERO" or "seven-camera HERO".

The exact operator phrase "Run the Cliff House build automatically" and
unambiguous equivalents select AUTOMATIC MODE. Immediately read and execute
`deployment/aec-cptx-profile/cliff-house-automatic-run.txt`. Call it an
automatic run, never a benchmark. Otherwise use MANUAL MODE with the numbered
phase prompts, object-by-object Rhino pacing, and operator review gates.
Automatic and manual construction modes read and apply
`deployment/aec-cptx-profile/canonical-cliff-house-geometry.txt`.
