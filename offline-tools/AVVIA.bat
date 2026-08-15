@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0server-offline.ps1"
if errorlevel 1 (
  echo.
  echo Impossibile avviare il gioco.
  pause
)

