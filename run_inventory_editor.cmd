@echo off
setlocal
cd /d %~dp0
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)
set FLASK_APP=inventory_editor.py
set FLASK_ENV=development
python -m flask run
