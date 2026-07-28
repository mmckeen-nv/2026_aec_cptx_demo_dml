@echo off
"%LOCALAPPDATA%\hermes\integrations\daystrom-dml\.venv-dml\Scripts\python.exe" -m dml_mcp.cma_mcp_server ^
  --storage-path "%LOCALAPPDATA%\hermes\integrations\daystrom-dml\stores\cma-cliff-house-01\cma_store.json" ^
  %*
