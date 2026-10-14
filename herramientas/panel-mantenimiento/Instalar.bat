@echo off
rem Instala el Panel de Mantenimiento (accesos directos en Inicio y Escritorio).
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Instalar.ps1" %*
pause
