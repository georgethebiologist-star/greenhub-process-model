@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch.ps1" %*
echo.
echo GreenHub launcher closed. You can close this window.
pause
endlocal
