# Setup Guide

## 1. Clone and run preflight

```bash
git clone https://github.com/mmckeen-nv/2026_aec_cptx_demo_dml.git
cd 2026_aec_cptx_demo_dml
python scripts/aec_setup.py --check --tier viewer
```

Choose the tier that matches the intended use:

- `viewer`: open/render the packaged Blender demos.
- `agent`: Hermes, Blender MCP, CUDA/Ollama, and Daystrom DML.
- `enhancement`: Blender, FFmpeg, and ComfyUI.
- `full`: all integrations, including Rhino and OBS.

Run `python scripts/aec_setup.py --configure` if an executable, endpoint, HDRI,
or source checkout is not auto-detected. The generated configuration is ignored
by Git.

## 2. Configure Hermes

Use `deployment/aec-cptx-profile/config.example.yaml` as a sanitized reference.
Keep the real `config.yaml`, `.env`, API keys, sessions, logs, and DML stores in
the local Hermes profile, never in this repository.

Set `AEC_DEMO_ROOT` to this checkout before starting Hermes or the Rhino helper
scripts. On Windows, the portable launchers derive Hermes from `%LOCALAPPDATA%`.

## 3. Start only the services required by the phase

- Rhino MCP: phases 02–07 and 12–13; default HTTP endpoint `localhost:3001`.
- Blender MCP: live Blender editing; default TCP endpoint `localhost:9876`.
- ComfyUI: optional stylization; default `http://127.0.0.1:8188`.
- Ollama: DML embeddings/summarization; default `http://127.0.0.1:11434`.
- OBS WebSocket: recording only. Set `OBS_WEBSOCKET_PASSWORD` locally.

Copy `tools/obs_recorder_config.example.json` to the ignored
`tools/obs_recorder_config.json` and match its scene/source names to OBS.

## 4. Verify the actual workflow

```bash
python scripts/aec_setup.py --check --tier full
blender --background --python demos/teapot/build_teapot_demo.py -- \
  --render /tmp/teapot.png
```

For an agent-driven session, verify DML separately:

```bash
hermes -p aec-cptx memory status
```

Then start the relevant MCP applications and tell Hermes:

```text
Resume cliff_house_02
```

Model units are metres. Test renders are 960×540; final renders default to
1920×1080. Render scripts use environment/config values rather than usernames
or fixed machine paths.
