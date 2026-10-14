@echo off
rem Abre el panel directamente desde esta carpeta, sin instalar nada.
start "" powershell.exe -NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "%~dp0PanelMantenimiento.ps1"
