# Setup Guide — AEC CPTX Demo

## 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/aec-cptx-demo.git
cd aec-cptx-demo
```

## 2. Set your ROOT path

Open `README.md` and note the `{ROOT}` variable. This must point to wherever you cloned the repo.

All other documents use `{ROOT}` as a relative anchor — you only need to set it once.

## 3. Configure Hermes

In your Hermes config, set the project profile to point to this directory. The agent reads the session startup sequence automatically on launch.

System prompt variables:
```
{ROOT}       = /path/to/aec-cptx-demo
{ASSET_ROOT} = /path/to/your/hdri-and-reference-assets
```

## 4. Start the MCP servers

**Rhino MCP** (required for phases 02–06, 12–13):
- Open Rhino
- Start the Rhino MCP server plugin
- Verify: `curl http://localhost:3001/mcp/`

**Blender MCP** (required for phases 07–11):
- Open Blender
- In the Scripting tab, run: `bpy.ops.blendermcp.start_server()`
- Port: 9876 (TCP, localhost only)
- Note: Hermes reaches Blender via a Rhino C# TcpClient proxy

**OBS WebSocket** (required for demo recording):
- Open OBS
- Tools → WebSocket Server Settings → enable, port 4455, password: bigfish
- Agent writes `tools/current_stage.json` to control scene names
- You control start/stop recording manually from the OBS tray

## 5. Prepare the Rhino base file

The file `aa_demo_versions/cliff_house_02/rhino_assets/base_model.3dm` is the Phase 0 starting point. It contains:
- Terrain network curves (uCurves + vCurves)
- Site analysis annotations
- Lot lines
- Footprint plan curves (pad_plan, patio_plan, driveway_plan, garage_plan)

It does NOT contain any built geometry. The agent builds everything during the demo.

## 6. Fill in the design brief

Edit `aa_demo_versions/cliff_house_02/user_prompts/project_prompt.md`.

Or tell Hermes: **"Interview me about my project"** — it will read each section aloud and fill the document in for you.

## 7. Run the demo

Tell Hermes: **"Resume cliff_house_02"**

Hermes will:
1. Read all session files
2. Ping all MCP connections
3. Report what is up/down
4. Ask: "What's next? Prepare the building site?"

Say yes. Watch it build.

## Notes

- **Model units:** meters
- **Render resolution:** 1920×1080 final / 960×540 test
- **Sun study location:** San Diego (32.7°N, -117.2°W, TZ=-8), time 17:30
- **NetworkSurface tolerances (fixed):** edge=0.0001, interior=0.0001, angle=1.0
- **EXR depth channel:** Depth.V FLOAT
