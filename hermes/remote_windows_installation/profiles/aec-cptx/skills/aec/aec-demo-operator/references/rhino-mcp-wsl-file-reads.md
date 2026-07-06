# WSL file reads from Windows Hermes (MSYS / git-bash)

## The problem

The Hermes `read_file` tool cannot resolve `\\wsl.localhost\Ubuntu\...` UNC paths.
Every call returns "File not found" regardless of the file's actual existence.
This affects ALL files under the WSL repo root.

## Solution 1 — MSYS forward-slash UNC (preferred)

Use `terminal` with forward-slash UNC paths. These are native to the MSYS/git-bash
shell that Hermes uses on this Windows machine.

```bash
# Read a file
cat //wsl.localhost/Ubuntu/home/test/2026_aec_cptx_demo/README.md

# List a directory
ls //wsl.localhost/Ubuntu/home/test/2026_aec_cptx_demo/

# Read multiple files at startup — issue parallel terminal calls
# (Hermes can run multiple terminal() calls concurrently)
```

This works with cat, ls, grep, head, tail, and any POSIX tool.
No `wsl.exe` invocation needed. No `MSYS_NO_PATHCONV` needed.

## Solution 2 — wsl.exe with MSYS_NO_PATHCONV

Use `MSYS_NO_PATHCONV=1` to prevent Git-Bash from rewriting `/home` paths
when calling `wsl.exe`:

```bash
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu -- sed -n '1,200p' /home/test/2026_aec_cptx_demo/README.md
MSYS_NO_PATHCONV=1 wsl.exe -d Ubuntu -- ls -la /home/test/2026_aec_cptx_demo
```

Heavier than Solution 1 — spawns a WSL process each time. Use as fallback.

## Pitfalls

- Avoid calling `bash -lc` with unescaped `$f` loops inside MSYS; it can strip variables.
  Use direct tool calls (sed/ls/cat) instead.
- The backslash UNC form (`\\wsl.localhost\...`) only works in Windows-native tools
  (Explorer, PowerShell). MSYS and Hermes read_file both fail with it.
- The double-forward-slash form (`//wsl.localhost/...`) is MSYS-specific. It will NOT
  work in PowerShell or cmd.exe.

## Session startup pattern

When the system prompt mandates reading 6+ WSL files at startup, batch them
as parallel `terminal` calls using the MSYS UNC form:

```
terminal("cat //wsl.localhost/Ubuntu/home/test/2026_aec_cptx_demo/README.md")
terminal("cat //wsl.localhost/Ubuntu/home/test/2026_aec_cptx_demo/SETUP.md")
terminal("cat //wsl.localhost/Ubuntu/home/test/2026_aec_cptx_demo/skills/INDEX.md")
...
```

All 6 calls can be issued in a single parallel batch — no dependencies between them.
