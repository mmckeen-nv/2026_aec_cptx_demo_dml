# Rhino 8 / Rhino MCP Platform 0.1.5 call recipe

status: READ_ONLY_CAPTURE_REFERENCE
mutation_policy: SUPERSEDED_BY_CURRENT_PHASE_CSHARP

project: vp-studio-01
phase: rhino
operation: reliable-agent-authored-rhino-calls
outcome: SUCCESS_VALIDATED
validation_status: PASSED
source_provenance: live schema inspection and read-only Rhino MCP probes on 2026-07-14

Geometry mutation now uses only the exact inline C# `Func<>`/`Action<>`
scaffold embedded in the current phase prompt through
`mcp_rhino_run_csharp(script=...)`. Treat every `Objects.Add*` return as a
`Guid` and construct geometry directly from absolute WorldXY intervals.

The Python details below are retained only for read-only inspection and viewport
capture. Python uses `doc = __rhino_doc__` and must not create, move, delete, or
replace geometry.

- `doc.Layers.FindByFullPath(path, True)` returns an integer index; `-1` means
  absent. Do not access `.Index` on its result.
- `rhinoscriptsyntax.LayerIndex` and `rhinoscriptsyntax.ObjectAttributes` are
  absent. Use `Rhino.DocObjects.ObjectAttributes` and integer layer indices.
- Create nested layers parent-first with `Rhino.DocObjects.Layer`, assigning
  `ParentLayerId = doc.Layers[parent_index].Id` before `doc.Layers.Add(layer)`.
- Prepare ObjectAttributes before calling the applicable `doc.Objects.Add*`
  method. For rhinoscriptsyntax-created geometry, retrieve the object with
  `doc.Objects.FindId(guid)`, update `rhobj.Attributes`, and call
  `rhobj.CommitChanges()`.
- Inspect `payload.error` and stdout. Transport success does not prove geometry
  was created.

`mcp_rhino_get_viewport_image` returns nested base64 rather than a usable URL.
Never invent a URL, copy base64 into `execute_code`, or loop on that tool. Save
the active view directly through this read-only Rhino call; the controller
recognizes the successful `CaptureToBitmap` call as the viewport checkpoint:

```python
import System
view = __rhino_doc__.Views.ActiveView
bitmap = view.CaptureToBitmap(System.Drawing.Size(960, 540))
image_path = r"C:\absolute\demo\work\rhino_phase_view.png"
bitmap.Save(image_path)
print(image_path)
```

Then call `vision_analyze(image_url=image_path, question=<focused defect
review>)` and require a literal PASS verdict. REVISE does not unlock saving or
handoff. This capture method was executed successfully against the live slot.

avoidance_rule: reject memories recommending `rs.LayerIndex`,
`rs.ObjectAttributes`, `.Index` after `FindByFullPath`, invented viewer URLs,
base64 decoding through `execute_code`, or a redundant
`mcp_rhino_get_viewport_image` call before `CaptureToBitmap`.
