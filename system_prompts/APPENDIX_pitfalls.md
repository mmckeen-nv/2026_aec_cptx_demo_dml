# Appendix -- Known Pitfalls
# system_prompts/APPENDIX_pitfalls.md
# Single source of truth. Do not duplicate in phase prompts or agent_reference/.
# Last updated: May 2026

Add to this file whenever a new issue is discovered. Reference it from phase prompts
with: "See APPENDIX_pitfalls.md for known issues relevant to this phase."

---

| Issue | Symptom | Fix |
|---|---|---|
| Quaternion rotation mode on imported objects | Setting rotation_euler has no effect; geometry doesn't move | Always set `rotation_mode = 'XYZ'` before setting rotation_euler |
| frame_set() inside keyframe loop | All frames bake to the same position | Set property, then keyframe_insert(frame=N). Never call frame_set inside the loop |
| Depth map range too wide | Flat mid-grey image, no differentiation | Use per-frame auto-normalisation from actual min/max pixel values |
| flipud on Blender EXR | Depth maps are upside-down | Do NOT apply flipud -- OpenEXR Python is already top-down |
| HDRI not fully zeroed for passes | Segmentation/depth maps have ambient shading | Set world background strength to zero AND set film_transparent=True |
| Pad/curtain wall floating above terrain | Visible gap between base and ground | Sample terrain Z at many perimeter points; extend pad bottom below the minimum |
| Chair faces wrong direction | Backs to fire instead of seats | Verify rotation with world-space axis check; use (theta + pi/2 + pi) |
| OPEN_EXR_MULTILAYER unavailable in render settings | Error when setting file format | Use OPEN_EXR for render output; multilayer is only available via compositor File Output node |
| PIL I;16 mode deprecated | 16-bit PNG save fails in Pillow 13+ | Use fromarray(uint16.astype(np.int32), mode='I') |
| Patio normal smoothing bleeding to top face | Top face appears smoothly shaded | Mark top and bottom ring edges as sharp; add Edge Split modifier with use_edge_sharp=True |
| Rhino Trim vs BooleanDifference on terrain | BooleanDifference fails on open surfaces, leaves artefacts | Use Trim with terrain as cutter -- not BooleanDifference |
| Action has no fcurves | Blender 5.x layered actions | Access via action.layers[].strips[].channelbag() |
| scene has no node_tree | Blender 5.x compositor | Use scene.compositing_node_group |
| Transmission input not found | Blender 5.x input name change | Check b.inputs list for current name: [i.name for i in b.inputs] |
| BlenderMCP drops after idle | Known issue with port 9876 | Re-run bpy.ops.blendermcp.start_server() in Scripting tab |
| OBS source is black (0x0) | Window handle lost after restart/virtual desktop switch | Right-click source in OBS -> Properties -> reselect window |
| Camera not animating | frame_set() bug in keyframe loop | scene.frame_set(0) then scene.frame_set(192) -- if same position, re-run without frame_set |
| Segmentation has gradients | Not all bounces zeroed | Set max/diffuse/glossy/transmission/volume ALL to 0 |
| Material not applied | Object name doesn't match keyword | Check name.lower() matches assignment condition |
| wmic command not found | wmic removed in Windows 11 | Use Get-CimInstance via PowerShell: `Get-CimInstance Win32_Process | Where-Object {__HERMES_FENCE_a9f7b3__.Name -eq 'Rhino.exe'}` |
| Thread.Sleep freezes viewport | Thread.Sleep blocks the Rhino UI thread | Use RhinoApp.Wait() in a loop: while (ms < delay) { RhinoApp.Wait(); ms += 50; } |
