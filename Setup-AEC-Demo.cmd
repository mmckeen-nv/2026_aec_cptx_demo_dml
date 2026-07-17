@echo off
setlocal
title AEC CPTX One-Click Workstation Setup
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Bootstrap-AEC-Windows.ps1" %*
set "EXITCODE=%ERRORLEVEL%"
echo.
if "%EXITCODE%"=="3010" (
  echo Windows must restart to continue. Automatic resume has been registered.
  exit /b 0
)
if not "%EXITCODE%"=="0" (
  echo Setup stopped with code %EXITCODE%. Review the message above.
) else (
  echo Setup completed successfully.
)
pause
exit /b %EXITCODE%
