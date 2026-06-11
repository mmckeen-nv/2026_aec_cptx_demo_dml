@echo off
setlocal
title Citizen Snips - AEC CPTX Hermes DML
set "HERMES_HOME=%LOCALAPPDATA%\hermes"
set "HERMES_PROFILE=aec-cptx"
set "PATH=%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts;%PATH%"
cd /d "%LOCALAPPDATA%\hermes\profiles\aec-cptx"
echo Starting Citizen Snips AEC CPTX Hermes with Daystrom DML...
echo Working directory: %CD%
echo Profile: aec-cptx
echo.
"%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\hermes.exe" -p aec-cptx
set "EXITCODE=%ERRORLEVEL%"
echo.
echo Hermes exited with code %EXITCODE%.
pause
exit /b %EXITCODE%
