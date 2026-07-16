# Phase 1 - Canonical Blender Build

Load the checked-in helper through Blender MCP and build once:

```python
import os, importlib.util
root=os.environ["AEC_DEMO_ROOT"]
path=os.path.join(root,"demos","teapot","skills","blender_teapot_interactions.py")
spec=importlib.util.spec_from_file_location("teapot_demo",path)
tp=importlib.util.module_from_spec(spec);spec.loader.exec_module(tp)
print(tp.build_canonical_teapot(root, reset_scene=True))
```

The only permitted tool is `mcp_blender_execute_blender_code(code=...)`. Never
call Rhino, a terminal, a generic `run` tool, or an external Python process.
Require `CANONICAL_DATA_PASS` and `TEAPOT_BUILD_PASS`. On failure, report the
exact mismatch; do not improvise geometry or retry with a different importer.
