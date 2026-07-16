# Phase 2 - Blender Product Stage

After `TEAPOT_BUILD_PASS`, use Blender MCP and the already-loaded helper:

```python
print(tp.prepare_product_stage("glazed_ceramic"))
print(tp.render_preview(root, filename="teapot_preview.png"))
```

Require `TEAPOT_LOOK_PASS` and `TEAPOT_PREVIEW_PASS`. The helper derives camera
and light placement from live canonical bounds. Do not rebuild, reimport, or
change scale. If preview validation fails, make one targeted presentation
correction through the helper and render once more. Then enter the open material
interaction phase.
