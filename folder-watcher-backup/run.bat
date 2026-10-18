@echo off
REM Folder Watcher & Auto-Backup — launcher (Windows)
REM Usage: run.bat --duration 120   (Ctrl+C stops and writes the report)
cd /d "%~dp0"
python watcher.py %*
pause
