@echo off
call "%~dp0Setup-AEC-Demo.cmd" -OfflineOnly %*
exit /b %ERRORLEVEL%
