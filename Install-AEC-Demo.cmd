@echo off
title AEC CPTX Demo Installer
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-AEC-Demo.ps1" %*
set "EXITCODE=%ERRORLEVEL%"
echo.
echo Installer exited with code %EXITCODE%.
pause
exit /b %EXITCODE%
