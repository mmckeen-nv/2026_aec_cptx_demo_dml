# AEC CPTX Demo — AI Architectural Visualization Pipeline

An agent-driven architectural visualization demo: Hermes interprets a design
brief, controls Rhino and Blender through MCP, renders the scene, and can send
the output through ComfyUI. Daystrom DML/DCN provides optional cross-session
continuity for the full agent-driven deployment.

The active project is `cliff_house_02`, a three-storey modernist cliff house.

## Start here

On Windows, use the root bootstrapper for a guided installation:

```powershell
.\Install-AEC-Demo.cmd -InstallDependencies
```

It also supports connected USB-drive and pre-seeded offline installs. See
[`docs/portable_install.md`](docs/portable_install.md).

Run the preflight before following manual installation instructions:

```bash
# Prove the packaged Blender demos can run
python scripts/aec_setup.py --check --tier viewer

# Agent-driven Blender workflow with Hermes and DML
python scripts/aec_setup.py --check --tier agent

# Every integration, including ComfyUI, OBS, and Rhino
python scripts/aec_setup.py --check --tier full
```

Create a user-local configuration when paths or endpoints are not discoverable:

```bash
python scripts/aec_setup.py --configure
```

The command writes ignored `config/demo.env`. See
[`config/demo.env.example`](config/demo.env.example) for every supported value.
Use `--install` to approve supported package-manager installs one at a time.

## Demo lineup

| Demo | Shipped state | Minimum runtime |
|---|---|---|
| Cliff House | Protected hero `.blend`, session copy, source checkpoint | Blender 4.0+ |
| Cliff House Modification | Blender and ComfyUI output examples | Blender; ComfyUI only to regenerate stylization |
| Virtual Production Studio | Rhino source, Blender scenes, raw and enhanced renders | Blender; Rhino/ComfyUI only to regenerate source/enhancement |
| Teapot | OBJ/3DM source, build script, Blender scene, hero render | Blender 4.0+ |

Daystrom DML is required for persistent memory in the agent-driven workflow. It
is not required merely to open or render the packaged `.blend` files. Maya and
Unreal Engine are not part of the current demo lineup.

## Quick render

```bash
blender --background --python demos/teapot/build_teapot_demo.py -- \
  --render /tmp/teapot.png
```

The Teapot build script creates a ceramic scene from the OBJ. The committed
`teapot_demo.blend` may represent a separate in-progress material session; do
not assume the two are identical.

## Pipeline

| Phase | Application | Result |
|---|---|---|
| 00–01 | Hermes | Startup, service checks, approved design brief |
| 02–06 | Rhino | Site, massing, plans, stacked geometry, detailing |
| 07 | Rhino → Blender | Validation, metadata-preserving `.3dm` handoff |
| 08–09 | Blender | Lighting, camera, and materials |
| 10–11 | Blender / ComfyUI | Test and final renders, depth and segmentation |
| 12–13 | Rhino | Layer reveal and sun-study animations |

Core operating rules:

- Derive geometry from existing curves and edges; do not eyeball vertices.
- Preserve Rhino object/layer metadata through the Blender import.
- Validate before export and again after import.
- Work on timestamped session copies; never silently overwrite a hero scene.
- Keep credentials, runtime memory, logs, caches, and machine snapshots out of Git.

## Repository layout

```text
demos/             Canonical portable demo assets
system_prompts/    Phase execution prompts
skills/            Agent rules and Rhino/Blender validation tools
scripts/           Setup, rendering, pass extraction, and ComfyUI automation
tools/             OBS tray/MCP helpers and Rhino reveal script
deployment/        Sanitized profiles, portable launchers, and WSL2 vLLM scripts
aa_demo_versions/  Earlier Cliff House source layout retained for compatibility
```

Complete component details and official installation references are in
[`demos/DEPENDENCIES.md`](demos/DEPENDENCIES.md). MCP and launch instructions
are in [`SETUP.md`](SETUP.md).

## External source policy

Hermes Agent, Daystrom DML, live Windows installations, DML stores, and caches
are not vendored. Source provenance is recorded in
[`deployment/SOURCE_VERSIONS.md`](deployment/SOURCE_VERSIONS.md). This keeps the
demo repository small and gives each dependency a clear update/security owner.

## License

MIT — see `LICENSE` when present in the distribution.
