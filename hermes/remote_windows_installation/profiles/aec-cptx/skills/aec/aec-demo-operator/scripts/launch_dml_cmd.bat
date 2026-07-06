@echo off
rem ------------------------------------------------------------
rem launch_dml_cmd.bat – minimal wrapper to start the DML service
rem ------------------------------------------------------------
rem 1️⃣ Set DML environment root
set "DML_DIR=C:\Users\test\AppData\Local\hermes\integrations\daystrom-dml"

rem 2️⃣ Point to the virtual‑env python interpreter
set "VENV=%DML_DIR%\.venv-dml"

rem 3️⃣ Path to the Python entry point that actually runs DML
set "ENTRY=%VENV%\Scripts\python.exe"

rem 4️⃣ Path to the core DML script
set "SCRIPT=%DML_DIR%\scripts\dml_memory.py"

rem 5️⃣ Portable configuration & store locations
set "CONFIG=%DML_DIR%\config\aec-cptx-portable.yaml"
set "STORE=%DML_DIR%\stores\aec-cptx-runtime-store"

rem ------------------------------------------------------------
rem 6️⃣ Execute the DML service
rem ------------------------------------------------------------
"%ENTRY%" "%SCRIPT%" ^
    --storage-dir "%STORE%" ^
    --config-path "%CONFIG%" %*

rem ------------------------------------------------------------
rem 7️⃣ Optional: pause so the user can see any error messages
rem ------------------------------------------------------------
echo.
echo DML launch command completed.
echo Check the console above for any error messages.
pause