@echo off
REM PDF Status Report Generator — launcher (Windows)
REM Usage: run.bat --project ERP-01
cd /d "%~dp0"
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
python make_sample_data.py
python generate_report.py %*
pause
