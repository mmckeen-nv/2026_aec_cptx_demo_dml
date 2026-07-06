# DML Launch Workflow (AEC CPTX)

This document records the exact, sandbox‑tested sequence for starting the Daystrom DML service before any other MCP tool (Blender, OBS, Rhino). Use it as a run‑book in every AEC CPTX demo session.

---

## 1. Prerequisites (one‑time environment setup)

| Item | Path |
|------|------|
| DML integration root | `C:\Users\test\AppData\Local\hermes\integrations\daystrom-dml` |
| Virtual‑env Python interpreter | `C:\Users\test\AppData\Local\hermes\integrations\daystrom-dml\.venv-dml\Scripts\python.exe` |
| DML entry‑point script | `C:\Users\test\AppData\Local\hermes\integrations\daystrom-dml\scripts\dml_memory.py` |
| Portable config (AEC‑CPTX) | `C:\Users\test\AppData\Local\hermes\integrations\daystrom-dml\config\aec-cptx-portable.yaml` |
| Store directory | `C:\Users\test\AppData\Local\hermes\integrations\daystrom-dml\stores\aec-cptx-runtime-store` |

---

## 2. Exact launch command (run from any CMD prompt)

```bat
@echo off
rem ------------------------------------------------------------
rem 1️⃣ Set environment variables – only needed once per session
rem ------------------------------------------------------------
set "DML_DIR=C:\Users\test\AppData\Local\hermes\integrations\daystrom-dml"
set "VENV=%DML_DIR%\.venv-dml"

rem ------------------------------------------------------------
rem 2️⃣ Launch the DML service via the verified batch wrapper
rem ------------------------------------------------------------
call "%~dp0..\scripts\launch_dml_cmd.bat"
rem (the wrapper prints a short status line when it successfully binds the port)

rem ------------------------------------------------------------
rem 3️⃣ Verify that DML is listening on the expected port
rem    (default port is 8765; read from the portable YAML if you changed it)
rem ------------------------------------------------------------
netstat -ano | findstr :8765
rem You should see a line like:
rem   TCP    127.0.0.1:8765         0.0.0.0:0              LISTENING       <PID>
rem The PID shown must belong to the python.exe process that was just started.

rem ------------------------------------------------------------
rem 4️⃣ If the LISTENING line appears, DML is healthy – proceed
rem    to start Blender MCP, OBS WebSocket, or Rhino slot.
rem ------------------------------------------------------------
echo DML service is up – you may now start other MCP components.
pause
```

### Notes

* **Do not** run any additional tool calls (e.g., `skill_view`, file reads) before the `netstat` check succeeds.  
* The batch file **pauses** at the end so you can read any error output if the port is not bound.  
* If the `netstat` command returns no results, the DML service failed to bind – rerun the batch and inspect the console for traceback messages.  
* All subsequent MCP start‑ups (Blender, OBS, Rhino) must be performed **after** this block reports success.

---

*Keep this file under version control in the `references/` directory of the `aec-demo-operator` skill so every future session can auto‑import it.*  