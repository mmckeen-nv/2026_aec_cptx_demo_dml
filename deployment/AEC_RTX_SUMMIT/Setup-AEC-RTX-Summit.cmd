@echo off
setlocal
title AEC RTX Summit - Remote GPT + DML Setup
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-AEC-RTX-Summit.ps1" %*
set "EXITCODE=%ERRORLEVEL%"
echo.
if "%EXITCODE%"=="0" (
  echo AEC RTX Summit setup completed successfully.
) else (
  echo AEC RTX Summit setup stopped with code %EXITCODE%.
)
pause
exit /b %EXITCODE%
