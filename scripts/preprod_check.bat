@echo off
setlocal
cd /d %~dp0\..
call .venv\Scripts\activate
python scripts\preprod_check.py
endlocal
