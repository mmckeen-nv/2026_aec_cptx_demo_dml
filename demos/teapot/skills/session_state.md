# Session State - BAC Teapot

- Project: `teapot-01`
- Initial state: `WAITING_FOR_BUILD_REQUEST`
- Pipeline after explicit request: Blender build -> product stage -> open material interactions
- Canonical source: `utah_teapot.obj`
- Finished width: 0.30 m; datum Z=0; Z-up
- Blender collection: `BAC_TEAPOT`
- Blender helper: `skills/blender_teapot_interactions.py`
- Blender MCP: launcher-owned bridge on port 9876
- Rhino: prohibited for this demo
- Memory: Daystrom DML active-read, advisory

Never infer completion from old files. Inspect live Blender state and continue
from the first missing receipt.
