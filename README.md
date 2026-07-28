# AEC CPTX Demo — AI Architectural Visualization Pipeline

An agent-driven architectural visualization demo: Hermes interprets a design
brief, controls Rhino and Blender through MCP, renders the scene, and can send
the output directly through the FLUX.2 ComfyUI stage. Daystrom DML/DCN provides optional cross-session
continuity for the full agent-driven deployment.

The active project is `cliff_house_02`, a three-storey modernist cliff house.

## Start here

On Windows, double-click the one-click workstation setup. It self-elevates,
enables WSL2, installs Ubuntu, resumes automatically after a required reboot,
provisions the GPU containers, installs the demo, and runs full preflight:

```powershell
.\Setup-AEC-Demo.cmd
```

The setup also builds the local AEC Mission Control dashboard and installs
`AEC Mission Control.bat` on the Desktop. The installer prompts securely for
the NVIDIA inference key when the `aec-cptx` profile does not already have one.

For an already-prepared workstation, the lower-level guided installer remains
available:

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
| Cliff House Modification | Blender plus SDXL/FLUX output examples | Blender; ComfyUI model set to regenerate stylization |
| Virtual Production Studio | Rhino source, Blender scenes, raw and SDXL/FLUX renders | Blender; Rhino/ComfyUI to regenerate source/enhancement |
| Teapot | Canonical source, Blender interaction scene, optional SDXL/FLUX product render | Blender 4.0+; ComfyUI model set for enhancement |

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
| 10–11 | Blender / ComfyUI | Test/final renders, depth, SDXL conditioning, and FLUX refinement |
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
