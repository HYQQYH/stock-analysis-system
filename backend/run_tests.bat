@echo off
cd /d "%~dp0"
call aistock_env\Scripts\python.exe -m pytest tests/test_integration.py -v --tb=short
pause
