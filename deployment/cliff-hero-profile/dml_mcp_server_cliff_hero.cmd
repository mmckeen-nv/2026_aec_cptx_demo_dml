@echo off
"%LOCALAPPDATA%\hermes\integrations\daystrom-dml\.venv-dml\Scripts\python.exe" -m dml_mcp.dml_mcp_server ^
  --config "%LOCALAPPDATA%\hermes\integrations\daystrom-dml\config\aec-cptx-portable.yaml" ^
  --storage "%LOCALAPPDATA%\hermes\integrations\daystrom-dml\stores\cliff-house-hero-runtime-store" ^
  --transport stdio %*
