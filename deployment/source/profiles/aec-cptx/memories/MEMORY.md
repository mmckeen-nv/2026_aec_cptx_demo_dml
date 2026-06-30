WSL UNC: read_file fails. write_file reports success but files silently don't appear — use `wsl bash -c 'cat > ...'` for writes. terminal forward-slash UNC for reads. wsl mkdir for dirs.
§
OBS WebSocket: port 4455, pw bigfish. ClosedResourceError = re-enable WebSocket server in OBS settings.
§
BlenderMCP: TCP 9876, helper at C:\Users\test\Documents\blender_helper.py. Blender 5.1. ComfyUI at C:\Users\test\ComfyUI, SDXL+CN depth. Denoise 0.65-0.70 + CN depth 0.72-0.78 + per-seed variation. Blender ShaderNodeCameraData depth→CN. OBJ import 180-deg X rotation.
§
DML ingest: after every phase, use hermes-dml-memory.cmd ingest --kind phase-outcome --no-filter-noise --no-chunk. PolicyRouter config bug FIXED June 30 2026 — iteration-flexible budget now active.
§
AEC startup: ONLY first actions are 3 parallel MCP health pings (list_slots, netstat 9876, netstat 4455), then ≤5 line status. No file reads, no DML retrieves, no skill re-loading at startup.
§
mcp_rhino_spawn_slot always fails on this machine with Win32Exception error 5 (access denied, Job Object breakaway). Must use schtasks PowerShell launcher with RHINO_MCP_AUTOSTART_PORT=10500 and /runscript="_MCPSpawn" instead. Slot appears as adopted (e.g. "aardvark") after ~30 seconds.
§
Rhino Python: SweepOneRail with angled cross-section planes fails silently at many orientations. Use Surface.CreateExtrusion of arch curves along a direction vector instead — 100% success rate for structural rib geometry.
§
teapot_build LITE(Rhino→Maya→UE5.8): ALL 3 MCP LIVE. Maya CP :50007, UE TCP :55557. MayaMCP=PatrickPalmer/MayaMCP. unreal-mcp=chongdashu/MCPGameProject. UE5.8 src fixes saved as skill. Reqs: .NET10, .NET FW4.8.1 DevPack, VS2022 C++GameDev. Build via UE Build.bat not MSBuild. Phases at aa_demo_versions/teapot_build/.
