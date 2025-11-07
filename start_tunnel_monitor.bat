@echo off
REM Start the VS Code Tunnel Monitor
REM This script launches the Python monitor with pythonw (no console window)

cd /d "%~dp0"
start "" "C:\Users\ricardolo\AppData\Local\Programs\Python\Python312\pythonw.exe" "%~dp0tunnel_monitor.py"
