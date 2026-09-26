@echo off
setlocal
set PYTHONHOME=
set PYTHONPATH=
pythonw "%~dp0meowdesk_main.py" --locate "%~1"
if errorlevel 9009 python "%~dp0meowdesk_main.py" --locate "%~1"
