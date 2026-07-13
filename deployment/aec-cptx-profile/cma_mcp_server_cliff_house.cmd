@echo off
"%LOCALAPPDATA%\hermes\integrations\daystrom-dml\.venv-dml\Scripts\python.exe" -m cma.mcp_server ^
  --storage-path "%LOCALAPPDATA%\hermes\integrations\daystrom-dml\stores\cma-cliff-house-01\cma_store.json" ^
  %*
