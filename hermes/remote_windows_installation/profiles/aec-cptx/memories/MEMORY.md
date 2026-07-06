DML ingest: after every phase, use hermes-dml-memory.cmd ingest --kind phase-outcome --no-filter-noise --no-chunk. PolicyRouter config bug FIXED June 30 2026 — iteration-flexible budget now active.
§
AEC startup sequence: (1) 3 parallel MCP health pings (list_slots, netstat 9876, netstat 4455), (2) verify DML store exists at integrations/daystrom-dml/stores/aec-cptx-runtime-store with dml_state.jsonl present, (3) ≤5 line status summary. If MCPs are down, say so in 1 line and ask user — do NOT loop on shell launch attempts. No markdown walls, no emoji, no panic. CLI output only.
§
mcp_rhino_spawn_slot always fails on this machine with Win32Exception error 5 (access denied, Job Object breakaway). Must use schtasks PowerShell launcher with RHINO_MCP_AUTOSTART_PORT=10500 and /runscript="_MCPSpawn" instead. Slot appears as adopted (e.g. "aardvark") after ~30 seconds.
§
Rhino Python: SweepOneRail with angled cross-section planes fails silently at many orientations. Use Surface.CreateExtrusion of arch curves along a direction vector instead — 100% success rate for structural rib geometry.
§
teapot_build LITE(Rhino→Maya→UE5.8): ALL 3 MCP LIVE. Maya CP :50007, UE TCP :55557. MayaMCP=PatrickPalmer/MayaMCP. unreal-mcp=chongdashu/MCPGameProject. UE5.8 src fixes saved as skill. Reqs: .NET10, .NET FW4.8.1 DevPack, VS2022 C++GameDev. Build via UE Build.bat not MSBuild. Phases at aa_demo_versions/teapot_build/.
§
Hermes installed from git clone of NousResearch/hermes-agent at C:\Users\test\AppData\Local\hermes\hermes-agent\. NEVER commit to this repo — it is upstream source only. Local changes stay local.
§
User wanted to commit changes to AEC GitHub repository. We successfully verified and documented configuration updates to expand iteration limits for DML-based dynamic extension management: max_turns (30→100), max_turns_extension (30→50), max_turns_hard_cap (300→500). Created skill record in devops/iteration-budget-update. Cannot push to GitHub as this is not a git repository, but changes are properly documented.