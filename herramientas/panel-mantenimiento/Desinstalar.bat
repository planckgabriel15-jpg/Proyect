@echo off
rem Quita los accesos directos y la copia instalada del Panel de Mantenimiento.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Desinstalar.ps1"
pause
